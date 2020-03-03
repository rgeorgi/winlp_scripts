#!/usr/bin/env python3
"""
This script is intended to send personalized notes to authors regarding revisions to their submissions.

It uses:
    * Softconf submissions
    * A google sheet with softconf IDs, and a column that contains text to be sent to the author.


"""
import os
import sys
from argparse import ArgumentParser
from pandas import DataFrame, isna

from winlp_scripts.email_tools import gmail_send, craft_text_email
from winlp_scripts.softconf import SoftconfConnection, PAPER_ID, PAPER_TITLE, MC_EMAIL, MC_FIRST, MC_LAST, PASSCODE
from winlp_scripts.utils import load_yml
from winlp_scripts.google_sheets import GoogleSheetInterface

def generate_notes(submission_data: DataFrame, notes: DataFrame, template_path: str):
    """
    Given the submission information

    :param submission_data:
    :param notes:
    :param template_path:
    :return:
    """
    with open(template_path, 'r') as template_f:
        template_text = template_f.read()

    # Fill a dictionary keyed by the submission ID
    # with the author contact information
    sub_dict = {}
    for row_id, sub_row in submission_data.iterrows():
        mc_last, mc_first, mc_email, paper_title, paper_id = [sub_row.get(key) for key in [MC_LAST, MC_FIRST, MC_EMAIL, PAPER_TITLE, PAPER_ID]]
        sub_dict[int(paper_id)] = (paper_title, mc_email, mc_first, mc_last)

    # Now, examine the rows in the notes spreadsheet.
    for row_id, note_row in notes.iterrows():
        paper_id = int(note_row[0])
        note = note_row[-1]
        decision = note_row[-3]

        if decision == 'reject':
            decision_txt = '''I am sorry to inform you that the following submission was not selected by the program committee.'''
        else:
            decision_txt = '''On behalf of the WiNLP 2020 Program Committee, I am delighted to inform you that the following submission has been accepted to appear at the workshop.'''

        paper_title, mc_email, mc_first, mc_last = sub_dict.get(paper_id)

        if note:
            # print(note_row, submission_data.keys())
            # print(sub_dict.get(paper_id), note)

            yield template_text.format(**{
                'paper_id': paper_id,
                'mc_first': mc_first,
                'mc_last': mc_last,
                'paper_title': paper_title,
                'decision': decision_txt,
                'note': note
            }), mc_email


if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('-c', '--config', type=load_yml, default='config.yml', help="Path to the configuration file which specifies login details and other settings.")
    p.add_argument('-s', '--sheet', type=str, required=True, help='id of the google sheet to draw the author notes from.')
    p.add_argument('-t', '--template', type=str, help='Path to the template to generate emails from.', required=True)
    p.add_argument('-e', '--email', type=bool, help='Actually send the emails. Defaults to just printing the messages.')

    args = p.parse_args()

    # --1) Set up the connection to SoftConf
    softconf_settings = args.config.get('softconf') # type: dict
    scc = SoftconfConnection(softconf_settings.get('user'),
                             softconf_settings.get('pass'),
                             softconf_settings.get('url_base'))
    # reviews = scc.reviews()
    submissions = scc.submission_information(keys=[PAPER_ID, PASSCODE, PAPER_TITLE, MC_EMAIL, MC_FIRST, MC_LAST])

    # --2) Set up the connection to Google Sheets
    google_settings = args.config.get('google')
    gsi = GoogleSheetInterface(google_settings.get('token_file'),
                               google_settings.get('client_file'))

    # --3) Obtain google email credentials
    gmail_user = google_settings.get('user')
    gmail_pass = google_settings.get('pass')

    review_sheet =  gsi.get_sheet(args.sheet)

    for text, to_email in generate_notes(submissions, review_sheet, args.template): # type: str
        msg = craft_text_email(text, 'WiNLP 2020 Submission Notification')
        if args.email:
            gmail_send(gmail_user, gmail_pass, ['winlp-chairs@googlegroups.com', to_email], msg)
        else:
            print(msg)