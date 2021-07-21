import geocode_addresses_03 as geo
import dist_matrix_05 as dist
import vrp_solve_07 as solve
import vrp_route_map_02 as map

import argparse
import sys
import pandas as pd
import os
import yaml

# following two lines for testing only
pd.options.display.width = 0
pd.options.display.max_rows = 1000

def main():
    # TODO: add this all to a function or separate file
    # noinspection PyTypeChecker
    parser_obj = argparse.ArgumentParser(
        prog='tool',
        description='Set up and solve a Vehicle Routing Problem for a proposed WI library delivery region.',
        usage='input_file {ideal, starter} region_number {distance, duration} '
              'num_vehicles max_hours max_miles veh_cap break_time_minutes'
              '\n       {automatic, path_cheapest_arc, savings, sweep, christofides, parallel_cheapest_insertion, '
              'local_cheapest_insertion, global_cheapest_arc, local_cheapest_arc, first_unbound_min_value}'
              '\n       {automatic, greedy_descent, guided_local_search, simulated_annealing, tabu_search}'
              '\n       [-g/--geocode] [-r/--regions] [-o/--output] '
              '[--out_format {csv, xlsx}] [-m/--map] [-t/--text_file] '
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
    param_group.add_argument('veh_cap', action='store', default=50, type=int,
                             help='Vehicle capacity (all vehicles)')
    param_group.add_argument('break_time_minutes', action='store', default=0, type=float,
                             help='Total break time per route in minutes.')

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

    options_group = parser_obj.add_argument_group(title='Optional arguments')

    options_group.add_argument('-g', '--geocode', action='store_true', help='Add location geocode data to data file.')
    options_group.add_argument('-r', '--regions', action='store_true', help='Add proposed region data to data file.')
    options_group.add_argument('-o', '--output', action='store_true', help='Export updated data set to a file.')
    options_group.add_argument('--out_format', required='-o' in sys.argv or '--output' in sys.argv,
                        choices=['csv', 'xlsx'], default='csv', type=str,
                        help="Updated data set output file format ('csv' or 'xlsx').")
    options_group.add_argument('-m', '--map', action='store_true', help='Map optimal route plan '
                                                                        '(opens in default browser window).')
    options_group.add_argument('-t', '--text_file', action='store_true', help='Export solution to text file.')
    options_group.add_argument('-v', '--vehicle_increment', action='store_true', help='Add one vehicle to fleet and '
                                                                                      'resolve VRP until '
                                                                                      'feasible solution is found.')
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
    ##distance_matrix, duration_matrix = dist.create_matrices(api_address_array, conf_dict)
    # for testing
    distance_matrix = [[0, 97712, 98229, 98734, 100752, 83871, 83081, 107085, 108558, 98129, 81978, 73909, 119041, 120006, 15693, 13389, 22102, 19007, 26922, 18356, 55400, 21942, 59727, 49282, 61345, 28081, 22203, 17013], [97953, 0, 2586, 3643, 12329, 18239, 45286, 44494, 44744, 22588, 29276, 37556, 24410, 25376, 90045, 106631, 120556, 109325, 75966, 108508, 56524, 106891, 65943, 77658, 74783, 128627, 77668, 96804], [98860, 2849, 0, 1482, 10168, 16976, 43015, 44123, 44373, 20428, 27005, 35285, 24039, 25005, 90952, 107538, 121464, 107054, 76873, 109415, 54253, 107799, 63672, 75387, 72512, 129535, 78576, 97712], [99344, 3301, 1280, 0, 9775, 17460, 43498, 42778, 43028, 20035, 27489, 35769, 22694, 23660, 91436, 108022, 121947, 107537, 77357, 109899, 54737, 108282, 64156, 75871, 72996, 130019, 79059, 98195], [101380, 12148, 10128, 9875, 0, 17731, 35082, 39369, 40842, 11418, 19073, 27729, 23502, 24468, 93472, 110057, 123983, 99121, 66879, 111935, 46321, 108016, 55740, 67454, 64579, 132054, 81095, 100231], [83942, 18231, 16910, 17416, 17735, 0, 45494, 53704, 55177, 25702, 28422, 30249, 37722, 38688, 76034, 92620, 106545, 88024, 61955, 94497, 48069, 92880, 57488, 69202, 66327, 114616, 63657, 82793], [98428, 47754, 42662, 43168, 34676, 45533, 0, 26471, 28106, 19199, 17550, 15685, 40706, 40280, 77049, 104856, 112356, 80104, 57562, 108603, 27303, 88999, 36722, 48437, 36613, 118335, 66107, 89294], [126273, 46123, 44103, 42910, 38456, 53788, 26546, 0, 1353, 29294, 27660, 35060, 20233, 19837, 101040, 132701, 140200, 107948, 81553, 136448, 55148, 116844, 64567, 76282, 80441, 146180, 90098, 113285], [127688, 46224, 44203, 43010, 39872, 55204, 27847, 1500, 0, 30710, 29076, 36476, 20334, 19938, 102456, 134117, 141616, 109364, 82969, 137864, 56564, 118260, 65983, 77697, 81741, 147596, 91514, 114701], [98488, 27897, 22806, 20060, 11227, 25643, 19196, 29270, 30743, 0, 4356, 16830, 23023, 22597, 90581, 107166, 121092, 86711, 55980, 109044, 33911, 95607, 43330, 55044, 52170, 129163, 78204, 97340], [101052, 31649, 26557, 27062, 18571, 28547, 17572, 27657, 29130, 4376, 0, 9826, 26206, 25780, 75819, 107480, 114979, 82727, 56332, 111227, 29927, 91623, 39346, 51061, 48186, 120959, 64877, 88064], [73764, 38720, 33629, 34134, 25643, 30233, 15685, 34958, 36431, 13478, 9512, 0, 39329, 38903, 67910, 98556, 106056, 73804, 48423, 102303, 21004, 82699, 30423, 42137, 39262, 112036, 56968, 80155], [119608, 25890, 23869, 22676, 23506, 37724, 36513, 20084, 20334, 22786, 26211, 39373, 0, 966, 111700, 128286, 142211, 112262, 85867, 130163, 59462, 121157, 68881, 80595, 77720, 150282, 99323, 118459], [120695, 26977, 24956, 23763, 24593, 38810, 36806, 19462, 19712, 23080, 26504, 39667, 1087, 0, 112787, 129372, 143298, 112556, 86160, 131250, 59755, 121451, 69174, 80889, 78014, 151369, 100410, 119546], [15684, 84709, 85226, 85732, 87750, 70869, 77091, 101095, 102568, 85127, 75988, 67919, 106038, 107004, 0, 23460, 38311, 35006, 22648, 26263, 64213, 35447, 63067, 65281, 77344, 46382, 12251, 8349], [12193, 106465, 106982, 107487, 109506, 92624, 104384, 132278, 133751, 111136, 107171, 99546, 127794, 128760, 23156, 0, 9969, 26660, 41502, 4968, 76729, 26011, 67380, 56935, 68999, 14547, 33569, 18881], [21950, 120225, 120742, 121248, 123266, 106384, 111617, 139511, 140984, 120643, 114404, 106780, 141554, 142520, 38232, 9763, 0, 33893, 58050, 8480, 83963, 25744, 74614, 64169, 76232, 9275, 47329, 29671], [20469, 111891, 106800, 107305, 98814, 87896, 79897, 107790, 109264, 86649, 82683, 75059, 112161, 111735, 34587, 26897, 34397, 0, 26348, 30644, 52242, 10394, 42893, 32448, 44511, 40377, 24872, 39442], [27106, 75826, 76343, 76848, 67032, 61985, 57729, 81733, 83206, 56177, 56626, 48557, 86104, 85678, 22660, 41618, 58631, 26395, 0, 44017, 36689, 31423, 40488, 49368, 61431, 66702, 11271, 29513], [18530, 108861, 109378, 109883, 111902, 95020, 108432, 136326, 137799, 109278, 111219, 103594, 130190, 131156, 26867, 4936, 8544, 30708, 46686, 0, 80777, 30059, 71428, 60983, 73047, 16258, 35965, 17839], [55404, 59930, 54838, 55343, 46852, 48862, 26560, 55829, 57302, 34687, 30722, 23097, 60200, 59774, 64222, 76905, 84404, 52152, 36689, 80652, 0, 61048, 8428, 20486, 20116, 90384, 47891, 76467], [20126, 106744, 107261, 107766, 107825, 92903, 88908, 116802, 118275, 95660, 91695, 84071, 121173, 120747, 35369, 26555, 26437, 9407, 31449, 30302, 61253, 0, 51905, 41459, 53523, 28924, 29880, 39099], [66023, 68317, 63225, 63731, 55239, 57249, 36322, 64216, 65689, 43074, 39109, 31484, 68587, 68161, 80140, 72451, 79950, 47698, 42920, 76198, 8917, 56594, 0, 16032, 17372, 85930, 54122, 84996], [50869, 80637, 75545, 76050, 67559, 69569, 48642, 76535, 78009, 55394, 51429, 43804, 80907, 80481, 64986, 57297, 64796, 32544, 48948, 61044, 20987, 41440, 11638, 0, 11616, 70776, 56411, 69842], [62623, 77355, 72263, 72769, 64277, 66287, 36769, 80863, 82498, 52112, 48147, 40522, 77625, 77199, 76741, 69051, 76551, 44299, 60703, 72798, 20266, 53194, 16010, 11616, 0, 82531, 68166, 81596], [26875, 128216, 128733, 129239, 131257, 114376, 116542, 144436, 145909, 128634, 119329, 111704, 149545, 150511, 46223, 14800, 10165, 38818, 66041, 16486, 88887, 30669, 79538, 69093, 81157, 0, 55320, 37662], [21063, 77281, 77798, 78303, 80322, 63440, 66152, 90155, 91629, 77698, 65048, 56980, 98610, 99576, 12315, 30594, 47776, 24939, 11293, 35728, 47912, 29795, 51712, 55780, 67844, 55847, 0, 19168], [16966, 97136, 97653, 98158, 100177, 83295, 89548, 113551, 115025, 97553, 88444, 80376, 118465, 119431, 8342, 18851, 29851, 40046, 29494, 17805, 76669, 39397, 80766, 70321, 82385, 37923, 19097, 0]]
    duration_matrix = [[0, 3938, 3909, 3910, 3907, 3220, 4021, 5210, 5316, 4144, 4119, 3566, 4744, 4859, 1015, 1055, 1488, 1158, 1524, 1173, 2943, 1183, 2679, 2158, 2490, 1728, 1369, 1229], [3985, 0, 313, 347, 863, 1079, 2058, 2384, 2384, 1570, 1694, 2021, 1336, 1450, 3447, 4422, 4553, 4435, 3361, 4505, 2738, 4833, 2962, 3344, 3472, 4826, 3158, 3766], [4023, 314, 0, 176, 693, 1149, 1980, 2204, 2205, 1400, 1616, 1943, 1156, 1270, 3485, 4460, 4592, 4357, 3399, 4543, 2660, 4871, 2884, 3266, 3394, 4864, 3196, 3804], [3977, 316, 241, 0, 630, 1104, 1935, 2096, 2096, 1337, 1571, 1897, 1048, 1162, 3440, 4414, 4546, 4312, 3354, 4497, 2615, 4825, 2839, 3220, 3348, 4819, 3151, 3758], [4001, 850, 777, 631, 0, 1077, 1527, 2006, 2111, 900, 1163, 1496, 1156, 1270, 3464, 4439, 4570, 3905, 3295, 4522, 2207, 4363, 2431, 2813, 2941, 4843, 3175, 3783], [3269, 1062, 1110, 1112, 1070, 0, 2075, 2808, 2913, 1528, 1657, 1606, 1946, 2061, 2731, 3706, 3837, 3834, 2645, 3789, 2358, 4117, 2582, 2963, 3091, 4110, 2442, 3050], [3924, 1943, 1892, 1893, 1474, 2029, 0, 1330, 1480, 1130, 1059, 974, 1911, 1916, 3636, 4160, 4593, 3161, 2707, 4237, 1464, 3620, 1688, 2069, 2054, 4833, 3226, 3976], [5155, 2357, 2285, 2096, 1915, 2779, 1336, 0, 218, 1601, 1529, 1863, 1062, 1083, 4831, 5392, 5824, 4393, 3902, 5469, 2696, 4851, 2919, 3301, 3043, 6065, 4421, 5171], [5266, 2350, 2278, 2089, 2026, 2890, 1478, 204, 0, 1712, 1640, 1974, 1055, 1076, 4942, 5503, 5935, 4504, 4013, 5580, 2807, 4962, 3030, 3412, 3185, 6176, 4532, 5281], [4192, 1441, 1390, 1393, 924, 1498, 1165, 1657, 1762, 0, 614, 1257, 1363, 1368, 3655, 4629, 4761, 3681, 3056, 4712, 1983, 4139, 2207, 2589, 2717, 5034, 3365, 3973], [4004, 1492, 1441, 1443, 1024, 1622, 1039, 1527, 1632, 551, 0, 833, 1579, 1584, 3679, 4241, 4673, 3241, 2751, 4318, 1544, 3700, 1768, 2150, 2278, 4914, 3270, 4019], [3600, 1969, 1918, 1920, 1501, 1632, 969, 1860, 1965, 1208, 856, 0, 2031, 2036, 3233, 3872, 4304, 2873, 2305, 3949, 1176, 3331, 1400, 1781, 1909, 4545, 2824, 3573], [4811, 1295, 1223, 1034, 1162, 1937, 1915, 1049, 1049, 1280, 1592, 2031, 0, 115, 4273, 5248, 5380, 4561, 4071, 5331, 2864, 5020, 3088, 3469, 3598, 5652, 3984, 4592], [4995, 1479, 1407, 1218, 1346, 2121, 1984, 1067, 1067, 1349, 1662, 2100, 184, 0, 4457, 5432, 5564, 4631, 4140, 5515, 2933, 5089, 3157, 3539, 3667, 5836, 4168, 4776], [1060, 3482, 3453, 3454, 3451, 2764, 3650, 4839, 4945, 3688, 3749, 3196, 4288, 4403, 0, 1556, 1687, 1906, 1347, 1638, 3079, 2170, 3365, 2906, 3238, 1960, 834, 624], [1046, 4428, 4399, 4400, 4397, 3710, 4110, 5324, 5430, 4585, 4233, 3756, 5234, 5349, 1531, 0, 801, 1283, 2422, 479, 3163, 1302, 2804, 2283, 2615, 1033, 1883, 1386], [1420, 4495, 4466, 4468, 4464, 3777, 4519, 5733, 5839, 4701, 4642, 4165, 5302, 5416, 1622, 750, 0, 1692, 2512, 767, 3572, 1433, 3213, 2692, 3024, 699, 1950, 1462], [1114, 4413, 4362, 4364, 3945, 3818, 3177, 4391, 4497, 3652, 3300, 2823, 4562, 4567, 1816, 1351, 1783, 0, 1529, 1428, 2230, 731, 1871, 1350, 1682, 2023, 1546, 1994], [1529, 3354, 3325, 3327, 3302, 2637, 2731, 3920, 4026, 3046, 2829, 2276, 4092, 4097, 1334, 2350, 2611, 1515, 0, 2587, 1810, 1842, 2071, 2260, 2592, 2883, 714, 1822], [1215, 4496, 4467, 4469, 4465, 3778, 4254, 5468, 5574, 4702, 4377, 3900, 5303, 5417, 1623, 468, 852, 1427, 2513, 0, 3307, 1447, 2948, 2427, 2759, 1163, 1951, 1410], [2943, 2767, 2715, 2717, 2298, 2431, 1541, 2745, 2850, 2005, 1654, 1176, 2916, 2921, 3086, 3158, 3590, 2158, 1823, 3235, 0, 2617, 673, 1067, 1196, 3831, 2459, 3426], [1165, 4837, 4808, 4809, 4406, 4119, 3638, 4853, 4958, 4113, 3762, 3284, 5024, 5029, 2105, 1402, 1619, 763, 1845, 1479, 2692, 0, 2333, 1811, 2144, 1827, 1847, 2045], [2590, 2841, 2790, 2792, 2373, 2505, 1605, 2819, 2925, 2080, 1728, 1251, 2990, 2995, 3292, 2827, 3259, 1828, 2139, 2904, 657, 2286, 0, 736, 965, 3500, 2775, 3470], [2063, 3293, 3242, 3243, 2824, 2957, 2057, 3271, 3376, 2531, 2180, 1702, 3442, 3447, 2765, 2300, 2732, 1300, 2163, 2377, 1110, 1759, 751, 0, 676, 2972, 2530, 2943], [2410, 3428, 3377, 3378, 2959, 3092, 2067, 3071, 3221, 2666, 2315, 1837, 3577, 3582, 3112, 2647, 3079, 1647, 2510, 2724, 1257, 2106, 970, 685, 0, 3320, 2877, 3290], [1769, 4866, 4837, 4839, 4836, 4149, 4869, 6083, 6189, 5073, 4992, 4515, 5673, 5788, 1993, 1056, 649, 2042, 2884, 1175, 3922, 1783, 3563, 3042, 3374, 0, 2322, 1834], [1390, 3134, 3105, 3107, 3104, 2417, 3226, 4415, 4520, 3341, 3324, 2771, 3941, 4056, 780, 1938, 2041, 1573, 744, 1993, 2501, 1856, 2762, 2645, 2977, 2314, 0, 1268], [1231, 3812, 3782, 3784, 3781, 3094, 4018, 5208, 5313, 4018, 4117, 3564, 4618, 4733, 592, 1379, 1509, 2058, 1789, 1383, 3447, 2077, 3579, 3057, 3390, 1782, 1276, 0]]

    # check results
    dist.check_matrix_results(distance_matrix)
    dist.check_matrix_results(duration_matrix)

    vrp_input_dict = solve.format_ORtools_data(distance_matrix, duration_matrix, region_data, conf_dict)

    vrp_model, vrp_index = solve.vrp_setup(vrp_input_dict, conf_dict)

    vrp_solution = solve.solve_vrp(vrp_model, conf_dict)

    if vrp_solution:
        solve.print_solution(vrp_input_dict, vrp_index, vrp_model, vrp_solution)
        opt_routes = solve.get_routes(vrp_input_dict, vrp_index, vrp_model, vrp_solution)
        if conf_dict['map']:
            map.map_vrp_routes(opt_routes, region_data, conf_dict['general_maps_api_key'], conf_dict['model'],
                               conf_dict['region_number'])
    else:
        print('No solution found.')


if __name__ == '__main__':
    main()
