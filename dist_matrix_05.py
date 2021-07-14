import math
import urllib.request
import json


def prep_input_data(in_dataframe, config_dict):

    model_region = config_dict['model'] + '_region_' + \
        ('0' + str(config_dict['region_number'])
         if config_dict['region_number'] < 10
         else str(config_dict['region_number'])
         )

    model_column = config_dict['model'] + '_proposal_region'
    hub_column = config_dict['model'] + '_regional_hub'

    region_stop_data = in_dataframe.loc[(in_dataframe[model_column] == model_region) &
                                        (in_dataframe['redundant_address'] == 'False')].copy()
    region_stop_data.sort_values(hub_column, inplace=True)

    region_stop_data['api_address_string'] = \
        region_stop_data['address_number'] + '+' + \
        region_stop_data['address_street'].str.split().str.join('+') + '+' + \
        region_stop_data['address_city'].str.split().str.join('+') + '+' + \
        region_stop_data['address_state']

    return region_stop_data


def create_api_address_lists(stop_df):

    # limit 25 origins or 25 destinations per API request - https://stackoverflow.com/a/52062952
    # divide data into groups w/ max 25 addresses
    max_stops = 25
    num_addresses = len(stop_df['api_address_string'])
    num_groups = math.ceil(num_addresses / max_stops)

    # store each address group as nested list
    address_array = []
    for i in range(num_groups):
        address_array.append(stop_df['api_address_string'].tolist()[i * max_stops: (i + 1) * max_stops])

    return address_array


def create_matrices(address_array, config_dict):
    """ Sends Google Maps API requests to create distance & duration matrices for each group of addresses;
    assembles group matrices into full matrices.

    Params:


    Returns:
        Distance and duration matrices w/ rows as nested lists.
    """

    api_key = config_dict['dist_matrix_api_key']
    max_elements = 100  # limit 100 elements per API request - https://tinyurl.com/3sywy4ky

    distance_matrix_array = []
    duration_matrix_array = []

    # destination addresses for each group in address array
    for m in range(len(address_array)):
        destination_group = address_array[m]

        # origin addresses for each group in address array
        for n in range(len(address_array)):
            origin_group = address_array[n]

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


def main():
    pass


if __name__ == '__main__':
    main()
