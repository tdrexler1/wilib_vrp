import math
import urllib.request
import json
import argparse
import os
import pandas as pd
import yaml
import sys
import pickle
import openrouteservice


def parse_args():
    # noinspection PyTypeChecker
    parser_obj = argparse.ArgumentParser(
        prog='tool',
        description='Build and pickle the distance and duration matrices for a proposed WI library delivery region.',
        usage='input_file {ideal, starter} region_number '
              '\n       [-h/--help]',
        add_help=False,
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=27, width=200)
    )

    setup_group = parser_obj.add_argument_group(title='Problem setup arguments')
    setup_group.add_argument('input_file', action='store', type=str,
                             help="Name of file containing input library data ('csv' or 'xlsx' format).")
    setup_group.add_argument('model', choices=['ideal', 'starter'], default='ideal',
                             help='PLSR Delivery Workgroup proposed model version.')
    setup_group.add_argument('region_number', type=int, choices=range(1, 8) if 'ideal' in sys.argv else range(1, 9),
                             help='Model region number (1-7 for ideal model, 1-8 for starter model).')

    parser_obj.add_argument('-h', '--help', action='help', help='Show this message and exit.')

    return vars(parser_obj.parse_args())


def prep_input_data(in_dataframe, config_dict):

    model_region = config_dict['model'] + '_region_' + \
        ('0' + str(config_dict['region_number'])
         if config_dict['region_number'] < 10
         else str(config_dict['region_number'])
         )

    model_column = config_dict['model'] + '_proposal_region'
    hub_column = config_dict['model'] + '_regional_hub'

    region_stop_data = in_dataframe.loc[(in_dataframe[model_column] == model_region) &
                                        (in_dataframe['redundant_address'].str.lower() == 'false')].copy()

    region_stop_data.sort_values(hub_column, inplace=True)

    region_stop_data['api_address_string'] = \
        region_stop_data['address_number'] + '+' + \
        region_stop_data['address_street'].str.split().str.join('+') + '+' + \
        region_stop_data['address_city'].str.split().str.join('+') + '+' + \
        region_stop_data['address_state']

    return region_stop_data


def create_api_geoloc_lists(stop_df):

    # limit 25 origins or 25 destinations per API request - https://stackoverflow.com/a/52062952
    # divide data into groups w/ max 25 addresses

    stop_coords = [[eval(x)[1], eval(x)[0]] for x in stop_df['geo_coords']]
    max_stops = 25
    num_addresses = len(stop_df['geo_coords'])

    num_groups = math.ceil(num_addresses / max_stops)

    # store each address group as nested list
    address_array = []
    for i in range(num_groups):
        address_array.append(stop_coords[i * max_stops: (i + 1) * max_stops])

    return address_array


def create_matrices(address_array, config_dict):
    """ Sends Google Maps API requests to create distance & duration matrices for each group of addresses;
    assembles group matrices into full matrices.

    Params:


    Returns:
        Distance and duration matrices w/ rows as nested lists.
    """

    ors_client = openrouteservice.Client(key=config_dict['ors_key'])

    distance_matrix_array = []
    duration_matrix_array = []

    # destination addresses for each group in address array
    for m in range(len(address_array)):
        #destination_group = address_array[m]
        origin_group = address_array[m]

        # origin addresses for each group in address array
        for n in range(len(address_array)):
            #origin_group = address_array[n]
            destination_group = address_array[n]

            numbers = list( range( len( origin_group ), ( len(origin_group) + len( destination_group) ) ) )

            request = {'locations': origin_group+destination_group,
                       'destinations': numbers,
                       'metrics': ['distance', 'duration'],
                       'units': 'm'}

            response_dict = ors_client.distance_matrix(**request)

            group_distance_matrix = response_dict['distances'][:len(origin_group)]
            group_duration_matrix = response_dict['durations'][:len(origin_group)]

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


def save_matrices(distance_matrix, duration_matrix, conf_dict):

    matrice_dict = {'distance_matrix': distance_matrix, 'duration_matrix': duration_matrix}

    output_dir_path = os.path.expanduser('~\\PycharmProjects\\wilib_vrp\\solution_output\\')
    if not os.path.isdir(output_dir_path):
        os.mkdir(output_dir_path)

    pickle_name = \
        output_dir_path + \
        conf_dict['model'] + \
        str(conf_dict['region_number']) + \
        '_matrices.pickle'

    with open(pickle_name, 'wb') as pick_file:
        pickle.dump(matrice_dict, pick_file)


def main():
    args_dict = parse_args()

    infile_format = os.path.splitext(args_dict['input_file'])[1].replace('.', '')

    if infile_format == 'csv':
        stop_data = pd.read_csv(
            args_dict['input_file'],
            header=0,
            index_col='LIBID',
            dtype=str
        )
    elif infile_format == 'xlsx':
        stop_data = pd.read_excel(
            args_dict['input_file'],
            header=0,
            index_col='LIBID',
            dtype=str,
            engine='openpyxl'
        )

    try:
        with open(os.path.expanduser('~/google_maps_api_key.yml'), 'r') as api_keys:
            key_data = yaml.full_load(api_keys)
    except OSError as e:
        print(e)

    args_dict['ors_key'] = key_data['open_route_service']['ors_key']

    region_data = prep_input_data(stop_data, args_dict)

    api_address_array = create_api_geoloc_lists(region_data)

    # create distance & duration matrices
    print('Building distance and duration matrices...')
    distance_matrix, duration_matrix = create_matrices(api_address_array, args_dict)

    # check results
    check_matrix_results(distance_matrix)
    check_matrix_results(duration_matrix)
    print('Distance and duration matrices complete.')

    #print(distance_matrix)
    #print(duration_matrix)

    save_matrices(distance_matrix, duration_matrix, args_dict)


if __name__ == '__main__':
    main()