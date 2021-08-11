#! python3

import argparse
import pandas as pd
import os
import yaml
import json
import urllib.request

def parse_args():
    """
    Sets up parser and help menu for command-line arguments.

    :return: A dict with argument, value entries.
    :rtype: dict
    """

    # instantiate parser object with description & help menu
    parser_obj = argparse.ArgumentParser(description='Add geocoding & region data to library directory data file.',
                                         usage='input_file {csv, xlsx} [-g/--geocode] [-r/--regions]'
                                               '\n     [-h]',
                                         add_help=False)
    parser_obj.add_argument('input_file', action='store', type=str,
                            help="Name of file containing input library data ('csv' or 'xlsx' format).")
    parser_obj.add_argument('out_format', choices=['csv', 'xlsx'], default='csv', type=str,
                            help="Updated data set output file format ('csv' or 'xlsx').")
    parser_obj.add_argument('-g', '--geocode', action='store_true', help='Add location geocode data to data file.')
    parser_obj.add_argument('-r', '--regions', action='store_true', help='Add proposed region data to data file.')

    # return argument values as dict
    return vars(parser_obj.parse_args())


def add_region_data(stop_df):
    """
    Adds columns to library DataFrame with labels indicating proposal and region
    number for each library based on the 'County' column value.

    :param stop_df: Input DataFrame of library data.
    :type stop_df: pandas.DataFrame
    :return: Updated DataFrame with added columns.
    :rtype: pandas.DataFrame
    """

    # lists of counties in each region of PLSR proposals
    ideal_region_01 = ['Ashland', 'Barron', 'Bayfield', 'Burnett', 'Chippewa', 'Douglas', 'Dunn', 'Eau Claire', 'Pepin',
                       'Pierce', 'Polk', 'Rusk', 'Sawyer', 'St. Croix', 'Washburn']
    ideal_region_02 = ['Clark', 'Forest', 'Iron', 'Langlade', 'Lincoln', 'Marathon', 'Oneida', 'Portage', 'Price',
                       'Taylor', 'Vilas', 'Wood']
    ideal_region_03 = ['Brown', 'Door', 'Florence', 'Kewaunee', 'Marinette', 'Menominee', 'Oconto', 'Outagamie',
                       'Shawano', 'Waupaca']
    ideal_region_04 = ['Adams', 'Buffalo', 'Crawford', 'Jackson', 'Juneau', 'La Crosse', 'Monroe', 'Richland',
                       'Trempealeau', 'Vernon']
    ideal_region_05 = ['Calumet', 'Dodge', 'Fond du Lac', 'Green Lake', 'Manitowoc', 'Marquette', 'Ozaukee',
                       'Sheboygan', 'Washington', 'Waushara', 'Winnebago']
    ideal_region_06 = ['Columbia', 'Dane', 'Grant', 'Green', 'Iowa', 'Lafayette', 'Rock', 'Sauk']
    ideal_region_07 = ['Jefferson', 'Kenosha', 'Milwaukee', 'Racine', 'Walworth', 'Waukesha']

    starter_region_01 = ['Ashland', 'Bayfield', 'Burnett', 'Douglas', 'Iron', 'Sawyer', 'Vilas', 'Washburn']
    starter_region_02 = ['Barron', 'Chippewa', 'Dunn', 'Eau Claire', 'Pepin', 'Pierce', 'Polk', 'Rusk', 'St. Croix']
    starter_region_03 = ['Clark', 'Forest', 'Langlade', 'Lincoln', 'Marathon', 'Oneida', 'Price', 'Taylor']
    starter_region_04 = ['Brown', 'Door', 'Florence', 'Kewaunee', 'Marinette', 'Menominee', 'Oconto', 'Outagamie',
                         'Shawano', 'Waupaca']
    starter_region_05 = ['Buffalo', 'Jackson', 'Juneau', 'La Crosse', 'Monroe', 'Trempealeau', 'Vernon']
    starter_region_06 = ['Calumet', 'Dodge', 'Fond du Lac', 'Green Lake', 'Manitowoc', 'Marquette', 'Ozaukee',
                         'Sheboygan', 'Washington', 'Waushara', 'Winnebago']
    starter_region_07 = ['Adams', 'Columbia', 'Crawford', 'Dane', 'Grant', 'Green', 'Iowa', 'Lafayette', 'Portage',
                         'Richland', 'Sauk', 'Wood']
    starter_region_08 = ['Jefferson', 'Kenosha', 'Milwaukee', 'Racine', 'Rock', 'Walworth', 'Waukesha']

    # create & concatenate lists of tuples (library name, region label)
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

    # create & merge DataFrames with region labels for each county
    region_df = pd.DataFrame(ideal_region_tuples, columns=['county', 'ideal_proposal_region'])\
        .merge(pd.DataFrame(starter_region_tuples, columns=['county', 'starter_proposal_region']), on='county')\
        .sort_values('county')

    # remove any spaces from county names
    stop_df['county'] = stop_df['county'].str.strip()

    # merge regional labels DataFrame & library DataFrame, reset index
    # https://stackoverflow.com/a/11982843
    stop_df = stop_df.reset_index().merge(region_df, how='left', on='county').set_index('LIBID')

    return stop_df


def geocode_api_request(x, api_key):
    """
    Utility function to build Google Maps Geocoding Service API request URL strings.

    :param x: An API-formatted string of the library's address.
    :type x: str
    :param api_key: Google Maps Geocoding API key.
    :type api_key: str
    :return: Latitude, longitude pair as tuple.
    :rtype: tuple
    """

    # construct request url string
    geocode_base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    request_url = f"{geocode_base_url}?address={x}&key={api_key}"

    # send geocoding API request
    json_result = urllib.request.urlopen(request_url).read()

    # API request results as JSON object
    response = json.loads(json_result)

    # if geocoding service located the stop, return geocoordinates
    if response["status"] in ["OK", "ZERO_RESULTS"]:

        return (response['results'][0]['geometry']['location']['lat'],
                response['results'][0]['geometry']['location']['lng'])


def add_geocode_data(stop_df):
    """
    Adds column to library DataFrame with geocoded location data formatted
    as (latitude, longitude) tuple.

    :param stop_df: Input DataFrame of library data.
    :type stop_df: pandas.DataFrame
    :return: Updated DataFrame with added geolocation data column.
    :rtype: pandas.DataFrame
    """

    # retrieve Google Maps Geocoding Service API key
    try:
        with open(os.path.expanduser('~/google_maps_api_key.yml'), 'r') as conf:
            conf_data = yaml.full_load(conf)
    except OSError as e:
        print(e)

    geocode_api_key = conf_data['google_maps']['geocoding_api_key']

    # https://stackoverflow.com/a/33770421 - conditionally selecting rows

    # build url address strings for libraries with pluscode location data
    stop_df.loc[stop_df['pluscode'].notna(), 'geo_address_url_string'] = \
        stop_df['pluscode'].str.replace("+", "%2B").str.replace(" ", "%20").str.replace(",", "")

    # build urls for libraries with address location data
    # https://stackoverflow.com/a/52270276 - concatenate multiple column values
    address_cols = \
        ['address_number', 'address_street_dir_prefix', 'address_street', 'address_street_suffix',
         'address_street_dir_suffix', 'address_city', 'address_state', 'address_zip']
    stop_df.loc[stop_df['pluscode'].isna(), 'geo_address_url_string'] = \
        stop_df[address_cols].apply(lambda x: ' '.join(x.values.astype(str)),
                                    axis=1).str.replace('nan', '').str.split().str.join('%20')

    # use 'apply' method to add column with (lat, lon) tuples
    stop_df['geo_coords'] = stop_df['geo_address_url_string'].apply(geocode_api_request, api_key=geocode_api_key)

    # split lat, lon pairs into separate columns
    stop_df['latitude'] = stop_df['geo_coords'].apply(lambda x: x[0])
    stop_df['longitude'] = stop_df['geo_coords'].apply(lambda x: x[1])

    stop_df.drop(columns=['geo_address_url_string'], inplace=True)

    return stop_df


def main():
    """
    Adds geolocation data and PLSR Delivery Workgroup proposal region labels
    to input data file. Outputs the updated file in 'csv' or 'xlsx' format.
    """

    # parse command-line arguments using 'argparse' module
    args_dict = parse_args()

    # parse name & file format of input data file
    infile_name = os.path.splitext(args_dict['input_file'])[0]
    infile_format = os.path.splitext(args_dict['input_file'])[1].replace('.', '')

    # import data to Pandas DataFrame
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

    # remove any empty rows
    input_df = input_df[input_df.index.notna()]

    outfile_name = infile_name

    # add requested data & set output file name
    if args_dict['geocode']:
        input_df = add_geocode_data(input_df)
        outfile_name += '_geo'

    if args_dict['regions']:
        input_df = add_region_data(input_df)
        outfile_name += '_reg'

    out_df = input_df

    # output to selected file format
    if args_dict['out_format'] == 'csv':
        out_df.to_csv(outfile_name + '.csv')

    elif args_dict['out_format'] == 'xlsx':
        out_df.to_excel(outfile_name + '.xlsx', sheet_name='wi_library_directory')


if __name__ == '__main__':
    main()
