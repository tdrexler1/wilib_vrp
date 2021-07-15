import gmplot
from gmplot import _Route
import webbrowser

# TODO: need to override class _Route(object)
def write_mod(self, w):
    '''
    Write the route.

    Args:
        w (_Writer): Writer used to write the route.
    '''
    w.write('new google.maps.DirectionsService().route({')
    w.indent()
    w.write('origin: %s,' % self._origin)
    w.write('destination: %s,' % self._destination)
    if self._waypoints:
        w.write('waypoints: [')
        w.indent()
        ##
        [w.write('{location: %s, stopover: true},' % waypoint) for waypoint in self._waypoints]
        w.dedent()
        w.write('],')
    w.write('travelMode: "%s"' % self._travel_mode)
    w.dedent()
    ##
    w.write('''  
            }, function(response, status) {
                if (status == google.maps.DirectionsStatus.OK) {
                    new google.maps.DirectionsRenderer({
						map: map, polylineOptions: {
							strokeColor: "%s"
						} 
					}).setDirections(response);
                }
            });
        ''' % self._route_color)
    w.write()





# Google GENERAL MAPS API key - works for maps_javascript_api & directions_api

def map_vrp_routes(route_array, stop_data, gmaps_api_key):
    gmplot._Route.write = write_mod
    gmap = gmplot.GoogleMapPlotter(43.04955, -89.39237, 15, apikey=gmaps_api_key)
    route_colors = ['blue', 'green', 'red']

    for n, route in enumerate(route_array):

        origin = (float(stop_data.loc[route[0], 'latitude']), float(stop_data.loc[route[0], 'longitude']))
        destination = (float(stop_data.loc[route[-1], 'latitude']), float(stop_data.loc[route[-1], 'longitude']))
        waypoints_list = \
            [(float(stop_data.loc[x, 'latitude']), float(stop_data.loc[x, 'longitude'])) for x in route[1:-2]]

        gmap.directions(origin, destination, waypoints=waypoints_list, route_color=route_colors[n])

    gmap.draw('gmap.html')

    filepath = 'C:/Users/tdrex/PycharmProjects/wilib_vrp/gmap.html'

    # https://stackoverflow.com/questions/22445217/python-webbrowser-open-to-open-chrome-browser
    chrome_path = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s'
    webbrowser.get(chrome_path).open('file:\\' + filepath)
    # webbrowser.open('file:\\' + filepath)





