import sys
from argparse import ArgumentParser

from winlp_scripts.budget_sheet import grab_sheet, get_col
from winlp_scripts.email_tools import create_html_email, gmail_send
from winlp_scripts.utils import load_yml, usd

if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('-c', '--config', default='config.yml', type=load_yml)

    args = p.parse_args()

    cred_path = args.config['google']['token_file']
    sheet_id = args.config['budget']['sheet_id']
    mappings = load_yml(args.config['budget']['mapping'])
    template_path = args.config['templates']['reimburse_email']
    with open(template_path) as template_f:
        template_html = template_f.read()

    gmail_user = args.config['google']['user']
    gmail_pass = args.config['google']['pass']

    header, rows = grab_sheet(sheet_id, 1, cred_path)
    for row in rows:
        local = lambda x: get_col(row, x, mappings)
        method = local('method')
        status = local('status')
        acl_refund = usd(local('acl_refund'))
        approved_amt = usd(local('approved'))
        name = local('name')
        email = local('email')

        if status in ['Paid', 'Did Not Attend', 'No Request Received']:
            continue

        template_str = template_html.format(name=name,
                                            reg_amt=acl_refund,
                                            other_amt=approved_amt,
                                            total_amt=approved_amt+acl_refund)

        msg = create_html_email(template_str, 'WiNLP Reimbursement: Payment Method Information Requested')
        if 'Georgi' in name:
            gmail_send(gmail_user, gmail_pass, [email], msg)
    sys.exit()

