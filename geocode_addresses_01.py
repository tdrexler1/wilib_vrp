#! python3

import pandas as pd
import json
import urllib.request
import os
import yaml

pd.options.display.width = 0
GEOCODE_BASE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

def geocode_api_request(x, api_key):
    #GEOCODE_BASE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

    request_url = f"{GEOCODE_BASE_URL}?address={x}&key={api_key}"

    json_result = urllib.request.urlopen(request_url).read()

    # results as JSON object
    response = json.loads(json_result)

    if response["status"] in ["OK", "ZERO_RESULTS"]:
        # print(response)
        #print(f"lat = {response['results'][0]['geometry']['location']['lat']}, "
        #      f"lng = {response['results'][0]['geometry']['location']['lng']}")
        return (response['results'][0]['geometry']['location']['lat'],
                response['results'][0]['geometry']['location']['lng'])


def geocode_addresses(input_file):
    """ Adds geocodes for library locations using address and/or PlusCode data.

    Params:
        input_file: Excel filename.

    Returns:
        None
    """

    # Google GEOCODING API key
    try:
        with open(os.path.expanduser('~/google_maps_api_key.yml'), 'r') as conf:
            conf_data = yaml.full_load(conf)
            geocode_api_key = conf_data['google_maps']['geocoding_api_key']
    except OSError as e:
        print(e)

    # read in data
    stop_data = pd.read_excel(
        input_file,
        header=0,
        index_col='LIBID',
        dtype=str,
        engine='openpyxl')

    # build address string formatted for API request
    stop_data['geo_address_url_string'] = stop_data['address_full_no_unit'].str.replace(",", "").str.split().str.join('%20')
        #stop_data['address_number'] + '%20' + \
        #stop_data['address_street'].str.split().str.join('%20') + '%20' + \
        #stop_data['address_city'].str.split().str.join('%20') + '%20' + \
        #stop_data['address_state']
    #print(stop_data['geo_address_url_string'])

    # TODO: pull id column & geo_address_url_string columns; convert to dict
    # TODO: iterate through dict keys to send requests, return results to lat & lng keys
    # TODO: convert dict to dataframe and left join to stop data
    # TODO: seems like there should be a better way to do this??? how about DataFrame.apply()

    stop_data['geo_coords'] = stop_data['geo_address_url_string'].apply(geocode_api_request, api_key = geocode_api_key)
    stop_data['latitude'] = stop_data['geo_coords'].apply(lambda x: x[0])
    stop_data['longitude'] = stop_data['geo_coords'].apply(lambda x: x[1])
    stop_data = stop_data.drop(['geo_address_url_string'], axis=1)
    #print(stop_data[['stop_short_name', 'geo_coords', 'latitude', 'longitude']].head(10))
    stop_data.to_excel('wi_library_directory_testfile_small.xlsx')


    '''address_urls_list = stop_data['geo_address_url_string'].tolist()

    for address_url in address_urls_list:

        request_url = f"{GEOCODE_BASE_URL}?address={address_url}&key={geocode_api_key}"

        json_result = urllib.request.urlopen(request_url).read()

        # results as JSON object
        response = json.loads(json_result)

        if response["status"] in ["OK", "ZERO_RESULTS"]:
            #print(response)
            print(f"lat = {response['results'][0]['geometry']['location']['lat']}, "
                  f"lng = {response['results'][0]['geometry']['location']['lng']}")
        #result = json.load(urllib.request.urlopen(url))

        #if result["status"] in ["OK", "ZERO_RESULTS"]:
        #    print(json.dumps(result))
            #print(json.dumps([s["formatted_address"] for s in result], indent=2))
        #    return result["results"]'''

    #raise Exception(result["error_message"])




def main():
    data_file = 'wi_library_directory_testfile_small.xlsx'

    # read and format address data
    #geocode_addresses(data_file)

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
    stop_data['geo_address_url_string'] = stop_data['address_full_no_unit'].str.replace(",", "").str.split().str.join('%20')
    stop_data['geo_coords'] = stop_data['geo_address_url_string'].apply(geocode_api_request, api_key = geocode_api_key)
    stop_data['latitude'] = stop_data['geo_coords'].apply(lambda x: x[0])
    stop_data['longitude'] = stop_data['geo_coords'].apply(lambda x: x[1])
    stop_data = stop_data.drop(['geo_address_url_string'], axis=1)
    #print(stop_data[['stop_short_name', 'geo_coords', 'latitude', 'longitude']].head(10))
    stop_data.to_excel(data_file)

if __name__ == '__main__':
    main()
