from gmplot.utility import _get_value
from gmplot.gmplot import _format_LatLng

class _Route_mod(object):
    '''For more info, see Google Maps' `Directions Service https://developers.google.com/maps/documentation/javascript/directions`_.'''

    def __init__(self, origin, destination, **kwargs):
        '''
        Args:
            origin ((float, float)): Origin, as a latitude/longitude tuple.
            destination ((float, float)): Destination, as a latitude/longitude tuple.

        Optional:

        Args:
            travel_mode (str): Travel mode. Defaults to 'DRIVING'.
            waypoints ([(float, float)]): Waypoints.
        '''
        self._origin = _format_LatLng(*origin)
        self._destination = _format_LatLng(*destination)
        self._travel_mode = _get_value(kwargs, ['travel_mode'], 'DRIVING').upper()
        self._waypoints = [_format_LatLng(*waypoint) for waypoint in _get_value(kwargs, ['waypoints'], [])]

        # ***
        self._route_color = _get_value(kwargs, ['route_color'], 'blue').lower()




    def write(self, w):
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
            [w.write('{location: %s, stopover: true},' % waypoint) for waypoint in self._waypoints]  # ***
            w.dedent()
            w.write('],')
        w.write('travelMode: "%s"' % self._travel_mode)
        w.dedent()
        # ***
        # add color option for route lines, suppress directions markers: https://stackoverflow.com/a/24653283
        w.write('''  
                    }, function(response, status) {
                        if (status == google.maps.DirectionsStatus.OK) {
                            new google.maps.DirectionsRenderer({
        						map: map, polylineOptions: {
        							strokeColor: "%s"
        						}, suppressMarkers: true 
        					}).setDirections(response);
                        }
                    });
                ''' % self._route_color)
        w.write()