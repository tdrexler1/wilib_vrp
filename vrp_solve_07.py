import math
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# DONE: add capacity constraint
# DONE: add in exchange times at each stop
# DONE: add in break time per route
# DONE: add function to output solutions in array, possibly CSV
# DONE: add command-line inputs (# vehicles, maximum miles, maximum route time)
# DONE: add toggle for time/distance as primary constraint
# TODO: figure out how to force certain stops to the same routes
# TODO: comments & docstrings

# constants
METERS_PER_MILE = 1609.34
SECONDS_PER_HOUR = 3600
SECONDS_PER_MINUTE = 60


def format_ORtools_data(dist_mtrx, dur_mtrx, stop_info, conf_dict):
    """ Sets up the data dict used by Google OR Tools. """

    problem_data_dict = {
        'distance_matrix': dist_mtrx,
        'duration_matrix': dur_mtrx,
        'num_vehicles': conf_dict['num_vehicles'],
        'depot': 0,
        'library_names': stop_info['stop_short_name'].tolist(),
        'library_ids': stop_info.index.tolist(),
        'service_time': stop_info['service_time_mins'].astype(float).multiply(SECONDS_PER_MINUTE).astype(int).tolist(),
        'demands': stop_info['avg_pickup'].astype(int).tolist(),
        'vehicle_capacities': [conf_dict['veh_cap']] * conf_dict['num_vehicles']
    }

    # exchange time at each stop
    problem_data_dict['service_time'][problem_data_dict['depot']] = 0
    assert len(problem_data_dict['duration_matrix']) == len(problem_data_dict['service_time'])

    return problem_data_dict


def vrp_setup(vrp_data_dict, config_dict):
    # 1.To "force" assignment of a node to a specific vehicle you can use:
    # routing.VehicleVar(locatin_index).SetValue(vehicle_id)
    # https://gist.github.com/Mizux/f200bd2b0fc6ad622922b0ca9e868823

    # create routing index manager
    index_manager = pywrapcp.RoutingIndexManager(
        len(vrp_data_dict['distance_matrix']),
        vrp_data_dict['num_vehicles'],
        vrp_data_dict['depot']
    )

    # create routing model
    routing_model = pywrapcp.RoutingModel(index_manager)

    # [START distance dimension]
    def distance_callback(from_index, to_index):
        """ Returns distance between two nodes. """

        # convert routing variable index to distance matrix NodeIndex
        from_node = index_manager.IndexToNode(from_index)
        to_node = index_manager.IndexToNode(to_index)
        return vrp_data_dict['distance_matrix'][from_node][to_node]

    # register distance_callback
    distance_callback_index = routing_model.RegisterTransitCallback(distance_callback)

    # convert input miles to meters
    max_distance = math.ceil(config_dict['max_miles'] * METERS_PER_MILE)

    # add distance constraint
    routing_model.AddDimension(
        distance_callback_index,
        0,
        max_distance,
        True,
        'Distance'
    )
    distance_dimension = routing_model.GetDimensionOrDie('Distance')

    # [END distance dimension]

    # [START time dimension]
    def duration_callback(from_index, to_index):
        """ Returns transit time between two nodes. """

        # convert routing variable index to duration matrix NodeIndex
        from_node = index_manager.IndexToNode(from_index)
        to_node = index_manager.IndexToNode(to_index)
        return vrp_data_dict['duration_matrix'][from_node][to_node] + vrp_data_dict['service_time'][from_node]

    # register duration_callback
    duration_callback_index = routing_model.RegisterTransitCallback(duration_callback)

    # convert input hours & minutes to seconds
    # max_duration = math.ceil(args_dict['max_hours'] * SECONDS_PER_HOUR -
    #                          args_dict['break_time_minutes'] * SECONDS_PER_MINUTE)
    max_duration = math.ceil(config_dict['max_hours'] * SECONDS_PER_HOUR)
    break_duration = math.ceil(config_dict['break_time_minutes'] * SECONDS_PER_MINUTE)

    # add duration constraint
    routing_model.AddDimension(
        duration_callback_index,
        break_duration,
        max_duration,
        True,
        'Duration'
    )
    duration_dimension = routing_model.GetDimensionOrDie('Duration')
    # [END time dimension]

    # [START capacity constraint]
    def demand_callback(from_index):
        """Returns the demand of the node."""
        # Convert from routing variable Index to demands NodeIndex.
        from_node = index_manager.IndexToNode(from_index)
        return vrp_data_dict['demands'][from_node]

    demand_callback_index = routing_model.RegisterUnaryTransitCallback(demand_callback)

    routing_model.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,
        vrp_data_dict['vehicle_capacities'],
        True,
        'Capacity'
    )
    capacity_dimension = routing_model.GetDimensionOrDie('Capacity')
    # [END capacity constraint]

    # [START break_constraint]
    # https://github.com/google/or-tools/blob/master/ortools/constraint_solver/samples/vrp_breaks.py
    # warning: Need a pre-travel array using the solver's index order.
    node_visit_transit = [0] * routing_model.Size()
    for index in range(routing_model.Size()):
        node = index_manager.IndexToNode(index)
        node_visit_transit[index] = vrp_data_dict['service_time'][node]

    break_intervals = {}
    for v in range(vrp_data_dict['num_vehicles']):
        break_intervals[v] = [
            routing_model.solver().FixedDurationIntervalVar(
                14400,  # minimum break start time (4 hours)
                21600,  # maximum break start time (6 hours)
                break_duration,
                False,  # optional: no
                f'Break for vehicle {v + 1}')
        ]
        duration_dimension.SetBreakIntervalsOfVehicle(
            break_intervals[v],  # breaks
            v,  # vehicle index
            node_visit_transit)
    # [END break_constraint]

    # choose distance or time as primary constraint
    if config_dict['constraint'] == 'distance':
        routing_model.SetArcCostEvaluatorOfAllVehicles(distance_callback_index)
        distance_dimension.SetGlobalSpanCostCoefficient(100)
    elif config_dict['constraint'] == 'duration':
        routing_model.SetArcCostEvaluatorOfAllVehicles(duration_callback_index)
        duration_dimension.SetGlobalSpanCostCoefficient(100)

    return routing_model, index_manager


def solve_vrp(vrp_model, config_dict):
    search_param_args = \
        {
            'first_solution_strategy':
                {
                    'automatic': routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC,
                    'path_cheapest_arc': routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC,
                    'savings': routing_enums_pb2.FirstSolutionStrategy.SAVINGS,
                    'sweep': routing_enums_pb2.FirstSolutionStrategy.SWEEP,
                    'christofides': routing_enums_pb2.FirstSolutionStrategy.CHRISTOFIDES,
                    'parallel_cheapest_insertion': routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION,
                    'local_cheapest_insertion': routing_enums_pb2.FirstSolutionStrategy.LOCAL_CHEAPEST_INSERTION,
                    'global_cheapest_arc': routing_enums_pb2.FirstSolutionStrategy.GLOBAL_CHEAPEST_ARC,
                    'local_cheapest_arc': routing_enums_pb2.FirstSolutionStrategy.LOCAL_CHEAPEST_ARC,
                    'first_unbound_min_value': routing_enums_pb2.FirstSolutionStrategy.FIRST_UNBOUND_MIN_VALUE
                },
            'local_search_metaheuristic':
                {
                    'automatic': routing_enums_pb2.LocalSearchMetaheuristic.AUTOMATIC,
                    'greedy_descent': routing_enums_pb2.LocalSearchMetaheuristic.GREEDY_DESCENT,
                    'guided_local_search': routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH,
                    'simulated_annealing': routing_enums_pb2.LocalSearchMetaheuristic.SIMULATED_ANNEALING,
                    'tabu_search': routing_enums_pb2.LocalSearchMetaheuristic.TABU_SEARCH
                }
        }

    #
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()

    search_parameters.first_solution_strategy = \
        search_param_args['first_solution_strategy'][config_dict['first_solution_strategy']]
    search_parameters.local_search_metaheuristic = \
        search_param_args['local_search_metaheuristic'][config_dict['local_search_metaheuristic']]

    search_parameters.time_limit.seconds = 30
    search_parameters.log_search = False

    # solve the problem
    vrp_solution = vrp_model.SolveWithParameters(search_parameters)
    solver_status_code_dict = {
        0: 'ROUTING_NOT_SOLVED - Problem not solved yet',
        1: 'ROUTING_SUCCESS - Problem solved successfully',
        2: 'ROUTING_FAIL - No solution found to the problem',
        3: 'ROUTING_FAIL_TIMEOUT - Time limit reached before finding a solution',
        4: 'ROUTING_INVALID - Model, model parameters, or flags are not valid'
    }
    print(f'Solver status: {solver_status_code_dict[vrp_model.status()]}\n')

    return vrp_solution



def format_time_display(time_in_seconds):

    mins, secs = divmod(time_in_seconds, 60)
    hrs, mins = divmod(mins, 60)

    time_display_string = f'{hrs} {"hours" if hrs > 1 else "hour"}, {mins} {"minutes" if mins > 1 else "minute"}'

    return time_display_string


def print_solution(model_data_dict, idx_manager, routing_mdl, solution):
    """ Prints VRP solution to console.

    Parameters:
        model_data_dict: Dict with distance & duration matrices and other problem data.
        idx_manager: OR-Tools routing index manager object.
        routing_mdl: OR-Tools routing model object.
        solution: OR-Tools solution object.
    """

    # tracking variables for all routes
    total_distance = 0
    total_time = 0

    distance_dimension = routing_mdl.GetDimensionOrDie('Distance')
    time_dimension = routing_mdl.GetDimensionOrDie('Duration')
    capacity_dimension = routing_mdl.GetDimensionOrDie('Capacity')
    break_intervals = solution.IntervalVarContainer()

    for vehicle_id in range(model_data_dict['num_vehicles']):

        num_stops = 0


        index = routing_mdl.Start(vehicle_id)
        plan_output = f'Route for vehicle {vehicle_id + 1}:\n\t'

        # iterate over all stops on the route
        while not routing_mdl.IsEnd(index):

            # substitute library names for index numbers
            plan_output += f'{model_data_dict["library_names"][idx_manager.IndexToNode(index)]} -> '

            num_stops += 1

            index = solution.Value(routing_mdl.NextVar(index))

        route_distance = solution.Value(distance_dimension.CumulVar(index))
        route_time = solution.Value(time_dimension.CumulVar(index))
        route_load = solution.Value(capacity_dimension.CumulVar(index))

        plan_output += f' {model_data_dict["library_names"][idx_manager.IndexToNode(index)]}\n'
        plan_output += f'\tRoute distance: {route_distance/METERS_PER_MILE:.2f} miles\n'
        plan_output += f'\tRoute time: {format_time_display(route_time)}\n'
        plan_output += f'\tRoute load: {route_load} containers\n'
        plan_output += f'\tNumber of stops: {num_stops - 1}\n'

        brk = break_intervals.Element(vehicle_id)
        if brk.PerformedValue():
            plan_output += f'\tBreak: start time = {format_time_display(brk.StartValue())}; ' \
                           f'end time = {format_time_display(brk.StartValue() + brk.DurationValue())}\n'
        else:
            plan_output += f'\tNo break.\n'

        print(plan_output)

        total_distance += route_distance
        total_time += route_time

    print(f'Total distance, all routes: {total_distance/METERS_PER_MILE:.2f} miles')

    total_mins, total_secs = divmod(total_time, 60)
    total_hours, total_mins = divmod(total_mins, 60)
    print(f'Total time, all routes: {total_hours} {"hours" if total_hours > 1 else "hour"}, '
          f'{total_mins} {"minutes" if total_mins > 1 else "minute"}')


def get_routes(model_data_dict, idx_manager, routing_mdl, solution):
    """Get vehicle routes from a solution and store them in an array."""
    # Get vehicle routes and store them in a two dimensional array whose
    # i,j entry is the jth location visited by vehicle i along its route.
    routes = []
    for route_nbr in range(routing_mdl.vehicles()):
        index = routing_mdl.Start(route_nbr)
        route = [model_data_dict['library_ids'][idx_manager.IndexToNode(index)]]
        while not routing_mdl.IsEnd(index):
            index = solution.Value(routing_mdl.NextVar(index))
            route.append(model_data_dict['library_ids'][idx_manager.IndexToNode(index)])
        routes.append(route)
    return routes