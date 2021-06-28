#! python3

import pandas as pd
import json
import urllib.request
import os
import yaml

pd.options.display.width = 0
GEOCODE_BASE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


def geocode_api_request(x, api_key):

    request_url = f"{GEOCODE_BASE_URL}?address={x}&key={api_key}"

    json_result = urllib.request.urlopen(request_url).read()

    # results as JSON object
    response = json.loads(json_result)

    if response["status"] in ["OK", "ZERO_RESULTS"]:

        return (response['results'][0]['geometry']['location']['lat'],
                response['results'][0]['geometry']['location']['lng'])


def main():
    data_file = 'wi_library_directory_testfile_small.xlsx'

    # Google GEOCODING API key
    try:
        with open(os.path.expanduser('~/google_maps_api_key.yml'), 'r') as conf:
            conf_data = yaml.full_load(conf)
            geocode_api_key = conf_data['google_maps']['geocoding_api_key']
    except OSError as e:
        print(e)

    # read in data
    stop_data = pd.read_excel(
        data_file,
        header=0,
        index_col='LIBID',
        dtype=str,
        engine='openpyxl')

    # build address string as URL formatted for API request

    # https: // stackoverflow.com / a / 33770421
    # potential mask: stop_data_pluscodes = stop_data[stop_data['pluscode'].notna()]

    stop_data.loc[stop_data['pluscode'].notna(), 'geo_address_url_string'] = \
        stop_data['pluscode'].str.replace("+", "%2B").str.replace(" ", "%20").str.replace(",", "")
    stop_data.loc[stop_data['pluscode'].isna(), 'geo_address_url_string'] = \
        stop_data['address_full_no_unit'].str.replace(",", "").str.split().str.join('%20')
    stop_data['geo_coords'] = stop_data['geo_address_url_string'].apply(geocode_api_request, api_key=geocode_api_key)
    stop_data['latitude'] = stop_data['geo_coords'].apply(lambda x: x[0])
    stop_data['longitude'] = stop_data['geo_coords'].apply(lambda x: x[1])

    # TODO: drop all columns not used for mapping
    '''drop_cols = ['address_number', 'address_street_dir_prefix', 'address_street', 'address_street_suffix',
                 'adddress_street_unit', 'address_street_number', 'address_street_number_no_unit', 'address_city',
                 'address_state', 'address_zip', 'address_zip4', 'address_zip9', 'address_country',
                 'address_verified_01', 'address_verified_02', 'geoloc_verified', 'geo_address_url_string']
    stop_data = stop_data.drop(drop_cols, axis=1)'''
    #stop_data = stop_data.drop(['geo_address_url_string'], axis=1)

    stop_data.to_csv(os.path.splitext(data_file)[0] + '_geo.csv')


if __name__ == '__main__':
    main()
