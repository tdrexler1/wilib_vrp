import gmplot
import webbrowser
import string

# TODO: need to override class _Route(object)
from route_mod_class import write_point, write_map, directions
from gmplot.gmplot import GoogleMapPlotter

# Google GENERAL MAPS API key - works for maps_javascript_api & directions_api

def map_vrp_routes(route_array, stop_data, gmaps_api_key):

    GoogleMapPlotter.directions = directions
    GoogleMapPlotter.write_map = write_map
    GoogleMapPlotter.write_point = write_point

    gmap = gmplot.GoogleMapPlotter(43.04955, -89.39237, 15, apikey=gmaps_api_key)
    route_colors = ['blue', 'green', 'red']

    stop_data_dict = stop_data.to_dict()

    for n, route in enumerate(route_array):

        origin = (float(stop_data.loc[route[0], 'latitude']), float(stop_data.loc[route[0], 'longitude']))
        destination = (float(stop_data.loc[route[-1], 'latitude']), float(stop_data.loc[route[-1], 'longitude']))
        waypoints_list = \
            [(float(stop_data.loc[x, 'latitude']), float(stop_data.loc[x, 'longitude'])) for x in route[1:-2]]

        gmap.directions(origin, destination, waypoints=waypoints_list, route_color=route_colors[n])

        # TODO: write a function to create the info window string
        # TODO: add origin/destination marker with special formatting

        for m, wp in enumerate(route[1:-2]):
            gmap.marker(float(stop_data_dict['latitude'][wp]), float(stop_data_dict['longitude'][wp]),
                        color=route_colors[n],
                        label=list(string.ascii_uppercase)[m],
                        title=stop_data_dict['stop_short_name'][wp],
                        info_window=f"{stop_data_dict['stop_short_name'][wp]}<br>{stop_data_dict['stop_type'][wp]}"
                        )

    gmap.draw('gmap.html')

    filepath = 'C:/Users/tdrex/PycharmProjects/wilib_vrp/gmap.html'
    #filepath = 'C:/Users/zzzlib/PycharmProjects/wilib_vrp/gmap.html'

    # https://stackoverflow.com/questions/22445217/python-webbrowser-open-to-open-chrome-browser
    chrome_path = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s'
    webbrowser.get(chrome_path).open('file://' + filepath)
    #webbrowser.open('file:\\' + filepath)
