import geocode_addresses_03
import dist_matrix_04
import vrp_solve_06
#import vrp_route_map_01

import argparse
import sys

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
    for k, v in args_dict.items():
        print(f'key: {k}, value: {v}')

    #dist_matrix_04.main()

if __name__ == '__main__':
    main()
