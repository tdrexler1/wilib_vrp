import gmplot
import webbrowser
import string
import random

# TODO: need to override class _Route(object)
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
                         'wi_state_gove': 'WI Government',
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


def map_vrp_routes(route_array, stop_data, gmaps_api_key, model_name, region_number):



    route_colors = random.sample(ROUTE_COLORS, len(route_array))

    stop_data_dict = stop_data.to_dict()

    hub_id = route_array[0][0]

    gmap = gmplot.GoogleMapPlotter(
        float(stop_data_dict['latitude'][hub_id]),
        float(stop_data_dict['longitude'][hub_id]),
        15,
        apikey=gmaps_api_key
    )

    gmap.marker(float(stop_data_dict['latitude'][hub_id]), float(stop_data_dict['longitude'][hub_id]),
                color='white',
                label='*',
                title=f"Region {region_number} Hub",
                info_window=f"<strong>{model_name.capitalize()} proposal, region {region_number} hub</strong>"
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
            [(float(stop_data_dict['latitude'][x]), float(stop_data_dict['longitude'][x])) for x in route[1:-2]]

        gmap.directions(origin, destination, waypoints=waypoints_list, route_color=route_colors[n])

        for m, wp in enumerate(route[1:-2]):
            gmap.marker(float(stop_data_dict['latitude'][wp]), float(stop_data_dict['longitude'][wp]),
                        color=route_colors[n],
                        label=list(string.ascii_uppercase)[m],
                        label_color='white',
                        title=stop_data_dict['stop_short_name'][wp],
                        info_window=write_infowindow_text(stop_data_dict, wp, m, n)
                        )

    gmap.draw('gmap.html')

    filepath = 'C:/Users/tdrex/PycharmProjects/wilib_vrp/gmap.html'
    #filepath = 'C:/Users/zzzlib/PycharmProjects/wilib_vrp/gmap.html'

    # https://stackoverflow.com/questions/22445217/python-webbrowser-open-to-open-chrome-browser
    chrome_path = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s'
    webbrowser.get(chrome_path).open('file://' + filepath)
    #webbrowser.open('file:\\' + filepath)
