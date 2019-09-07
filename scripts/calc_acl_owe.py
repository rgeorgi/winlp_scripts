from argparse import ArgumentParser
from winlp_scripts.budget_sheet import grab_sheet, get_col
from winlp_scripts.utils import load_yml, usd


def calc_fees(rows, mapping):
    for row in rows:
        col = lambda x: get_col(row, x, mapping)
        colbool = lambda x: col(x) == 'Y'
        colamt = lambda x: usd(col(x))

        name = col('name')
        main_conf = 295 if colbool('r_main_conf') else 0
        developing = colbool('developing')
        acl_owed = colamt('r_acl_owed')
        acl_paid = colamt('r_acl')
        regpaid = colamt('r_reg')

        if main_conf or acl_owed or regpaid:
            print(','.join([str(s) for s in [name, acl_paid, regpaid,
                                             main_conf, acl_owed, 110]]))



if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('-c', '--config', default='config.yml', type=load_yml)
    p.add_argument('-i', '--index', type=int, default=1, help='The index of the page on the provided sheet that the travel grants live.')
    p.add_argument('-n', '--numrows', type=int, default=48, help='The number of the last populated row in the spreadsheet')
    p.add_argument('-m', '--mapping', type=load_yml, default='data/budget_mapping.yml')

    args = p.parse_args()

    # Grab values from the config
    google_dict = args.config.get('google', {})
    api_key = google_dict.get('api_key')
    sheet_id = google_dict.get('budget_sheet_id')

    # Also get the column mappings

    headers, rows = grab_sheet(sheet_id, api_key)

    calc_fees(rows, args.mapping)