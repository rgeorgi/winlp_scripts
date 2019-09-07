from argparse import ArgumentParser

from winlp_scripts.budget_sheet import grab_sheet
from winlp_scripts.utils import load_yml, col_letter, usd
import googleapiclient.discovery

def analyze_sheet(rows, letter_mapping):



    num_travel_overages = 0
    total_travel_overages = 0
    total_travel_requests = 0
    overall_transport_shortfall = 0
    total_to_award = 0

    for row in rows:
        def get_col(key):
            return usd(row[col_letter(letter_mapping.get(key))])

        e_air = get_col('e_air')
        e_train = get_col('e_train')
        r_air = get_col('r_air')
        r_train = get_col('r_train')

        e_hotel = get_col('e_hotel')

        e_travel_amt = e_air + e_train
        r_travel_amt = r_air + r_train



        if r_travel_amt != 0:
            if r_travel_amt > e_travel_amt:
                num_travel_overages += 1
                total_travel_overages += r_travel_amt - e_travel_amt
            total_travel_requests += 1
            overall_transport_shortfall += r_travel_amt - e_travel_amt

            total_to_award += e_hotel + e_air + e_train

    stats = [('# Of Travel Overages:', num_travel_overages, 'd'),
             ('% Of Travel Requests that were over estimate:', num_travel_overages/total_travel_requests*100, '.2f'),
             ('Avg. Amount of Overage:',total_travel_overages/num_travel_overages, '.2f'),
             ('Overall Transport Shortfall:', overall_transport_shortfall, '.2f'),
             ('Total Estimated to Award', total_to_award, '.2f')]

    for stat_header, num, fmt in stats:
        print('{{:<24s}} {{:{}}}'.format(fmt).format(stat_header, num))


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

    analyze_sheet(grab_sheet(sheet_id, api_key)[1], args.mapping)


