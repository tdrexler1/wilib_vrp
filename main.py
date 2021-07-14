import geocode_addresses_03 as geo
import dist_matrix_05 as dist
import vrp_solve_06 as solve
#import vrp_route_map_01

import argparse
import sys
import pandas as pd
import os
import yaml

# following two lines for testing only
pd.options.display.width = 0
pd.options.display.max_rows = 1000


def main():
    # noinspection PyTypeChecker
    parser_obj = argparse.ArgumentParser(
        prog='tool',
        description='Set up and solve a Vehicle Routing Problem for a proposed WI library delivery region.',
        usage='input_file {ideal, starter} region_number {distance, duration} num_vehicles max_hours max_miles'
              '\n       [-g/--geocode] [-r/--regions] [-o/--output] [--out_format {csv, xlsx}] [-m/--map] [-h/--help]',
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

    param_group = parser_obj.add_argument_group(title='VRP parameter arguments')
    param_group.add_argument('constraint', action='store', default='duration', type=str,
                             choices=['distance', 'duration'],
                             help="Select whether routes should be balanced by 'distance' or 'duration'.")
    param_group.add_argument('num_vehicles', action='store', default=1, type=int, choices=range(1, 11),
                             help='Number of vehicles/routes (1-10).')
    param_group.add_argument('max_hours', action='store', default=8, type=float,
                             help='Maximum allowable route time in hours.')
    param_group.add_argument('max_miles', action='store', default=500, type=float,
                             help='Maximum allowable route distance in miles.')
    param_group.add_argument('break_time_minutes', action='store', default=0, type=float,
                             help='Total break time per route in minutes.')

    options_group = parser_obj.add_argument_group(title='Optional arguments')

    options_group.add_argument('-g', '--geocode', action='store_true', help='Flag to add location geocode data.')
    options_group.add_argument('-r', '--regions', action='store_true', help='Flag to add proposed region data.')
    options_group.add_argument('-o', '--output', action='store_true', help='Flag to export updated data to a file.')
    options_group.add_argument('--out_format', required='-o' in sys.argv or '--output' in sys.argv,
                        choices=['csv', 'xlsx'], default='csv', type=str,
                        help="Output file format ('csv' or 'xlsx').")
    options_group.add_argument('-m', '--map', action='store_true', help='Flag to map optimal route plan '
                                                                        '(opens in default browser window).')
    options_group.add_argument('-h', '--help', action='help', help='Show this message and exit.')

    args_dict = vars(parser_obj.parse_args())

    stop_data = pd.read_excel(
        args_dict['input_file'],
        header=0,
        index_col='LIBID',
        dtype=str,
        engine='openpyxl')

    # Google Maps API keys
    try:
        with open(os.path.expanduser('~/google_maps_api_key.yml'), 'r') as api_keys:
            key_data = yaml.full_load(api_keys)
    except OSError as e:
        print(e)
    api_dict = key_data['google_maps']

    conf_dict = {**args_dict, **api_dict}

    region_data = dist.prep_input_data(stop_data, conf_dict)

    api_address_array = dist.create_api_address_lists(region_data)

    # create distance & duration matrices w/ Google Maps API
    distance_matrix, duration_matrix = dist.create_matrices(api_address_array, conf_dict)

    # check results
    dist.check_matrix_results(distance_matrix)
    dist.check_matrix_results(duration_matrix)

    #print(distance_matrix)
    #print(api_address_array)

if __name__ == '__main__':
    main()
