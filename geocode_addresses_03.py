#! python3

import pandas as pd
import json
import urllib.request
import os
import yaml

pd.options.display.width = 0
GEOCODE_BASE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

ideal_region_01 = ['Ashland', 'Barron', 'Bayfield', 'Burnett', 'Chippewa', 'Douglas', 'Dunn', 'Eau Claire', 'Pepin',
                   'Pierce', 'Polk', 'Rusk', 'Sawyer', 'St. Croix', 'Washburn'] #15
ideal_region_02 = ['Clark', 'Forest', 'Iron', 'Langlade', 'Lincoln', 'Marathon', 'Oneida', 'Portage', 'Price',
                   'Taylor', 'Vilas', 'Wood'] #12
ideal_region_03 = ['Brown', 'Door', 'Florence', 'Kewaunee', 'Marinette', 'Menominee', 'Oconto', 'Outagamie',
                   'Shawano', 'Waupaca'] #10
ideal_region_04 = ['Adams', 'Buffalo', 'Crawford', 'Jackson', 'Juneau', 'La Crosse', 'Monroe', 'Richland',
                   'Trempaealeau', 'Vernon'] #10
ideal_region_05 = ['Calumet', 'Dodge', 'Fond du Lac', 'Green Lake', 'Manitowoc', 'Marquette', 'Ozaukee', 'Sheboygan',
                   'Washington', 'Waushara', 'Winnebago'] #11
ideal_region_06 = ['Columbia', 'Dane', 'Grant', 'Green', 'Iowa', 'Lafeyette', 'Rock', 'Sauk'] #8
ideal_region_07 = ['Jefferson', 'Kenosha', 'Milwaukee', 'Racine', 'Walworth', 'Waukesha'] #6

starter_region_01 = ['Ashland', 'Bayfield', 'Burnett', 'Douglas', 'Iron', 'Sawyer', 'Vilas', 'Washburn'] #8
starter_region_02 = ['Barron', 'Chippewa', 'Dunn', 'Eau Claire', 'Pepin', 'Pierce', 'Polk', 'Rusk', 'St. Croix'] #9
starter_region_03 = ['Clark', 'Forest', 'Langlade', 'Lincoln', 'Marathon', 'Oneida', 'Price', 'Taylor'] #8
starter_region_04 = ['Brown', 'Door', 'Florence', 'Kewaunee', 'Marinette', 'Menominee', 'Oconto', 'Outagamie',
                     'Shawano', 'Waupaca'] #10
starter_region_05 = ['Buffalo', 'Jackson', 'Juneau', 'La Crosse', 'Monroe', 'Trempealeau', 'Vernon'] #7
starter_region_06 = ['Calumet', 'Dodge', 'Fond du Lac', 'Green Lake', 'Manitowoc', 'Marquette', 'Ozaukee', 'Sheboygan',
                     'Washington', 'Waushara', 'Winnebago'] #11
starter_region_07 = ['Adams', 'Columbia', 'Crawford', 'Dane', 'Grant', 'Green', 'Iowa', 'Lafayette', 'Portage',
                     'Richland', 'Sauk', 'Wood'] #12
starter_region_08 = ['Jefferson', 'Kenosha', 'Milwaukee', 'Racine', 'Rock', 'Walworth', 'Waukesha'] #7

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

    stop_data.to_csv(os.path.splitext(data_file)[0] + '_geo.csv')


if __name__ == '__main__':
    main()
