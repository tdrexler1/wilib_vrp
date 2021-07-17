import gmplot
import webbrowser
import string
import random

# TODO: need to override class _Route(object)
from route_mod_class import write_point, write_map, directions, marker
from gmplot.gmplot import GoogleMapPlotter

# Google GENERAL MAPS API key - works for maps_javascript_api & directions_api

ROUTE_COLORS = ['#1E90FF', '#3CB371', '#B22222', '#9370DB', '#D2691E', '#DAA520', '#708090', '#008080', '#A0522D',
                '#DB7093', '#6B8E23', '#00BFFF', '#483D8B']

def map_vrp_routes(route_array, stop_data, gmaps_api_key):

    GoogleMapPlotter.directions = directions
    GoogleMapPlotter.write_map = write_map
    GoogleMapPlotter.write_point = write_point
    GoogleMapPlotter.marker = marker
    #random.shuffle(ROUTE_COLORS)

    gmap = gmplot.GoogleMapPlotter(43.04955, -89.39237, 15, apikey=gmaps_api_key)


    stop_data_dict = stop_data.to_dict()

    hub_id = route_array[0][0]
    gmap.marker(float(stop_data_dict['latitude'][hub_id]), float(stop_data_dict['longitude'][hub_id]),
                        color='white',
                        label = '*',
                        label_color='blue'
                    )

    for n, route in enumerate(route_array):

        origin = (float(stop_data.loc[route[0], 'latitude']), float(stop_data.loc[route[0], 'longitude']))
        destination = (float(stop_data.loc[route[-1], 'latitude']), float(stop_data.loc[route[-1], 'longitude']))
        waypoints_list = \
            [(float(stop_data.loc[x, 'latitude']), float(stop_data.loc[x, 'longitude'])) for x in route[1:-2]]

        gmap.directions(origin, destination, waypoints=waypoints_list, route_color=ROUTE_COLORS[n])

        # TODO: write a function to create the info window string
        # TODO: add origin/destination marker with special formatting

        for m, wp in enumerate(route[1:-2]):
            gmap.marker(float(stop_data_dict['latitude'][wp]), float(stop_data_dict['longitude'][wp]),
                        color=ROUTE_COLORS[n],
                        label=list(string.ascii_uppercase)[m],
                        title=stop_data_dict['stop_short_name'][wp],
                        label_color='white',
                        info_window=f"{stop_data_dict['stop_short_name'][wp]}<br>{stop_data_dict['stop_type'][wp]}"
                        )

    gmap.draw('gmap.html')

    filepath = 'C:/Users/tdrex/PycharmProjects/wilib_vrp/gmap.html'
    #filepath = 'C:/Users/zzzlib/PycharmProjects/wilib_vrp/gmap.html'

    # https://stackoverflow.com/questions/22445217/python-webbrowser-open-to-open-chrome-browser
    chrome_path = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s'
    webbrowser.get(chrome_path).open('file://' + filepath)
    #webbrowser.open('file:\\' + filepath)
