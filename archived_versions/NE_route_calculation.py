import os
import pandas as pd
import yaml
import json
import urllib.request

METERS_PER_MILE = 1609.34
SECONDS_PER_HOUR = 3600
SECONDS_PER_MINUTE = 60

def format_time_display(time_in_seconds):

    mins, secs = divmod(time_in_seconds, 60)
    hrs, mins = divmod(mins, 60)

    time_display_string = f'{hrs} {"hours" if hrs > 1 else "hour"}, {mins} {"minutes" if mins > 1 else "minute"}'

    return time_display_string

def map_vrp_routes():

    # Google Maps API keys
    try:
        with open(os.path.expanduser('~/google_maps_api_key.yml'), 'r') as api_keys:
            key_data = yaml.full_load(api_keys)
    except OSError as e:
        print(e)

    gmaps_api_key = key_data['google_maps']['general_maps_api_key']

    route = ['WI2200', 'UWSYS320', 'WI1200', 'UWSYS280', 'UWSYS180', 'WI1600', 'UWSYS160', 'WITC220', 'WI1900',
                    'ACAD0190', 'WITC130', 'WI2100', 'ACAD0090', 'UWSYS150', 'WIGOV320', 'WIGOV330', 'UWSYS220',
                    'WI2600', 'UWSYS140', 'WITC190', 'ACAD0100', 'ACAD0160']

    model_name = 'NE w/ West Bend'
    region_number = 0

    stop_data = pd.read_excel(
        'NE_WI_route_geo.xlsx',
        header=0,
        index_col='LIBID',
        dtype=str,
        engine='openpyxl')

    stop_data_dict = stop_data.to_dict()

    hub_id = route[0]

    #print(route_array)
    #print(hub_id)
    #print(gmaps_api_key)
    #for k, v in stop_data_dict.items():
    #    print(f'{k}, {v}')

    origin = (float(stop_data_dict['latitude'][hub_id]), float(stop_data_dict['longitude'][hub_id]))
    destination = origin
    waypoints_list = \
        [(float(stop_data_dict['latitude'][x]), float(stop_data_dict['longitude'][x])) for x in route[1:-1]]


    request_url_base_str = 'https://maps.googleapis.com/maps/api/directions/json?'

    request_url_str = request_url_base_str + f'origin={origin[0]},{origin[1]}&destination={destination[0]},{destination[1]}'
    request_url_str += f"&waypoints="
    for wp in waypoints_list:
        request_url_str += f"{wp[0]},{wp[1]}|"
    request_url_str = request_url_str[:-1]

    request_url_str += f'&key={gmaps_api_key}'

    # send API request
    json_result = urllib.request.urlopen(request_url_str).read()

    # results as JSON object
    response = json.loads(json_result)

    total_distance = 0
    total_time = 0

    #print(response['routes'][0]['legs'])

    for leg in response['routes'][0]['legs']:
        total_distance += leg['distance']['value']
        total_time += leg['duration']['value'] + (7*60)

    print(f'total distance: {total_distance/METERS_PER_MILE:.2f}')
    print(f'total time: {format_time_display(total_time)}')

def main():
    map_vrp_routes()


if __name__ == '__main__':
    main()