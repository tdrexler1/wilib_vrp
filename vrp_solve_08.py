import math
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# TODO: figure out how to force certain stops to the same routes


class VrpModelObj(object):
    """


    """

    # constants
    _METERS_PER_MILE = 1609.34
    _SECONDS_PER_HOUR = 3600
    _SECONDS_PER_MINUTE = 60

    _search_param_dict = \
        {
            'first_solution_strategy':
                {
                    'path_cheapest_arc':
                        {'model_id_code': '01',
                         'solver_param': routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC},
                    'savings':
                        {'model_id_code': '02',
                         'solver_param': routing_enums_pb2.FirstSolutionStrategy.SAVINGS},
                    'sweep':
                        {'model_id_code': '03',
                         'solver_param': routing_enums_pb2.FirstSolutionStrategy.SWEEP},
                    'christofides':
                        {'model_id_code': '04',
                         'solver_param': routing_enums_pb2.FirstSolutionStrategy.CHRISTOFIDES},
                    'parallel_cheapest_insertion':
                        {'model_id_code': '05',
                         'solver_param': routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION},
                    'local_cheapest_insertion':
                        {'model_id_code': '06',
                         'solver_param': routing_enums_pb2.FirstSolutionStrategy.LOCAL_CHEAPEST_INSERTION},
                    'global_cheapest_arc':
                        {'model_id_code': '07',
                         'solver_param': routing_enums_pb2.FirstSolutionStrategy.GLOBAL_CHEAPEST_ARC},
                    'local_cheapest_arc':
                        {'model_id_code': '08',
                         'solver_param': routing_enums_pb2.FirstSolutionStrategy.LOCAL_CHEAPEST_ARC},
                    'first_unbound_min_value':
                        {'model_id_code': '09',
                         'solver_param': routing_enums_pb2.FirstSolutionStrategy.FIRST_UNBOUND_MIN_VALUE},
                    'automatic':
                        {'model_id_code': '10',
                         'solver_param': routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC}
                },
            'local_search_metaheuristic':
                {
                    'greedy_descent':
                        {'model_id_code': '01',
                         'solver_param': routing_enums_pb2.LocalSearchMetaheuristic.GREEDY_DESCENT},
                    'guided_local_search':
                        {'model_id_code': '02',
                         'solver_param': routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH},
                    'simulated_annealing':
                        {'model_id_code': '03',
                         'solver_param': routing_enums_pb2.LocalSearchMetaheuristic.SIMULATED_ANNEALING},
                    'tabu_search':
                        {'model_id_code': '04',
                         'solver_param': routing_enums_pb2.LocalSearchMetaheuristic.TABU_SEARCH},
                    'automatic':
                        {'model_id_code': '05',
                         'solver_param': routing_enums_pb2.LocalSearchMetaheuristic.AUTOMATIC}
                }
        }

    def __init__(self, vrp_distance_matrix, vrp_duration_matrix, region_df, config_dict):
        self._vrp_distance_matrix = vrp_distance_matrix
        self._vrp_duration_matrix = vrp_duration_matrix
        self._vrp_num_vehicles = config_dict['num_vehicles']
        self._region_df = region_df
        self._config_dict = config_dict

    def _format_vrp_model_id(self):

        id_string = 'idl' if self._config_dict['model'] == 'ideal' else 'str'
        id_string += str(self._config_dict['region_number']) if self._config_dict['region_number'] < 10 else str(
            self._config_dict['region_number'])
        id_string += '_'
        id_string += ('0' + str(int(self._config_dict['max_hours']))) if self._config_dict['max_hours'] < 10 \
            else str(int(self._config_dict['max_hours']))
        id_string += \
            self._search_param_dict['first_solution_strategy']\
                [self._config_dict['first_solution_strategy']]['model_id_code']
        id_string += \
            self._search_param_dict['local_search_metaheuristic']\
                [self._config_dict['local_search_metaheuristic']]['model_id_code']
        id_string += ('0' + str(int(self._config_dict['veh_cap']))) if self._config_dict['veh_cap'] < 100 else \
            str(int(self._config_dict['veh_cap']))

        self._vrp_model_id = id_string

    def get_model_id(self):
        self._format_vrp_model_id()
        return self._vrp_model_id

    def __vrp_format_input_data(self):

        self._vrp_input_data_dict = {
            'distance_matrix': self._vrp_distance_matrix,
            'duration_matrix': self._vrp_duration_matrix,
            'num_vehicles': self._vrp_num_vehicles,
            'depot': 0,
            'library_names': self._region_df['stop_short_name'].tolist(),
            'library_ids': self._region_df.index.tolist(),
            'service_time': self._region_df['service_time_mins'].astype(float).multiply(self._SECONDS_PER_MINUTE).astype(
                int).tolist(),
            'demands': self._region_df['avg_pickup'].astype(int).tolist(),
            'vehicle_capacities': [self._config_dict['veh_cap']] * self._vrp_num_vehicles
        }

        # exchange time at each stop
        self._vrp_input_data_dict['service_time'][self._vrp_input_data_dict['depot']] = 0
        assert len(self._vrp_input_data_dict['duration_matrix']) == len(self._vrp_input_data_dict['service_time'])

    def __vrp_initialize(self):
        # 1.To "force" assignment of a node to a specific vehicle you can use:
        # routing.VehicleVar(location_index).SetValue(vehicle_id)
        # https://gist.github.com/Mizux/f200bd2b0fc6ad622922b0ca9e868823

        # create routing index manager
        vrp_index_manager = pywrapcp.RoutingIndexManager(
            len(self._vrp_input_data_dict['distance_matrix']),
            self._vrp_input_data_dict['num_vehicles'],
            self._vrp_input_data_dict['depot']
        )

        # create routing model
        vrp_routing_model = pywrapcp.RoutingModel(vrp_index_manager)
        self._format_vrp_model_id()

        # [START distance dimension]
        def distance_callback(from_index, to_index):
            """ Returns distance between two nodes. """

            # convert routing variable index to distance matrix NodeIndex
            from_node = vrp_index_manager.IndexToNode(from_index)
            to_node = vrp_index_manager.IndexToNode(to_index)
            return math.ceil(self._vrp_input_data_dict['distance_matrix'][from_node][to_node])

        # register distance_callback
        distance_callback_index = vrp_routing_model.RegisterTransitCallback(distance_callback)

        # convert input miles to meters
        max_distance = math.ceil(self._config_dict['max_miles'] * self._METERS_PER_MILE)

        # add distance constraint
        vrp_routing_model.AddDimension(
            distance_callback_index,
            0,
            max_distance,
            True,
            'Distance'
        )
        distance_dimension = vrp_routing_model.GetDimensionOrDie('Distance')

        # [END distance dimension]

        # [START time dimension]
        def duration_callback(from_index, to_index):
            """ Returns transit time between two nodes. """

            # convert routing variable index to duration matrix NodeIndex
            from_node = vrp_index_manager.IndexToNode(from_index)
            to_node = vrp_index_manager.IndexToNode(to_index)
            return math.ceil(self._vrp_input_data_dict['duration_matrix'][from_node][to_node] + \
                   self._vrp_input_data_dict['service_time'][from_node])

        # register duration_callback
        duration_callback_index = vrp_routing_model.RegisterTransitCallback(duration_callback)

        # convert input hours & minutes to seconds
        max_duration = math.ceil(self._config_dict['max_hours'] * self._SECONDS_PER_HOUR)
        break_duration = math.ceil(self._config_dict['break_time_minutes'] * self._SECONDS_PER_MINUTE)

        # add duration constraint
        vrp_routing_model.AddDimension(
            duration_callback_index,
            break_duration,
            max_duration,
            True,
            'Duration'
        )
        duration_dimension = vrp_routing_model.GetDimensionOrDie('Duration')

        # [END time dimension]

        # [START capacity constraint]
        def demand_callback(from_index):
            """Returns the demand of the node."""
            # Convert from routing variable Index to demands NodeIndex.
            from_node = vrp_index_manager.IndexToNode(from_index)
            return math.ceil(self._vrp_input_data_dict['demands'][from_node])

        demand_callback_index = vrp_routing_model.RegisterUnaryTransitCallback(demand_callback)

        vrp_routing_model.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,
            self._vrp_input_data_dict['vehicle_capacities'],
            True,
            'Capacity'
        )
        capacity_dimension = vrp_routing_model.GetDimensionOrDie('Capacity')
        # [END capacity constraint]

        # [START break_constraint]
        # https://github.com/google/or-tools/blob/master/ortools/constraint_solver/samples/vrp_breaks.py
        # warning: Need a pre-travel array using the solver's index order.
        node_visit_transit = [0] * vrp_routing_model.Size()
        for index in range(vrp_routing_model.Size()):
            node = vrp_index_manager.IndexToNode(index)
            node_visit_transit[index] = self._vrp_input_data_dict['service_time'][node]

        break_intervals = {}
        for v in range(self._vrp_input_data_dict['num_vehicles']):
            break_intervals[v] = [
                vrp_routing_model.solver().FixedDurationIntervalVar(
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
        if self._config_dict['constraint'] == 'distance':
            vrp_routing_model.SetArcCostEvaluatorOfAllVehicles(distance_callback_index)
            distance_dimension.SetGlobalSpanCostCoefficient(100)
        elif self._config_dict['constraint'] == 'duration':
            vrp_routing_model.SetArcCostEvaluatorOfAllVehicles(duration_callback_index)
            duration_dimension.SetGlobalSpanCostCoefficient(100)

        self._vrp_index_manager = vrp_index_manager
        self._vrp_routing_model = vrp_routing_model

    def __vrp_solve(self):

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()

        search_parameters.first_solution_strategy = \
            self._search_param_dict['first_solution_strategy']\
            [self._config_dict['first_solution_strategy']]['solver_param']
        search_parameters.local_search_metaheuristic = \
            self._search_param_dict['local_search_metaheuristic']\
            [self._config_dict['local_search_metaheuristic']]['solver_param']

        search_parameters.time_limit.seconds = 15
        search_parameters.log_search = False

        # solve the problem
        self._vrp_solution = self._vrp_routing_model.SolveWithParameters(search_parameters)
        solver_status_code_dict = {
            0: 'ROUTING_NOT_SOLVED - Problem not solved yet',
            1: 'ROUTING_SUCCESS - Problem solved successfully',
            2: 'ROUTING_FAIL - No solution found to the problem',
            3: 'ROUTING_FAIL_TIMEOUT - Time limit reached before finding a solution',
            4: 'ROUTING_INVALID - Model, model parameters, or flags are not valid'
        }
        print(f'Solver status: {solver_status_code_dict[self._vrp_routing_model.status()]}' +
              (f'\n' if self._vrp_routing_model.status() == 1 else f''))

    @staticmethod
    def _format_time_display(time_in_seconds):

        mins, secs = divmod(time_in_seconds, 60)
        hrs, mins = divmod(mins, 60)

        time_display_string = f'{hrs} {"hours" if hrs > 1 else "hour"}, {mins} {"minutes" if mins > 1 else "minute"}'

        return time_display_string

    def __vrp_format_solution(self):

        # tracking variables for all routes
        total_distance = 0
        total_time = 0
        vrp_route_plan = f"Model ID: {self._vrp_model_id}\n" \
                         f"{self._config_dict['model'].capitalize()} proposal, " \
                         f"region {self._config_dict['region_number']}\n\n" \
                         f"Solution strategies:\n" \
                         f"\tFirst solution strategy: {self._config_dict['first_solution_strategy']}\n" \
                         f"\tLocal search metaheuristic: {self._config_dict['local_search_metaheuristic']}\n\n" \
                         f"Model parameters:\n" \
                         f"\tMaximum hours per route: {self._config_dict['max_hours']}\n" \
                         f"\tMaximum distance per route: {self._config_dict['max_miles']} miles\n" \
                         f"\tVehicle capacity: {self._config_dict['veh_cap']}\n" \
                         f"\tDriver break time: {self._config_dict['break_time_minutes']} minutes\n" \
                         f"\tNumber of vehicles/routes: {self._vrp_num_vehicles}\n\n"

        distance_dimension = self._vrp_routing_model.GetDimensionOrDie('Distance')
        time_dimension = self._vrp_routing_model.GetDimensionOrDie('Duration')
        capacity_dimension = self._vrp_routing_model.GetDimensionOrDie('Capacity')
        break_intervals = self._vrp_solution.IntervalVarContainer()

        for vehicle_id in range(self._vrp_num_vehicles):

            num_stops = 0

            index = self._vrp_routing_model.Start(vehicle_id)
            vrp_route_plan += f'Route for vehicle {vehicle_id + 1}:\n\t'

            # iterate over all stops on the route
            while not self._vrp_routing_model.IsEnd(index):
                # substitute library names for index numbers
                vrp_route_plan += \
                    f'{self._vrp_input_data_dict["library_names"][self._vrp_index_manager.IndexToNode(index)]} -> '

                num_stops += 1

                index = self._vrp_solution.Value(self._vrp_routing_model.NextVar(index))

            route_distance = self._vrp_solution.Value(distance_dimension.CumulVar(index))
            route_time = self._vrp_solution.Value(time_dimension.CumulVar(index))
            route_load = self._vrp_solution.Value(capacity_dimension.CumulVar(index))

            vrp_route_plan += \
                f' {self._vrp_input_data_dict["library_names"][self._vrp_index_manager.IndexToNode(index)]}\n\n'
            vrp_route_plan += f'\tRoute distance: {route_distance / self._METERS_PER_MILE:.2f} miles\n'
            vrp_route_plan += f'\tRoute time: {self._format_time_display(route_time)}\n'
            vrp_route_plan += f'\tRoute load: {route_load} containers\n'
            vrp_route_plan += f'\tNumber of stops: {num_stops - 1}\n'

            brk = break_intervals.Element(vehicle_id)
            if brk.PerformedValue():
                vrp_route_plan += f'\tBreak: start time = {self._format_time_display(brk.StartValue())}; ' \
                               f'end time = {self._format_time_display(brk.StartValue() + brk.DurationValue())}\n\n'
            else:
                vrp_route_plan += f'\tNo break.\n\n'

            total_distance += route_distance
            total_time += route_time

        vrp_route_plan += f'Total distance, all routes: {total_distance / self._METERS_PER_MILE:.2f} miles\n'

        total_mins, total_secs = divmod(total_time, 60)
        total_hours, total_mins = divmod(total_mins, 60)
        vrp_route_plan += f'Total time, all routes: {total_hours} {"hours" if total_hours > 1 else "hour"}, ' \
                       f'{total_mins} {"minutes" if total_mins > 1 else "minute"}'
        vrp_route_plan += f'\n\n' \
                          f'------------------------\n\n'

        self._vrp_route_plan = vrp_route_plan

    def __vrp_list_routes(self):
        """Get vehicle routes from a solution and store them in an array."""
        # Get vehicle routes and store them in a two dimensional array whose
        # i,j entry is the jth location visited by vehicle i along its route.
        vrp_route_array = []
        for route_nbr in range(self._vrp_routing_model.vehicles()):
            index = self._vrp_routing_model.Start(route_nbr)
            route = [self._vrp_input_data_dict['library_ids'][self._vrp_index_manager.IndexToNode(index)]]
            while not self._vrp_routing_model.IsEnd(index):
                index = self._vrp_solution.Value(self._vrp_routing_model.NextVar(index))
                route.append(self._vrp_input_data_dict['library_ids'][self._vrp_index_manager.IndexToNode(index)])
            vrp_route_array.append(route)
        self._vrp_route_array = vrp_route_array

    def solve_vrp(self):
        if self._config_dict['vehicle_increment']:
            while self._vrp_num_vehicles <= 15:
                print(f'Trying to solve VRP using {self._vrp_num_vehicles} ' +
                      ('vehicles...' if self._vrp_num_vehicles > 1 else 'vehicle...'), end='')
                self.__vrp_format_input_data()
                self.__vrp_initialize()
                self.__vrp_solve()
                if self._vrp_solution:
                    return self._vrp_solution
                self._vrp_num_vehicles += 1
            return None

        else:
            self.__vrp_format_input_data()
            self.__vrp_initialize()
            self.__vrp_solve()
            if self._vrp_solution:
                return self._vrp_solution
            else:
                return None

    def get_vrp_route_plan(self):
        if self._vrp_solution:
            self.__vrp_format_solution()
            return self._vrp_route_plan
        else:
            return None

    def get_vrp_route_array(self):
        if self._vrp_solution:
            self.__vrp_list_routes()
            return self._vrp_route_array
        else:
            return None
