#! python3

import pandas as pd
import json
import urllib.request
import math

import pickle

def create_api_request_data(input_file):
    # Google Maps API key
    api_key = 'AIzaSyCg-TP3o4X0-rotbpHkKawcV8ytOZmCznI'

    # read in data as pandas dataframe
    stop_data = pd.read_excel(
        input_file,
        header=0,
        index_col='id',
        dtype=str,
        usecols='A:S')
        #['id', 'stop_short_name', 'stop_full_name',
        #         'address_number', 'address_street', 'address_city', 'address_state', 'address_zip9'
        #         'county', 'address_full', 'address_country', 'system', 'delivery_frequency'])

    # concatenate address string for api request
    stop_data['api_address_string'] = \
        stop_data['address_number'] + '+' + \
        stop_data['address_street'].str.split().str.join('+') + '+' + \
        stop_data['address_city'].str.split().str.join('+') + '+' + \
        stop_data['address_state']
    #stop_data.set_index('api_address_string')

    pd.set_option('display.width', 200)
    pd.set_option('display.max_columns', None)
    #print(stop_data)
    #print(stop_data.dtypes)

    # calculate number of request sets needed
    max_stops = 25  # maximum 25 origins or 25 destinations per request - https://stackoverflow.com/a/52062952
    num_addresses = len(stop_data['api_address_string'])
    num_sets = math.ceil(num_addresses / max_stops)

    # array containing lists of addresses for each set
    address_array = []
    for i in range(num_sets):
        address_array.append(stop_data['api_address_string'].tolist()[i * max_stops: (i + 1) * max_stops])

    # create & format data dictionary
    data_dict = {'api_key': api_key,
                 'addresses': address_array,
                 'library_info': stop_data.drop(
                     columns=['api_address_string']
                 ).to_dict('index')}
                 #).reindex().to_dict('index')}

    print(f'\n')
    print(data_dict)
    return data_dict


def create_matrices(data):
    api_key = data["api_key"]
    max_elements = 100
    dist_matrix_array = []
    dura_matrix_array = []

    for m in range(len(data['addresses'])):
        for n in range(len(data['addresses'])):
            setA = data['addresses'][m]
            setB = data['addresses'][n]

            # Distance Matrix API only accepts 100 elements per request, so get rows in multiple requests.
            num_addresses = len(setB)

            # Maximum number of rows that can be computed per request (6 in this example).
            max_rows = max_elements // num_addresses

            # num_addresses = q * max_rows + r (q = 2 and r = 4 in this example).
            q, r = divmod(len(setA), max_rows)

            dest_addresses = setB

            distance_matrix = []
            duration_matrix = []
            # Send q requests, returning max_rows rows per request.
            for i in range(q):
                origin_addresses = setA[i * max_rows: (i + 1) * max_rows]
                response = send_request(origin_addresses, dest_addresses, api_key)
                partial_matrices = build_matrices(response)
                distance_matrix += partial_matrices[0]
                duration_matrix += partial_matrices[1]

            # Get the remaining remaining r rows, if necessary.
            if r > 0:
                origin_addresses = setA[q * max_rows: q * max_rows + r]
                response = send_request(origin_addresses, dest_addresses, api_key)
                partial_matrices = build_matrices(response)
                distance_matrix += partial_matrices[0]
                duration_matrix += partial_matrices[1]

            dist_matrix_array.append(distance_matrix)
            dura_matrix_array.append(duration_matrix)

    full_dist_matrix = assemble_full_matrix(dist_matrix_array)
    full_dura_matrix = assemble_full_matrix(dura_matrix_array)

    return full_dist_matrix, full_dura_matrix


def send_request(origin_addresses, dest_addresses, api_key):
    """ Build and send request for the given origin and destination addresses."""

    def build_address_str(addresses):
        # Build a pipe-separated string of addresses
        address_str = ''
        for i in range(len(addresses) - 1):
            address_str += addresses[i] + '|'
        address_str += addresses[-1]

        return address_str

    request = 'https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial'
    origin_address_str = build_address_str(origin_addresses)
    dest_address_str = build_address_str(dest_addresses)
    request = request + '&origins=' + origin_address_str + '&destinations=' + \
              dest_address_str + '&key=' + api_key + '&units=imperial'

    jsonResult = urllib.request.urlopen(request).read()

    response = json.loads(jsonResult)

    return response


def build_matrices(response):
    distance_matrix = []
    duration_matrix = []
    for row in response['rows']:
        dist_row_list = [row['elements'][j]['distance']['value'] for j in range(len(row['elements']))]
        distance_matrix.append(dist_row_list)
        dura_row_list = [row['elements'][j]['duration']['value'] for j in range(len(row['elements']))]
        duration_matrix.append(dura_row_list)

    return distance_matrix, duration_matrix


def assemble_full_matrix(input_matrix):
    sections_per = int(math.sqrt(len(input_matrix)))

    row_list = []
    for i in range(sections_per):
        for r in range(len(input_matrix[i * sections_per])):
            this_row = []
            for j in range(sections_per):
                k = j + i * sections_per
                this_row += input_matrix[k][r]
            row_list.append(this_row)

    return row_list


def check_matrix_results(d_matrix):
    zero_indices = []
    for row in d_matrix:
        try:
            0 in row
        except ValueError:
            print('0 not found in row')
        zero_indices.append(row.index(0))

    check_list = [x for x in range(len(d_matrix))]

    try:
        zero_indices == check_list
    except RuntimeError:
        print('There was a problem building the matrix.')


def main():
    data_file = 'NWLS_delivery_stops.xlsx'

    input_data = create_api_request_data(data_file)
    #distance_matrix, duration_matrix = create_matrices(input_data)
    #check_matrix_results(distance_matrix)
    #check_matrix_results(duration_matrix)

    #data_dict = {'distance_matrix': distance_matrix,
    #             'duration_matrix': duration_matrix,
    #             'library_info': input_data['library_info']}

    #with open('vrp_data_dict.pickle', 'wb') as pick_file:
    #    pickle.dump(data_dict, pick_file)


if __name__ == '__main__':
    main()
