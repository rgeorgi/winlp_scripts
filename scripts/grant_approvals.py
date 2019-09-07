from argparse import ArgumentParser
import os
import datetime

from winlp_scripts.budget_sheet import grab_sheet, get_col
from winlp_scripts.template import process_docx_template
from winlp_scripts.utils import load_yml

from num2words import num2words


def generate_approvals(rows, mapping, invitation_template, output_dir: str):
    """
    Scan through the budget spreadsheet
    to generate approvals
    """

    # Create the output
    for row in rows:
        def get_col_local(key):
            return get_col(row, key, mapping)

        name = get_col_local('name')
        paper_title = get_col_local('paper')
        email = get_col_local('email')
        awarded = get_col_local('awarded')

        file_name = 'Travel Grant Letter - {}.docx'.format(name)
        full_path = os.path.join(output_dir, file_name)

        if awarded is not '':

            d = process_docx_template(invitation_template,
                                      keys={'date': datetime.datetime.now().strftime('%B %m, %Y'),
                                            'name':name,
                                            'email':email,
                                            'paper_title':paper_title,
                                            'amount':awarded,
                                            'text_amount':num2words(awarded)})
            os.makedirs(output_dir, exist_ok=True)
            d.save(full_path)



if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('-c', '--config', default='config.yml', type=load_yml)
    p.add_argument('-m', '--mapping', default='data/budget_mapping.yml', type=load_yml,
                   help='Mapping for columns to fields in the budget spreadsheet')
    p.add_argument('-o', '--output', default='letters', help='Directory to output invitation letters in.')

    args = p.parse_args()

    # Get Google API info
    google_sheet = args.config.get('google', {})
    api_key = google_sheet.get('api_key')
    cred_path = google_sheet.get('token_file')
    sheet_id = google_sheet.get('budget_sheet_id')

    # Retrieve the current state of the grant sheet
    headers, rows = grab_sheet(sheet_id,
                               cred_path=cred_path,
                               num_rows=args.mapping.get('num_rows'),
                               last_col=args.mapping.get('last_col'))

    invitation_template = args.config['templates']['invitation']
    email_template = args.config['templates']['grant_email']

    # generate_approvals(rows, args.mapping, invitation_template, args.output)

    print(email_template)
