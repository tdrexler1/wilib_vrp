import gmplot
import webbrowser
import string
import random
import os
import pandas as pd
import yaml

from route_mod_class import write_point, write_map, directions, marker, write_points
from gmplot.gmplot import GoogleMapPlotter

GoogleMapPlotter.directions = directions
GoogleMapPlotter.write_map = write_map
GoogleMapPlotter.write_point = write_point
GoogleMapPlotter.marker = marker
GoogleMapPlotter.write_points = write_points

# Google GENERAL MAPS API key - works for maps_javascript_api & directions_api

ROUTE_COLORS = ['#1E90FF', '#3CB371', '#B22222', '#9370DB', '#D2691E', '#DAA520', '#708090', '#008080', '#A0522D',
                '#DB7093', '#6B8E23', '#00BFFF', '#483D8B']

def write_infowindow_text(library_data, lib_id, stop_number, route_number):

    STOP_TYPE_STRINGS = {'library_system': 'Library system',
                         'outreach_service': 'Outreach service',
                         'private_academic': 'Academic library (private)',
                         'ARC': 'WHS Area Research Center',
                         'nwls_mailabook': 'NWLS mailabook',
                         'public_library': 'Public library',
                         'school': 'School library',
                         'uw_madison': 'UW-Madison campus library',
                         'uw_system': 'UW-System campus library',
                         'wi_state_gov': 'WI Government',
                         'wi_tech_college': 'WI Technical College library'}

    iw_text_string = f"<strong>{library_data['stop_full_name'][lib_id]}</strong>" \
                     f"<br>" \
                     f"{library_data['address_street_number'][lib_id]}" \
                     f"<br>" \
                     f"{library_data['address_city'][lib_id]}, WI {library_data['address_zip'][lib_id]}" \
                     f"<br>" \
                     f"<br>" \
                     f"Stop type: {STOP_TYPE_STRINGS[library_data['stop_type'][lib_id]]}" \
                     f"<br>" \
                     f"<br>" \
                     f"Route: #{route_number+1}" \
                     f"<br>" \
                     f"Route order: stop #{stop_number+1}" \
                     f"<br>" \
                     f"<br>" \
                     f"Average drop-off: {library_data['avg_dropoff'][lib_id]}" \
                     f"<br>" \
                     f"Average pick-up: {library_data['avg_pickup'][lib_id]}"

    return iw_text_string


def map_vrp_routes():

    # Google Maps API keys
    try:
        with open(os.path.expanduser('~/google_maps_api_key.yml'), 'r') as api_keys:
            key_data = yaml.full_load(api_keys)
    except OSError as e:
        print(e)
    gmaps_api_key = key_data['google_maps']['general_maps_api_key']

    route_array = [['WI2200', 'UWSYS320', 'WI1200', 'UWSYS280', 'UWSYS180', 'WI1600', 'UWSYS160', 'WITC220', 'WI1900',
                    'ACAD0190', 'WITC130', 'WI2100', 'ACAD0090', 'UWSYS150', 'WIGOV320', 'WIGOV330', 'UWSYS220',
                    'WI2600', 'UWSYS140', 'WITC190', 'ACAD0100', 'ACAD0160']]

    model_name = 'NE w/ West Bend'
    region_number = 0

    route_colors = random.sample(ROUTE_COLORS, len(route_array))

    stop_data = pd.read_excel(
        'NE_WI_route_geo.xlsx',
        header=0,
        index_col='LIBID',
        dtype=str,
        engine='openpyxl')

    stop_data_dict = stop_data.to_dict()

    hub_id = route_array[0][0]

    #print(route_array)
    #print(hub_id)
    #print(gmaps_api_key)
    #for k, v in stop_data_dict.items():
    #    print(f'{k}, {v}')


    gmap = gmplot.GoogleMapPlotter(
        43.04955, -89.39237, 15,
        apikey=gmaps_api_key
    )

    gmap.marker(float(stop_data_dict['latitude'][hub_id]), float(stop_data_dict['longitude'][hub_id]),
                color='white',
                label='*',
                title=f"Region {region_number} Hub",
                info_window=f"<strong>{model_name.capitalize()}</strong>"
                            f"<br>"
                            f"<br>"
                            f"Location:"
                            f"<br>"
                            f"{stop_data_dict['stop_full_name'][hub_id]}"
                            f"<br>"
                            f"{stop_data_dict['address_street_number'][hub_id]}"
                            f"<br>"
                            f"{stop_data_dict['address_city'][hub_id]}, WI {stop_data_dict['address_zip'][hub_id]}",
                label_color='black',
                label_font_size='20px',
                label_font_weight='bold'
                )

    for n, route in enumerate(route_array):

        origin = (float(stop_data_dict['latitude'][hub_id]), float(stop_data_dict['longitude'][hub_id]))
        destination = origin
        waypoints_list = \
            [(float(stop_data_dict['latitude'][x]), float(stop_data_dict['longitude'][x])) for x in route[1:-1]]

        google.maps.DirectionsService().route()
        gmap.directions(origin, destination, waypoints=waypoints_list, route_color=route_colors[n])

        for m, wp in enumerate(route[1:-1]):
            gmap.marker(float(stop_data_dict['latitude'][wp]), float(stop_data_dict['longitude'][wp]),
                        color=route_colors[n],
                        label=list(string.ascii_uppercase)[m],
                        label_color='white',
                        title=stop_data_dict['stop_short_name'][wp],
                        info_window=write_infowindow_text(stop_data_dict, wp, m, n)
                        )

    gmap.draw('NE_gmap.html')

    filepath = os.path.expanduser('~/PycharmProjects/wilib_vrp/NE_gmap.html')

    # https://stackoverflow.com/questions/22445217/python-webbrowser-open-to-open-chrome-browser
    chrome_path = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s'
    webbrowser.get(chrome_path).open('file://' + filepath)

    # open system default browser
    #webbrowser.open('file://' + filepath)


def main():
    map_vrp_routes()


if __name__ == '__main__':
    main()