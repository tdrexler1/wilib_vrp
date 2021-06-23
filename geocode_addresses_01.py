#! python3

import pandas as pd
import json
import urllib.request
import os
import yaml

GEOCODE_BASE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

def geocode_api_request(x, api_key):
    #GEOCODE_BASE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

    request_url = f"{GEOCODE_BASE_URL}?address={x}&key={api_key}"

    json_result = urllib.request.urlopen(request_url).read()

    # results as JSON object
    response = json.loads(json_result)

    if response["status"] in ["OK", "ZERO_RESULTS"]:
        # print(response)
        print(f"lat = {response['results'][0]['geometry']['location']['lat']}, "
              f"lng = {response['results'][0]['geometry']['location']['lng']}")
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

    stop_data['geo_coords'] = stop_data.apply(geocode_api_request(stop_data['geo_address_url_string'], geocode_api_key))

    print(stop_data.head())



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


'''
def create_matrices(stop_data_dict):
    """ Sends Google Maps API requests to create distance & duration matrices for each group of addresses;
    assembles group matrices into full matrices.

    Params:
        stop_data_dict: Dict containing data for each stop, including addresses formatted as API request strings.

    Returns:
        Distance and duration matrices w/ rows as nested lists.
    """

    api_key = stop_data_dict["api_key"]
    max_elements = 100  # limit 100 elements per API request - https://tinyurl.com/3sywy4ky

    distance_matrix_array = []
    duration_matrix_array = []

    # destination addresses for each group in address array
    for m in range(len(stop_data_dict['addresses'])):
        destination_group = stop_data_dict['addresses'][m]

        # origin addresses for each group in address array
        for n in range(len(stop_data_dict['addresses'])):
            origin_group = stop_data_dict['addresses'][n]

            max_rows = max_elements // len(origin_group)

            # q * max_rows + r = number of addresses in group
            q, r = divmod(len(destination_group), max_rows)

            group_distance_matrix = []
            group_duration_matrix = []

            # q API requests of max_rows each
            for i in range(q):
                destination_addresses = destination_group[i * max_rows: (i + 1) * max_rows]
                response = send_request(destination_addresses, origin_group, api_key)

                # build partial matrices from API response
                partial_matrices = build_matrices(response)

                group_distance_matrix += partial_matrices[0]
                group_duration_matrix += partial_matrices[1]

            # remaining r rows
            if r > 0:
                destination_addresses = destination_group[q * max_rows: q * max_rows + r]
                response = send_request(destination_addresses, origin_group, api_key)

                # build partial matrices from API response
                partial_matrices = build_matrices(response)

                group_distance_matrix += partial_matrices[0]
                group_duration_matrix += partial_matrices[1]

            distance_matrix_array.append(group_distance_matrix)
            duration_matrix_array.append(group_duration_matrix)

    # create full matrices from arrays of group matrices
    full_distance_matrix = assemble_full_matrix(distance_matrix_array)
    full_duration_matrix = assemble_full_matrix(duration_matrix_array)

    return full_distance_matrix, full_duration_matrix


def send_request(orig_addresses, dest_addresses, api_key):
    """ Builds Google Maps API request string, sends API request, and stores results as JSON object.

     Params:
         orig_addresses: List of address strings.
         dest_addresses: List of address strings.
         api_key: String of Google Maps API key.

    Returns:
        A JSON object with API request results.
     """

    def build_address_str(addresses):

        # pipe-separated string of addresses
        address_str = ''
        for i in range(len(addresses) - 1):
            address_str += addresses[i] + '|'
        address_str += addresses[-1]

        return address_str

    request = 'https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial'

    origin_address_str = build_address_str(orig_addresses)
    dest_address_str = build_address_str(dest_addresses)

    # assemble request string
    request = request + '&origins=' + origin_address_str + '&destinations=' + \
        dest_address_str + '&key=' + api_key + '&units=imperial'

    # send API request
    json_result = urllib.request.urlopen(request).read()

    # results as JSON object
    response = json.loads(json_result)

    return response


def build_matrices(response):
    """ Creates partial matrices from each set of API request results.

     Params:
         response: JSON object.

    Returns:
        Nested lists representing each 'row' in the partial matrix.
     """

    dist_matrix = []
    dura_matrix = []

    # pull distance & duration values from API request response
    for row in response['rows']:
        dist_row_list = [row['elements'][j]['distance']['value'] for j in range(len(row['elements']))]
        dist_matrix.append(dist_row_list)
        dura_row_list = [row['elements'][j]['duration']['value'] for j in range(len(row['elements']))]
        dura_matrix.append(dura_row_list)

    return dist_matrix, dura_matrix


def assemble_full_matrix(input_matrix):
    """ Builds full matrix from address group matrices. """

    # number of groups along each axis of full matrix
    groups_per = int(math.sqrt(len(input_matrix)))

    row_list = []

    # 'i' & 'j' iterate over group matrices
    for i in range(groups_per):

        # 'r' iterates over rows/lists in each group
        for r in range(len(input_matrix[i * groups_per])):
            this_row = []

            # 'i' & 'j' iterate over group matrices
            for j in range(groups_per):

                # 'k' = index of group in input_matrix
                k = j + i * groups_per

                this_row += input_matrix[k][r]

            row_list.append(this_row)

    return row_list


def check_matrix_results(d_matrix):
    """ Checks that matrix contains zeroes on diagonal as expected. """

    # row indices of zeroes
    zero_indices = []
    for row in d_matrix:
        try:
            0 in row
        except ValueError:
            print('0 not found in row')
        zero_indices.append(row.index(0))

    # list of sequential integers
    check_list = [x for x in range(len(d_matrix))]

    # compare zero indices with integers
    try:
        zero_indices == check_list
    except RuntimeError:
        print('There was a problem building the matrix.')
'''

def main():
    data_file = 'wi_library_directory_testfile.xlsx'

    # read and format address data
    geocode_addresses(data_file)



    '''
    # create distance & duration matrices w/ Google Maps API
    distance_matrix, duration_matrix = create_matrices(input_data)

    # check results
    check_matrix_results(distance_matrix)
    check_matrix_results(duration_matrix)

    # store matrices & dataframe of descriptive data
    data_dict = {'distance_matrix': distance_matrix,
                 'duration_matrix': duration_matrix,
                 'library_info': input_data['library_info']}

    with open('vrp_data_dict.pickle', 'wb') as pick_file:
        pickle.dump(data_dict, pick_file)
    '''


if __name__ == '__main__':
    main()
