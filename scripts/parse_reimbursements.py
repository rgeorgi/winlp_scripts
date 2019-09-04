"""
This script is intended to ingest the reimbursement request form
generated by limesurvey, and the files downloaded in conjunction
with them, and create folders to arrange the data for manual inspection.
"""
import pickle
from argparse import ArgumentParser
import os
from collections import OrderedDict, defaultdict
from io import BytesIO
from typing import Union

from pandas import DataFrame
import math
import zipfile
import json
import urllib.parse
import re

from winlp_scripts.limesurvey import LimeSurveyConnection
from winlp_scripts.utils import load_yml


def usd(s: Union[str, float]) -> float:
    """
    Unify the values entered for USD as float (0 when NaN)
    """
    if isinstance(s, str):
        return float(s) if not s.startswith('$') else float(s[1:])
    else:
        if math.isnan(s):
            s = 0
        return float(s)


def parse_sheet(responses: DataFrame,
                output_dir,
                zip: zipfile.ZipFile):
    """
    Process the returned responses
    """

    for row in responses.iterrows():
        data = row[1]
        email = data['email']
        address = data['mailingaddress']
        response_id = data['id']
        name = data['name']

        # Recordkeeping vars
        cost_dict = OrderedDict()
        comments = defaultdict(list)
        total_amt = 0.0

        # Respondent Directory
        respondent_dir = os.path.join(output_dir, '{} - {}'.format(response_id, name))

        files_for_post = {info for info in zip.filelist if
                          info.filename.startswith('{:05d}'.format(response_id))}  # type: Set[zipfile.ZipInfo]

        print(data.keys())

        def files_and_amts(file_data_name, dir_name, amt_key):
            nonlocal files_for_post, total_amt
            data_str = data[file_data_name]
            try:
                file_list = json.loads(data_str)
            except TypeError as te:
                file_list = []
            except json.JSONDecodeError as jde:
                file_list = []

            target_dir = os.path.join(respondent_dir, dir_name)

            # First, check through
            for file_dict in file_list:
                file_name = urllib.parse.unquote(file_dict['name'])
                file_size = float(file_dict['size'])*1024

                # If there are comments, add them
                # to the dictionary
                comment = file_dict['comment']
                if comment:
                    comments[dir_name].append((file_name, comment))

                target_file = {info for info in files_for_post if
                               info.file_size == file_size}

                if len(target_file) == 1:
                    files_for_post -= target_file
                    zip.extract(target_file.pop().filename, target_dir)

            # Now do amounts
            if usd(data[amt_key]):
                cost_dict[dir_name] = usd(data[amt_key])
            total_amt += usd(data[amt_key])



        # Now, create a folder for each respondent.
        respondent_dir = os.path.join(output_dir, '{} - {}'.format(response_id, name))
        os.makedirs(respondent_dir, exist_ok=True)

        files_and_amts('regfile', 'registration', 'registration')
        files_and_amts('flightdoc', 'air', 'flightamt')
        files_and_amts('bustraindocs', 'other_transport', 'bustrain')
        files_and_amts('hoteldoc', 'hotel', 'hotelprice')
        files_and_amts('visadoc', 'visa', 'visaamt')
        files_and_amts('addldocs', 'other', 'addlcosts')

        # Now, extract any other files
        for file in files_for_post:
            zip.extract(file, respondent_dir)

        # Also, create a summary file for the claimed amounts.
        summary_path = os.path.join(respondent_dir, 'summary.txt')
        with open(summary_path, 'w') as summary_f:
            summary_f.write('{}\n{}\n\n{}\n\n'.format(
                name, email, address
            ))
            for key in cost_dict:
                summary_f.write('{:>20s}: ${:0.2f}\n'.format(key, cost_dict[key]))

            summary_f.write('\ntotal itemized: ${:.2f}\n'.format(total_amt))

            if comments:
                summary_f.write('\n\nAdditional comments:\n')
                for key in sorted(comments.keys()):
                    if comments[key]:
                        summary_f.write(' '*5+'{}\n'.format(key))
                        for filename, comment in comments[key]:
                            if comment:
                                summary_f.write(' '*10+''+'{}: {}\n'.format(filename, comment))

if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('-z', '--zip', help='Path to save the zip of attached files.')
    p.add_argument('-o', '--output', help='Path to directory to use for output', default=os.getcwd())
    p.add_argument('-c', '--config', help='Path to the configuration file', type=load_yml, default='config.yml')
    p.add_argument('-s', '--surveyid', help='ID of the reimbursement survey', required=True, type=int)
    p.add_argument('--sheet', help='Path to the sheet destination', type=str)
    p.add_argument('-f', '--force', help='Overwrite previously downloaded data', action='store_true')

    args = p.parse_args()

    # Get the limesurvey params
    lime_user = args.config.get('limesurvey_user')
    lime_pass = args.config.get('limesurvey_pass')
    lime_base = args.config.get('limesurvey_url_base')

    with LimeSurveyConnection(lime_base, lime_user, lime_pass) as c:
        responses = c.export_responses(args.surveyid)

        # Download the zipfile only if it doesn't already exist.
        if args.zip and os.path.exists(args.zip) and not args.force:
            zip = zipfile.ZipFile(args.zip)
        else:
            zip = c.get_download_for_response_list(args.surveyid, list(responses['id']), bytes=True)
            with open(args.zip, 'wb') as zip_f:
                zip_f.write(zip)
            zip = zipfile.ZipFile(BytesIO(zip))


        # Now, get the survey responses
        if args.sheet or args.force:
            if os.path.exists(args.sheet):
                with open(args.sheet, 'r') as pickle_f:
                    responses = pickle.load(pickle_f)
            else:
                responses.to_pickle(args.sheet)

        parse_sheet(responses, args.output, zip)
        # parse_sheet(args.sheet, args.output, args.files)
    # print(file_ids)