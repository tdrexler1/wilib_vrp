import gmplot
import webbrowser
import string
import random
import time
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options  # chromedriver must be in PATH

from wi_lib_vrp_gmaps_mod_classes import write_point, write_map, directions, marker, write_points
from gmplot.gmplot import GoogleMapPlotter

GoogleMapPlotter.directions = directions
GoogleMapPlotter.write_map = write_map
GoogleMapPlotter.write_point = write_point
GoogleMapPlotter.marker = marker
GoogleMapPlotter.write_points = write_points

# Google GENERAL MAPS API key - works for maps_javascript_api & directions_api




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

    stop_address = \
        ' '.join(
            f"{str(library_data['address_number'][lib_id])} "
            f"{str(library_data['address_street_dir_prefix'][lib_id])} "
            f"{str(library_data['address_street'][lib_id])} "
            f"{str(library_data['address_street_suffix'][lib_id])} "
            f"{str(library_data['address_street_dir_suffix'][lib_id])}".replace('nan', '').split()
        )

    iw_text_string = f"<strong>{library_data['stop_full_name'][lib_id]}</strong>" \
                     f"<br>" \
                     f"{stop_address}" \
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


def map_vrp_routes(route_array, stop_data, gmaps_api_key, model_id, output_dir):

    ROUTE_COLORS = ['#1E90FF', '#3CB371', '#B22222', '#9370DB', '#D2691E', '#DAA520', '#708090', '#008080', '#A0522D',
                    '#DB7093', '#6B8E23', '#00BFFF', '#483D8B', '#FF0000', '#D8BFD8', '#800000', '#ADFF2F', '#FF1493',
                    '#FF4500', '#4682B4', '#32CD32', '#CD5C5C', '#556B2F', '#FFD700', '#9400D3']

    dark_text = ['#D8BFD8', '#ADFF2F', '#FFD700']

    route_colors = random.sample(ROUTE_COLORS, k=len(route_array))

    bounds_dict = {'north': float(stop_data['latitude'].max()),
                   'south': float(stop_data['latitude'].min()),
                   'east': float(stop_data['longitude'].min()),
                   'west': float(stop_data['longitude'].max())}

    stop_data_dict = stop_data.to_dict()

    hub_id = route_array[0][0]

    gmap = gmplot.GoogleMapPlotter(
        float(stop_data_dict['latitude'][hub_id]),
        float(stop_data_dict['longitude'][hub_id]),
        0,
        apikey=gmaps_api_key,
        fit_bounds=bounds_dict,
        title=f'{model_id} Route Map'
    )

    proposal_type = 'Ideal' if model_id[0:2] == 'idl' else 'Starter'

    hub_address = \
        str(stop_data_dict['address_number'][hub_id]) + \
        str(stop_data_dict['address_street_dir_prefix'][hub_id]) + \
        str(stop_data_dict['address_street'][hub_id]) + \
        str(stop_data_dict['address_street_suffix'][hub_id]) + \
        str(stop_data_dict['address_street_dir_suffix'][hub_id])

    gmap.marker(float(stop_data_dict['latitude'][hub_id]), float(stop_data_dict['longitude'][hub_id]),
                color='white',
                label='*',
                title=f"Region {model_id[3:4]} Hub",
                info_window=f"<strong>{proposal_type} proposal, region {model_id[3:4]} hub</strong>"
                            f"<br>"
                            f"<br>"
                            f"Location:"
                            f"<br>"
                            f"{stop_data_dict['stop_full_name'][hub_id]}"
                            f"<br>"
                            f"{hub_address}"
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
            [(float(stop_data_dict['latitude'][x]), float(stop_data_dict['longitude'][x])) for x in route[1:-2]]

        gmap.directions(origin, destination, waypoints=waypoints_list, route_color=route_colors[n])

        for m, wp in enumerate(route[1:-2]):
            gmap.marker(float(stop_data_dict['latitude'][wp]), float(stop_data_dict['longitude'][wp]),
                        color=route_colors[n],
                        label=list(string.ascii_uppercase)[m],
                        label_color='black' if route_colors[n] in dark_text else 'white',
                        title=stop_data_dict['stop_short_name'][wp],
                        info_window=write_infowindow_text(stop_data_dict, wp, m, n)
                        )

    gmap_file = output_dir + model_id + '.html'

    gmap.draw(gmap_file)

    return gmap_file

def display_map(route_map):

    # https://stackoverflow.com/questions/22445217/python-webbrowser-open-to-open-chrome-browser
    chrome_path = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s'
    webbrowser.get(chrome_path).open('file://' + route_map)

    # open system default browser
    #webbrowser.open('file://' + map_file_name + route_map)


def screenshot_map(route_map, output_dir):

    chrome_options = Options()
    chrome_options.add_argument("--headless")

    png_filepath = output_dir + os.path.basename(route_map)[:-4] + 'png'

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1920, 1080)
    driver.get(route_map)
    time.sleep(2)
    driver.save_screenshot(png_filepath)
