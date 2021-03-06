import webbrowser
import string
import random
import time
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options  # chromedriver must be in PATH
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# import method overrides for gmplot GoogleMapPlotter object
# https://stackoverflow.com/a/50600307
from wi_lib_vrp_gmaps_sub_classes import GoogleMapPlotter_mod


def write_infowindow_text(library_data, lib_id, stop_number, route_number):
    """
    Constructs the text shown in Google Maps InfoWindow for each library, which
    appear when the library marker is clicked.

    :param library_data: Dict of input data from external file.
    :type library_data: dict
    :param lib_id: ID of library associated with marker.
    :type lib_id: str
    :param stop_number: Denotes position of current stop in route stop sequence.
    :type stop_number: int
    :param route_number: Vehicle number for current route.
    :type route_number: int
    :return: String of InfoWindow text with HTML formatting.
    :rtype: str
    """

    # translate stop type from input data file to readable format
    stop_type_strings = {'library_system': 'Library system',
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

    # assemble address string from components
    stop_address = \
        ' '.join(
            f"{str(library_data['address_number'][lib_id])} "
            f"{str(library_data['address_street_dir_prefix'][lib_id])} "
            f"{str(library_data['address_street'][lib_id])} "
            f"{str(library_data['address_street_suffix'][lib_id])} "
            f"{str(library_data['address_street_dir_suffix'][lib_id])}".replace('nan', '').split()
        )

    # format InfoWindow text string with HTML tags
    iw_text_string = f"<strong>{library_data['stop_full_name'][lib_id]}</strong>" \
                     f"<br>" \
                     f"{stop_address}" \
                     f"<br>" \
                     f"{library_data['address_city'][lib_id]}, WI {library_data['address_zip'][lib_id]}" \
                     f"<br>" \
                     f"<br>" \
                     f"Stop type: {stop_type_strings[library_data['stop_type'][lib_id]]}" \
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
    """
    Creates a Google Map file using the 'gmplot' package. Initializes the map, adds markers for
    regional hub and library stops, and draws lines showing each route in a unique color.

    :param route_array: Nested lists of route stops in sequence from VrpModelObj
    :type route_array: list
    :param stop_data: Pandas DataFrame of input data from external file.
    :type stop_data: pandas.DataFrame
    :param gmaps_api_key: Google Maps API key for both maps_javascript_api & directions_api (should be an unrestricted key).
    :type gmaps_api_key: str
    :param model_id: VRP model ID code.
    :type model_id: str
    :param output_dir: Path to directory where HTML map files will be saved.
    :type output_dir: str
    :return: HTML file of the completed Google Map.
    :rtype: HTML file
    """

    # selected colors for routes & markers
    # chosen from list of gmplot supported colors (marker image files in 'markers' dir)
    route_colors = ['#1E90FF', '#3CB371', '#B22222', '#9370DB', '#D2691E', '#DAA520', '#708090', '#008080', '#A0522D',
                    '#DB7093', '#6B8E23', '#00BFFF', '#483D8B', '#FF0000', '#D8BFD8', '#800000', '#ADFF2F', '#FF1493',
                    '#FF4500', '#4682B4', '#32CD32', '#CD5C5C', '#556B2F', '#FFD700', '#9400D3']

    # marker colors requiring dark text for readability
    dark_text = ['#D8BFD8', '#ADFF2F', '#FFD700']

    # randomly choose route colors for all routes
    route_colors = random.sample(route_colors, k=len(route_array))

    # convert library input DataFrame to dict
    stop_data_dict = stop_data.to_dict()

    # id of regional hub
    hub_id = route_array[0][0]

    # initialize map object

    # https://stackoverflow.com/a/19164261
    gmap = GoogleMapPlotter_mod(
        float(stop_data_dict['latitude'][hub_id]),
        float(stop_data_dict['longitude'][hub_id]),
        0,
        apikey=gmaps_api_key,
        title=f'{model_id} Route Map'
    )

    # construct/retrieve information for hub marker InfoWindow (proposal type, street address)
    proposal_type = 'Ideal' if model_id[0:2] == 'idl' else 'Starter'

    hub_address = \
        str(stop_data_dict['address_number'][hub_id]) + \
        str(stop_data_dict['address_street_dir_prefix'][hub_id]) + \
        str(stop_data_dict['address_street'][hub_id]) + \
        str(stop_data_dict['address_street_suffix'][hub_id]) + \
        str(stop_data_dict['address_street_dir_suffix'][hub_id])

    # add specialized map marker for regional hub
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

    # iterate over regional routes/vehicles
    for n, route in enumerate(route_array):

        # retrieve route sequence data for gmplot request to Google Maps Directions API
        origin = (float(stop_data_dict['latitude'][hub_id]), float(stop_data_dict['longitude'][hub_id]))
        destination = origin
        waypoints_list = \
            [(float(stop_data_dict['latitude'][x]), float(stop_data_dict['longitude'][x])) for x in route[1:-1]]

        # get route directions for current route/vehicle
        # Directions Service: https://developers.google.com/maps/documentation/javascript/directions
        gmap.directions(origin, destination, waypoints=waypoints_list, route_color=route_colors[n])

        # iterate over stops on current route
        for m, wp in enumerate(route[1:-1]):

            # add Google Maps marker for current stop
            gmap.marker(float(stop_data_dict['latitude'][wp]), float(stop_data_dict['longitude'][wp]),
                        color=route_colors[n],
                        label=list(string.ascii_uppercase + string.ascii_lowercase)[m],
                        label_color='black' if route_colors[n] in dark_text else 'white',
                        title=stop_data_dict['stop_short_name'][wp],
                        info_window=write_infowindow_text(stop_data_dict, wp, m, n)
                        )

    # construct output file name
    gmap_file = output_dir + model_id + '.html'

    # output HTML file of Google Map
    gmap.draw(gmap_file)

    return gmap_file


def display_map(route_map):
    """
    Opens HTML file of Google Map in browser window or new tab.

    :param route_map: HTML file of Google Map with routes & stop markers.
    :type route_map: HTML file
    """

    # https://stackoverflow.com/a/24353812 - open map in Chrome browser/tab
    chrome_path = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s'
    webbrowser.get(chrome_path).open('file://' + route_map)

    # option to open map in system default browser

    # webbrowser.open('file://' + map_file_name + route_map)


def screenshot_map(route_map, output_dir):
    """
    Uses a headless Chrome browser to open Google Map file and take a screenshot,
    saved as a PNG image file.

    * Note: requires 'chromedriver' for 'selenium' package, which must be added to PATH

    :param route_map: HTML file of Google Map with routes & stop markers.
    :type route_map: HTML file
    :param output_dir: Path to directory where PNG image files will be saved.
    :type output_dir: str
    """

    # Selenium documentation:
    # https://selenium-python.readthedocs.io/index.html
    # https://www.selenium.dev/selenium/docs/api/py/index.html
    # https://www.selenium.dev/documentation/

    # configure headless Chrome browser
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    # construct output file name from map file name
    png_filepath = output_dir + os.path.basename(route_map)[:-4] + 'png'

    # use selenium webdriver to open map file & save screenshot
    driver = webdriver.Chrome(options=chrome_options)

    # set browser window size based on region - these sizes show every library
    win_size_dict = {
        'idl1': (600, 750),
        'idl2': (500, 650),
        'idl3': (1000, 1000),
        'idl4': (900, 900),
        'idl5': (850, 650),
        'idl6': (950, 700),
        'idl7': (1000, 850),
        'str1': (750, 500),
        'str2': (900, 800),
        'str3': (900, 900),
        'str4': (1000, 1000),
        'str5': (800, 800),
        'str6': (850, 650),
        'str7': (500, 650),
        'str8': (700, 500)
    }
    map_region = os.path.basename(route_map)[0:4]
    driver.set_window_size(win_size_dict[map_region][0], win_size_dict[map_region][1])

    # open the html map file
    driver.get(route_map)

    # force browser to wait until Google Maps script finishes rendering
    # https://stackoverflow.com/a/27112797
    element_list = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, 'gmnoprint'))
    )
    element_list.append(driver.find_element_by_class_name('gm-fullscreen-control'))

    # delete Google Maps controls & other elements
    for delete_element in element_list:

        try:
            # https://stackoverflow.com/q/22515012
            driver.execute_script("""
            var element = arguments[0];
            element.parentNode.removeChild(element);
            """, delete_element)

        # remove any already-deleted items from list
        except:
            # https://stackoverflow.com/a/36013523, https://www.selenium.dev/exceptions/#stale_element_reference
            element_list.remove(delete_element)

    # ensure adequate time for routes to render
    # https://stackoverflow.com/a/58264507, https://stackoverflow.com/a/58981854
    time.sleep(15)

    # output screenshot
    map_element = driver.find_element_by_id('map_canvas')
    map_element.screenshot(png_filepath)
