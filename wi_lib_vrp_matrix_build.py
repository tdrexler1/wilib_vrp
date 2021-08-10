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
    """
    Sets up parser and help menu for command-line arguments.

    :return: A dict with argument, value entries.
    :rtype: dict
    """

    # noinspection PyTypeChecker
    parser_obj = argparse.ArgumentParser(
        prog='tool',
        description='Build and pickle the distance and duration matrices for a proposed WI library delivery region.',
        usage='input_file {ideal, starter} region_number '
              '\n       [-h/--help]',
        add_help=False,
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=27, width=200)
    )

    # argument group for setup parameters
    setup_group = parser_obj.add_argument_group(title='Problem setup arguments')
    setup_group.add_argument('input_file', action='store', type=str,
                             help="Name of file containing input library data ('csv' or 'xlsx' format).")
    setup_group.add_argument('model', choices=['ideal', 'starter'], default='ideal',
                             help='PLSR Delivery Workgroup proposed model version.')
    setup_group.add_argument('region_number', type=int, choices=range(1, 8) if 'ideal' in sys.argv else range(1, 9),
                             help='Model region number (1-7 for ideal model, 1-8 for starter model).')

    # add help menu
    parser_obj.add_argument('-h', '--help', action='help', help='Show this message and exit.')

    # return argument values as dict
    return vars(parser_obj.parse_args())


def prep_input_data(in_dataframe, config_dict):
    """Prepares imported library stop data to build distance & duration matrices.

    Filters imported library data to stops in region of interest. Sorts data to
    place regional hub as first stop. Concatenates address string from address
    components.

    :param in_dataframe: Pandas DataFrame of input data from external file.
    :type in_dataframe: DataFrame
    :param config_dict: Dict of VRP configuration settings.
    :type config_dict: dict
    :return: Pandas DataFrame of regional stop data.
    :rtype: DataFrame
    """

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
    """
    Creates array of library stop geolocations.

    :param stop_df: Pandas DataFrame of filtered, formatted library stop data.
    :type stop_df: DataFrame
    :return: Nested lists of library geolocations.
    :rtype: list
    """

    # list of longitude, latitude pairs formatted as lists
    stop_coords = [[eval(x)[1], eval(x)[0]] for x in stop_df['geo_coords']]

    # divide data into groups w/ max 25 addresses to meet API request limits
    max_stops = 25

    # total number of stops
    num_addresses = len(stop_df['geo_coords'])

    # calculate number of 'groups' required
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
    """Functionality to build distance & duration matrices from command line."""

    # parse command-line arguments using 'argparse' module
    args_dict = parse_args()

    # parse whether data input file is 'csv' or 'xlsx' format, used by pandas read function
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

    # retrieve API keys for openrouteservice from YAML file
    try:
        with open(os.path.expanduser('~/wi_lib_vrp_api_keys.yml'), 'r') as api_keys:
            key_data = yaml.full_load(api_keys)
    except OSError as e:
        print(e)

    # add openrouteservice API key to dict of command line args
    args_dict['ors_key'] = key_data['open_route_service']['ors_key']

    # initialize pandas dataframe w/ data for all library locations in region
    region_data = prep_input_data(stop_data, args_dict)

    # retrieve library geolocations formatted as nested arrays
    api_geolocs_array = create_api_geoloc_lists(region_data)

    print('Building distance and duration matrices...')

    # save distance & duration matrices
    distance_matrix, duration_matrix = create_matrices(api_geolocs_array, args_dict)

    # check formatting of distance & duration matrices
    check_matrix_results(distance_matrix)
    check_matrix_results(duration_matrix)
    print('Distance and duration matrices complete.')

    # pickle distance & duration matrices
    save_matrices(distance_matrix, duration_matrix, args_dict)


if __name__ == '__main__':
    main()