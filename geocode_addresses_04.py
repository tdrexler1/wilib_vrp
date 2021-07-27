#! python3

import argparse
import pandas as pd
import json
import urllib.request
import os
import yaml

# TODO: following two lines for testing only
pd.options.display.width = 0
pd.options.display.max_rows = 1000


def add_region_data(stop_df):

    ideal_region_01 = ['Ashland', 'Barron', 'Bayfield', 'Burnett', 'Chippewa', 'Douglas', 'Dunn', 'Eau Claire', 'Pepin',
                       'Pierce', 'Polk', 'Rusk', 'Sawyer', 'St. Croix', 'Washburn']
    ideal_region_02 = ['Clark', 'Forest', 'Iron', 'Langlade', 'Lincoln', 'Marathon', 'Oneida', 'Portage', 'Price',
                       'Taylor', 'Vilas', 'Wood']
    ideal_region_03 = ['Brown', 'Door', 'Florence', 'Kewaunee', 'Marinette', 'Menominee', 'Oconto', 'Outagamie',
                       'Shawano', 'Waupaca']
    ideal_region_04 = ['Adams', 'Buffalo', 'Crawford', 'Jackson', 'Juneau', 'La Crosse', 'Monroe', 'Richland',
                       'Trempealeau', 'Vernon']
    ideal_region_05 = ['Calumet', 'Dodge', 'Fond du Lac', 'Green Lake', 'Manitowoc', 'Marquette', 'Ozaukee', 'Sheboygan',
                       'Washington', 'Waushara', 'Winnebago']
    ideal_region_06 = ['Columbia', 'Dane', 'Grant', 'Green', 'Iowa', 'Lafayette', 'Rock', 'Sauk']
    ideal_region_07 = ['Jefferson', 'Kenosha', 'Milwaukee', 'Racine', 'Walworth', 'Waukesha']

    starter_region_01 = ['Ashland', 'Bayfield', 'Burnett', 'Douglas', 'Iron', 'Sawyer', 'Vilas', 'Washburn']
    starter_region_02 = ['Barron', 'Chippewa', 'Dunn', 'Eau Claire', 'Pepin', 'Pierce', 'Polk', 'Rusk', 'St. Croix']
    starter_region_03 = ['Clark', 'Forest', 'Langlade', 'Lincoln', 'Marathon', 'Oneida', 'Price', 'Taylor']
    starter_region_04 = ['Brown', 'Door', 'Florence', 'Kewaunee', 'Marinette', 'Menominee', 'Oconto', 'Outagamie',
                         'Shawano', 'Waupaca']
    starter_region_05 = ['Buffalo', 'Jackson', 'Juneau', 'La Crosse', 'Monroe', 'Trempealeau', 'Vernon']
    starter_region_06 = ['Calumet', 'Dodge', 'Fond du Lac', 'Green Lake', 'Manitowoc', 'Marquette', 'Ozaukee', 'Sheboygan',
                         'Washington', 'Waushara', 'Winnebago']
    starter_region_07 = ['Adams', 'Columbia', 'Crawford', 'Dane', 'Grant', 'Green', 'Iowa', 'Lafayette', 'Portage',
                         'Richland', 'Sauk', 'Wood']
    starter_region_08 = ['Jefferson', 'Kenosha', 'Milwaukee', 'Racine', 'Rock', 'Walworth', 'Waukesha']

    ideal_region_tuples = [(x, 'ideal_region_01') for x in ideal_region_01] + \
                          [(x, 'ideal_region_02') for x in ideal_region_02] + \
                          [(x, 'ideal_region_03') for x in ideal_region_03] + \
                          [(x, 'ideal_region_04') for x in ideal_region_04] + \
                          [(x, 'ideal_region_05') for x in ideal_region_05] + \
                          [(x, 'ideal_region_06') for x in ideal_region_06] + \
                          [(x, 'ideal_region_07') for x in ideal_region_07]

    starter_region_tuples = [(x, 'starter_region_01') for x in starter_region_01] + \
                            [(x, 'starter_region_02') for x in starter_region_02] + \
                            [(x, 'starter_region_03') for x in starter_region_03] + \
                            [(x, 'starter_region_04') for x in starter_region_04] + \
                            [(x, 'starter_region_05') for x in starter_region_05] + \
                            [(x, 'starter_region_06') for x in starter_region_06] + \
                            [(x, 'starter_region_07') for x in starter_region_07] + \
                            [(x, 'starter_region_08') for x in starter_region_08]

    region_df = pd.DataFrame(ideal_region_tuples, columns=['county', 'ideal_proposal_region'])\
        .merge(pd.DataFrame(starter_region_tuples, columns=['county', 'starter_proposal_region']), on='county')\
        .sort_values('county')

    stop_df['county'] = stop_df['county'].str.strip()
    # https://stackoverflow.com/a/11982843
    stop_df = stop_df.reset_index().merge(region_df, how='left', on='county').set_index('LIBID')

    return stop_df


def geocode_api_request(x, api_key):

    geocode_base_url = "https://maps.googleapis.com/maps/api/geocode/json"

    request_url = f"{geocode_base_url}?address={x}&key={api_key}"

    json_result = urllib.request.urlopen(request_url).read()

    # results as JSON object
    response = json.loads(json_result)

    if response["status"] in ["OK", "ZERO_RESULTS"]:

        return (response['results'][0]['geometry']['location']['lat'],
                response['results'][0]['geometry']['location']['lng'])


def add_geocode_data(stop_data):

    # retrieve Google GEOCODING API key
    try:
        with open(os.path.expanduser('~/google_maps_api_key.yml'), 'r') as conf:
            conf_data = yaml.full_load(conf)
            geocode_api_key = conf_data['google_maps']['geocoding_api_key']
    except OSError as e:
        print(e)

    # build address string as URL formatted for API request
    # https://stackoverflow.com/a/33770421 - conditionally selecting rows

    # build urls for libraries with pluscode location data
    stop_data.loc[stop_data['pluscode'].notna(), 'geo_address_url_string'] = \
        stop_data['pluscode'].str.replace("+", "%2B").str.replace(" ", "%20").str.replace(",", "")

    # build urls for libraries with address location data
    #stop_data.loc[stop_data['pluscode'].isna(), 'geo_address_url_string'] = \
    #    stop_data['address_full_no_unit'].str.replace(",", "").str.split().str.join('%20')
    # https://stackoverflow.com/a/52270276
    address_cols = \
        ['address_number', 'address_street_dir_prefix', 'address_street', 'address_street_suffix',
         'address_street_dir_suffix', 'address_city', 'address_state', 'address_zip']
    stop_data.loc[stop_data['pluscode'].isna(), 'geo_address_url_string'] = \
        stop_data[address_cols].apply(lambda x: ' '.join(x.values.astype(str)), axis=1).str.replace('nan', '').str.split().str.join('%20')


    # add column with (lat, lon) pairs
    stop_data['geo_coords'] = stop_data['geo_address_url_string'].apply(geocode_api_request, api_key=geocode_api_key)

    # split lat, lon pairs into separate columns
    stop_data['latitude'] = stop_data['geo_coords'].apply(lambda x: x[0])
    stop_data['longitude'] = stop_data['geo_coords'].apply(lambda x: x[1])

    stop_data.drop(columns=['geo_address_url_string'], inplace=True)

    # return modified dataframe
    return stop_data


def main():

    # parse command line arguments
    parser = argparse.ArgumentParser(description='Add geocoding & region data to library directory data file.',
                                     usage='input_file {csv, xlsx} [-g/--geocode] [-r/--regions]'
                                           '\n     [-h]',
                                     add_help=False)
    parser.add_argument('input_file', action='store', type=str,
                        help="Name of file containing input library data ('csv' or 'xlsx' format).")
    parser.add_argument('out_format', choices=['csv', 'xlsx'], default='csv', type=str,
                        help="Updated data set output file format ('csv' or 'xlsx').")
    parser.add_argument('-g', '--geocode', action='store_true', help='Add location geocode data to data file.')
    parser.add_argument('-r', '--regions', action='store_true', help='Add proposed region data to data file.')

    args_dict = vars(parser.parse_args())

    infile_name = os.path.splitext(args_dict['input_file'])[0]
    outfile_name = infile_name
    infile_format = os.path.splitext(args_dict['input_file'])[1].replace('.', '')

    if infile_format == 'csv':
        input_df = pd.read_csv(
            args_dict['input_file'],
            header=0,
            index_col='LIBID',
            dtype=str
        )
    elif infile_format == 'xlsx':
        input_df = pd.read_excel(
            args_dict['input_file'],
            header=0,
            index_col='LIBID',
            dtype=str,
            engine='openpyxl'
        )

    input_df = input_df[input_df.index.notna()]

    if args_dict['geocode']:
        input_df = add_geocode_data(input_df)
        outfile_name += '_geo'
    if args_dict['regions']:
        input_df = add_region_data(input_df)
        outfile_name += '_reg'

    out_df = input_df

    if args_dict['out_format'] == 'csv':
        out_df.to_csv(outfile_name + '.csv')
    elif args_dict['out_format'] == 'xlsx':
        out_df.to_excel(outfile_name + '.xlsx', sheet_name='wi_library_directory')


if __name__ == '__main__':
    main()
