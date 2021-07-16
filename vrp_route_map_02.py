import gmplot
import webbrowser
import string

# TODO: need to override class _Route(object)
##from gmplot.gmplot import _Route
from route_mod_class import _Route_mod
from gmplot.gmplot import GoogleMapPlotter

def directions(self, origin, destination, **kwargs):
    '''
    Display directions from an origin to a destination.

    Requires `Directions API`_.

    Args:
        origin ((float, float)): Origin, in latitude/longitude.
        destination ((float, float)): Destination, in latitude/longitude.

    Optional:

    Args:
        travel_mode (str): `Travel mode`_. Defaults to 'DRIVING'.
        waypoints ([(float, float)]): Waypoints to pass through.

    .. _Directions API: https://console.cloud.google.com/marketplace/details/google/directions-backend.googleapis.com
    .. _Travel mode: https://developers.google.com/maps/documentation/javascript/directions#TravelModes

    Usage::

        import gmplot
        apikey = '' # (your API key here)
        gmap = gmplot.GoogleMapPlotter(37.766956, -122.438481, 13, apikey=apikey)

        gmap.directions(
            (37.799001, -122.442692),
            (37.832183, -122.477914),
            waypoints=[
                (37.801036, -122.434586),
                (37.805461, -122.437262)
            ]
        )

        gmap.draw('map.html')

    .. image:: GoogleMapPlotter.directions.png
    '''
    self._routes.append(_Route_mod(origin, destination, **kwargs))


# Google GENERAL MAPS API key - works for maps_javascript_api & directions_api

def map_vrp_routes(route_array, stop_data, gmaps_api_key):

    #_Route.write = write_mod
    GoogleMapPlotter.directions = directions

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




# pretty sure I can delete this
# def write_mod(self, w):
#     '''
#     Write the route.
#
#     Args:
#         w (_Writer): Writer used to write the route.
#     '''
#     w.write('new google.maps.DirectionsService().route({')
#     w.indent()
#     w.write('origin: %s,' % self._origin)
#     w.write('destination: %s,' % self._destination)
#     if self._waypoints:
#         w.write('waypoints: [')
#         w.indent()
#         #***
#         [w.write('{location: %s, stopover: true},' % waypoint) for waypoint in self._waypoints]
#         w.dedent()
#         w.write('],')
#     w.write('travelMode: "%s"' % self._travel_mode)
#     w.dedent()
#     #***
#     w.write('''
#             }, function(response, status) {
#                 if (status == google.maps.DirectionsStatus.OK) {
#                     new google.maps.DirectionsRenderer({
# 						map: map, polylineOptions: {
# 							strokeColor: "%s"
# 						}
# 					}).setDirections(response);
#                 }
#             });
#         ''' % self._route_color)
#     w.write()