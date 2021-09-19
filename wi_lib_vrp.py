#! python3

import argparse
import sys
import pandas as pd
import os
import yaml
import pickle

import wi_lib_vrp_matrix_build as dist
import wi_lib_vrp_route_viz as mapper
from wi_lib_vrp_VrpModelObj import VrpModelObj


def parse_args():
    """
    Sets up parser and help menu for command-line arguments.

    :return: A dict with argument, value entries.
    :rtype: dict
    """

    # instantiate parser object with description & help menu
    # noinspection PyTypeChecker
    # help menu formatting: https://stackoverflow.com/a/5464440
    # help menu formatting, width: https://stackoverflow.com/a/32891625
    parser_obj = argparse.ArgumentParser(
        prog='tool',
        description='Set up and solve a Vehicle Routing Problem for a proposed WI library delivery region.',
        usage='input_file {ideal, starter} region_number {distance, duration} '
              'num_vehicles max_hours max_miles veh_cap break_time_minutes'
              '\n       {automatic, path_cheapest_arc, savings, sweep, christofides, parallel_cheapest_insertion, '
              '\n        local_cheapest_insertion, global_cheapest_arc, local_cheapest_arc, first_unbound_min_value}'
              '\n       {automatic, greedy_descent, guided_local_search, simulated_annealing, tabu_search}'
              '\n       [-v/--vehicle_increment] [-b/--build_matrices]'
              '\n       [-d/--display] [-m/--map] [-s/--screenshot] [-t/--text_file]'
              '\n       [-h/--help]',
        add_help=False,
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=27, width=200)
    )

    # argument group for VRP setup options
    setup_group = parser_obj.add_argument_group(title='Problem setup arguments')
    setup_group.add_argument('input_file', action='store', type=str,
                             help="Name of file containing input library data ('csv' or 'xlsx' format).")
    setup_group.add_argument('model', choices=['ideal', 'starter'], default='ideal',
                             help='PLSR Delivery Workgroup proposed model version.')
    setup_group.add_argument('region_number', type=int, choices=range(1, 8) if 'ideal' in sys.argv else range(1, 9),
                             help='Model region number (1-7 for ideal model, 1-8 for starter model).')
    setup_group.add_argument('-b', '--build_matrices', action='store_true',
                             help='Build distance and duration matrices using external API.')

    # argument group for VRP parameters
    param_group = parser_obj.add_argument_group(title='VRP parameter arguments')
    param_group.add_argument('constraint', action='store', default='duration', type=str,
                             choices=['distance', 'duration'],
                             help="Select whether routes should be balanced by 'distance' or 'duration'.")
    param_group.add_argument('num_vehicles', action='store', default=1, type=int, choices=range(1, 16),
                             help='Number of vehicles/routes (1-15).')
    param_group.add_argument('max_hours', action='store', default=8, type=float,
                             help='Maximum allowable route time in hours.')
    param_group.add_argument('max_miles', action='store', default=500, type=float,
                             help='Maximum allowable route distance in miles.')
    param_group.add_argument('veh_cap', action='store', default=50, type=int,
                             help='Vehicle capacity (all vehicles)')
    param_group.add_argument('break_time_minutes', action='store', default=0, type=float,
                             help='Total break time per route in minutes.')

    # argument group for VRP solution search strategies
    strategy_group = parser_obj.add_argument_group(title='Search strategy arguments.')
    strategy_group.add_argument('first_solution_strategy',
                                choices=['automatic', 'path_cheapest_arc', 'savings', 'sweep', 'christofides',
                                         'parallel_cheapest_insertion', 'local_cheapest_insertion',
                                         'global_cheapest_arc', 'local_cheapest_arc', 'first_unbound_min_value'],
                                action='store', default='automatic', type=str,
                                help='Method the solver uses to find an initial solution.')
    strategy_group.add_argument('local_search_metaheuristic', choices=['automatic', 'greedy_descent',
                                                                       'guided_local_search', 'simulated_annealing',
                                                                       'tabu_search'],
                                action='store', default='automatic', type=str,
                                help='Local search strategy/metaheuristic.')
    strategy_group.add_argument('-v', '--vehicle_increment', action='store_true', help='Add one vehicle to fleet and '
                                                                                       'resolve VRP until '
                                                                                       'feasible solution is found.')

    # argument group for VRP output options
    output_options_group = parser_obj.add_argument_group(title='Optional output arguments.')
    output_options_group.add_argument('-d', '--display', action='store_true', help='Display solution on screen.')
    output_options_group.add_argument('-m', '--map', action='store_true', help='Map optimal route plan '
                                                                               '(opens in default browser window).')
    output_options_group.add_argument('-s', '--screenshot', action='store_true',
                                      help='Create a PNG screenshot of route plan map.')
    output_options_group.add_argument('-t', '--text_file', action='store_true', help='Export solution to text file.')

    output_options_group.add_argument('-h', '--help', action='help', help='Show this message and exit.')

    # return argument values as dict
    return vars(parser_obj.parse_args())


def main():
    """
    Organizes code to run VRP modeling program from command line.
    """

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

    # retrieve API keys for Google Maps & openrouteservice from YAML file
    try:
        with open(os.path.expanduser('~/wi_lib_vrp_api_keys.yml'), 'r') as api_keys:
            key_data = yaml.full_load(api_keys)
    except OSError as e:
        print(e)

    # merge dict of command-line args, values with dicts of api keys
    conf_dict = {**args_dict, **key_data['google_maps'], **key_data['open_route_service']}

    # set path for output directory
    vrp_output_path = '.\\vrp_output\\'

    # initialize pandas dataframe w/ data for all library locations in region
    region_data = dist.prep_input_data(stop_data, conf_dict)

    # optional command to build distance & duration matrices from scratch using openrouteservice
    if conf_dict['build_matrices']:

        # retrieve library geolocations formatted as nested arrays
        api_geolocs_array = dist.create_api_geoloc_lists(region_data)

        print('Building distance and duration matrices...', end='')

        # save distance & duration matrices
        distance_matrix, duration_matrix = dist.create_matrices(api_geolocs_array, conf_dict)

    # retrieve previously-created distance & duration matrices from pickle files
    else:
        print('Retrieving distance and duration matrices...', end='')

        matrix_pickle_name = \
            '.\\vrp_matrix_data\\' + \
            conf_dict['model'] + \
            str(conf_dict['region_number']) + \
            '_matrices.pickle'

        with open(matrix_pickle_name, 'rb') as pick_file:
            pickled_matrices = pickle.load(pick_file)

        # save distance & duration matrices
        distance_matrix = pickled_matrices['distance_matrix']
        duration_matrix = pickled_matrices['duration_matrix']

    # check formatting of distance & duration matrices
    dist.check_matrix_results(distance_matrix)
    dist.check_matrix_results(duration_matrix)
    print('matrices ready.')

    # create new VrpModelObj
    vrp_model = VrpModelObj(distance_matrix, duration_matrix, region_data, conf_dict)

    # get model id string for use in output file names
    vrp_model_id = vrp_model.get_model_id()

    # call to solve_vrp method of VrpModelObj
    vrp_solution = vrp_model.solve_vrp()

    # [START VRP solution output]

    # output to console or text file
    if conf_dict['display'] or conf_dict['text_file']:

        # retrieve route plan from VrpModelObj
        route_plan = vrp_model.get_vrp_route_plan()

        # output to console
        if conf_dict['display']:
            print(route_plan)

        # output to text file
        if conf_dict['text_file']:

            # construct output file path & create directory if necessary
            text_file_path = vrp_output_path + 'solution_files\\'

            if not os.path.isdir(text_file_path):
                os.makedirs(text_file_path)

            results_text_file = text_file_path + \
                conf_dict['model'] + \
                str(conf_dict['region_number']) + \
                '_' + str(conf_dict['veh_cap']) + \
                '_results.txt'

            # write output text file
            with open(results_text_file, 'a') as outfile:
                outfile.write(route_plan)

    # output to map w/ or w/o screenshot iff feasible VRP solution
    if (conf_dict['map'] or conf_dict['screenshot']) and vrp_solution:

        # construct output file path & create directory if necessary
        map_file_path = vrp_output_path + 'map_files\\'

        if not os.path.isdir(map_file_path):
            os.makedirs(map_file_path)

        # retrieve route stop sequences of optimal routes from VrpModelObject
        optimal_routes = vrp_model.get_vrp_route_array()

        # generate HTML file of Google Map
        route_map = \
            mapper.map_vrp_routes(optimal_routes, region_data, conf_dict['general_maps_api_key'], vrp_model_id,
                                  map_file_path)
        route_map_filepath = os.path.abspath(route_map)

        # display map file in browser or new tab
        if conf_dict['map']:
            mapper.display_map(route_map_filepath)

        # output screenshot of Google Map to PNG file
        if conf_dict['screenshot']:

            # construct output file path & create directory if necessary
            screenshot_file_path = vrp_output_path + 'screenshots\\'

            if not os.path.isdir(screenshot_file_path):
                os.makedirs(screenshot_file_path)

            # generate PNG file
            mapper.screenshot_map(route_map_filepath, screenshot_file_path)

    # [END VRP solution output]


if __name__ == '__main__':
    main()
