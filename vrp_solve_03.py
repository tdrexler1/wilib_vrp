import argparse
import math
import pickle ##
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# TODO: add capacity constraint
# TODO: add in exchange times at each stop
# TODO: add in break time per route
# TODO: add function to output solutions in array, possibly CSV
# DONE: add command-line inputs (# vehicles, maximum miles, maximum route time)
# DONE: add toggle for time/distance as primary constraint
# TODO: comments & docstrings

# constants
METERS_PER_MILE = 1609.34
SECONDS_PER_HOUR = 3600
SECONDS_PER_MINUTE = 60


def format_problem_data(input_data_dict, n_vehicles):
    """ Sets up the data dict used by Google OR Tools. """

    output_data_dict = {
        'distance_matrix': input_data_dict['distance_matrix'],
        'duration_matrix': input_data_dict['duration_matrix'],
        'num_vehicles': n_vehicles,
        'depot': 0,
        'library_names': [input_data_dict['library_info'][k]['stop_short_name'] for k in
                          input_data_dict['library_info'].keys()]
    }

    return output_data_dict

# TODO: is this function used/necessary?
def get_routes(solution, routing, manager):
    """ Gets routes from solver solution object & stores routes as an array. """

    # entry i, j is the jth location visited by vehicle i along its route
    routes = []
    for route_nbr in range(routing.vehicles()):
        index = routing.Start(route_nbr)
        route = [manager.IndexToNode(index)]
        while not routing.IsEnd(index):
            index = solution.Value(routing.NextVar(index))
            route.append(manager.IndexToNode(index))
        routes.append(route)
    return routes


def print_solution(model_data_dict, idx_manager, routing_mdl, solution, input_args_dict):
    """ Prints VRP solution to console in readable format.

    Parameters:
        model_data_dict: Dict with distance & duration matrices and other problem data.
        idx_manager: OR-Tools routing index manager object.
        routing_mdl: OR-Tools routing model object.
        solution: OR-Tools solution object, assuming the solver found a solution.
        input_args_dict: Dict of user-input arguments.
    """

    # tracking variables for all routes
    total_distance = 0
    total_time = 0

    for vehicle_id in range(model_data_dict['num_vehicles']):

        # tracking variables for each route
        route_distance = 0
        route_time = 0
        route_distance_02 = 0
        route_time_02 = 0
        num_stops = 0

        index = routing_mdl.Start(vehicle_id)
        plan_output = f'Route for vehicle {vehicle_id + 1}:\n\t'

        # iterate over all stops on the route
        while not routing_mdl.IsEnd(index):

            # substitute library names for index numbers
            plan_output += f'{model_data_dict["library_names"][idx_manager.IndexToNode(index)]} -> '

            previous_index = index
            index = solution.Value(routing_mdl.NextVar(index))


            if input_args_dict['constraint'] == 'distance':
                route_distance += routing_mdl.GetArcCostForVehicle(previous_index, index, vehicle_id)
                route_time += model_data_dict['duration_matrix'][idx_manager.IndexToNode(previous_index)][idx_manager.IndexToNode(index)]

            else:
                route_distance += model_data_dict['distance_matrix'][idx_manager.IndexToNode(previous_index)][idx_manager.IndexToNode(index)]
                route_time += routing_mdl.GetArcCostForVehicle(previous_index, index, vehicle_id)

            route_distance_02 += model_data_dict['distance_matrix'][idx_manager.IndexToNode(previous_index)][
                idx_manager.IndexToNode(index)]
            route_time_02 += model_data_dict['duration_matrix'][idx_manager.IndexToNode(previous_index)][
                idx_manager.IndexToNode(index)]

            num_stops += 1

        plan_output += f' {model_data_dict["library_names"][idx_manager.IndexToNode(index)]}\n'
        plan_output += f'Route distance: {route_distance/METERS_PER_MILE:.2f} miles\n'
        plan_output += f'Route distance 02: {route_distance_02 / METERS_PER_MILE:.2f} miles\n'

        route_time += int(input_args_dict['break_time_minutes'] * 60)

        mins, secs = divmod(route_time, 60)
        hours, mins = divmod(mins, 60)
        plan_output += f'Route time: {hours} {"hours" if hours > 1 else "hour"}, ' \
                       f'{mins} {"minutes" if mins > 1 else "minute"}\n'
        mins2, secs2 = divmod(route_time_02, 60)
        hours2, mins2 = divmod(mins2, 60)
        plan_output += f'Route time 02: {hours2} {"hours" if hours2 > 1 else "hour"}, ' \
                       f'{mins2} {"minutes" if mins2 > 1 else "minute"}\n'

        plan_output += f'Number of stops: {num_stops}\n'

        print(plan_output)

        total_distance += route_distance
        total_time += route_time

    print(f'Total distance, all routes: {total_distance/METERS_PER_MILE:.2f} miles')

    total_mins, total_secs = divmod(total_time, 60)
    total_hours, total_mins = divmod(total_mins, 60)
    print(f'Total time, all routes: {total_hours} {"hours" if total_hours > 1 else "hour"}, '
          f'{total_mins} {"minutes" if total_mins > 1 else "minute"}')


def main():

    # parse command line arguments
    parser = argparse.ArgumentParser(description='Solve the vehicle routing problem.',
                                     usage='{distance, duration} num_vehicles max_hours max_miles'
                                           '\n     [-h]',
                                     add_help=False)
    parser.add_argument('constraint', action='store', default='duration', type=str, choices=['distance', 'duration'],
                        help="Select route cost constraint: 'duration' or 'distance'")
    parser.add_argument('num_vehicles', action='store', default=1, type=int, choices=range(1, 10),
                        help='Number of vehicles/routes (1-10)')
    parser.add_argument('max_hours', action='store', default=8, type=float,
                        help='Maximum allowable route time in hours')
    parser.add_argument('max_miles', action='store', default=500, type=float,
                        help='Maximum allowable route distance in miles')
    parser.add_argument('break_time_minutes', action='store', default=0, type=float,
                        help='Total break time per route in minutes')
    args_dict = vars(parser.parse_args())

    # for testing - uses pickled data from dist_matrix_XX.py
    with open('vrp_data_dict.pickle', 'rb') as pick_file:
        pickled_data = pickle.load(pick_file)

    vrp_data_dict = format_problem_data(pickled_data, args_dict['num_vehicles'])

    # create routing index manager
    index_manager = pywrapcp.RoutingIndexManager(
        len(vrp_data_dict['distance_matrix']),
        vrp_data_dict['num_vehicles'],
        vrp_data_dict['depot']
    )

    # create routing model
    routing_model = pywrapcp.RoutingModel(index_manager)

    # distance dimension
    def distance_callback(from_index, to_index):
        """ Returns distance between two nodes. """

        # convert routing variable index to distance matrix NodeIndex
        from_node = index_manager.IndexToNode(from_index)
        to_node = index_manager.IndexToNode(to_index)
        return vrp_data_dict['distance_matrix'][from_node][to_node]

    # register distance_callback
    distance_callback_index = routing_model.RegisterTransitCallback(distance_callback)

    # convert input miles to meters
    max_distance = math.ceil(args_dict['max_miles'] * METERS_PER_MILE)

    # add distance constraint
    routing_model.AddDimension(
        distance_callback_index,
        0,
        max_distance,
        True,
        'Distance'
    )
    distance_dimension = routing_model.GetDimensionOrDie('Distance')

    # time dimension
    def duration_callback(from_index, to_index):
        """ Returns transit time between two nodes. """

        # convert routing variable index to duration matrix NodeIndex
        from_node = index_manager.IndexToNode(from_index)
        to_node = index_manager.IndexToNode(to_index)
        return vrp_data_dict['duration_matrix'][from_node][to_node]

    # register duration_callback
    duration_callback_index = routing_model.RegisterTransitCallback(duration_callback)

    # convert input hours & minutes to seconds
    max_duration = math.ceil(args_dict['max_hours'] * SECONDS_PER_HOUR -
                             args_dict['break_time_minutes'] * SECONDS_PER_MINUTE)
    #print(max_duration)

    # add duration constraint
    routing_model.AddDimension(
        duration_callback_index,
        0,
        max_duration,
        True,
        'Duration'
    )
    duration_dimension = routing_model.GetDimensionOrDie('Duration')

    # choose distance or time as primary constraint
    if args_dict['constraint'] == 'distance':
        routing_model.SetArcCostEvaluatorOfAllVehicles(distance_callback_index)
        distance_dimension.SetGlobalSpanCostCoefficient(100)
    else:
        routing_model.SetArcCostEvaluatorOfAllVehicles(duration_callback_index)
        duration_dimension.SetGlobalSpanCostCoefficient(100)

    # set first solution heuristic
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_MOST_CONSTRAINED_ARC
    search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_parameters.time_limit.seconds = 30
    search_parameters.log_search = False

    # solve the problem
    vrp_solution = routing_model.SolveWithParameters(search_parameters)
    solver_status_code_dict = {
        0: 'ROUTING_NOT_SOLVED - Problem not solved yet',
        1: 'ROUTING_SUCCESS - Problem solved successfully',
        2: 'ROUTING_FAIL - No solution found to the problem',
        3: 'ROUTING_FAIL_TIMEOUT - Time limit reached before finding a solution',
        4: 'ROUTING_INVALID - Model, model parameters, or flags are not valid'
    }
    print(f'Solver status: {solver_status_code_dict[routing_model.status()]}\n')

    if vrp_solution:
        print_solution(vrp_data_dict, index_manager, routing_model, vrp_solution, args_dict)
    else:
        print('No solution found.')

# here are some changes
if __name__ == '__main__':
    main()
