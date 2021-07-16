from gmplot.utility import _get_value, _INDENT_LEVEL
from gmplot.gmplot import _format_LatLng
from gmplot.gmplot import _MarkerIcon
from gmplot.gmplot import _Marker
from gmplot.gmplot import _MarkerInfoWindow

import json

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


class _MarkerInfoWindow_mod(object):
    def __init__(self, marker_name, content):
        '''
        Args:
            marker_name (str): JavaScript name of the marker that should display this info window.
            content (str): HTML content to be displayed in this info window.
        '''
        self._marker_name = marker_name
        self._content = content

    def write(self, w, info_marker_index):
        '''
        Write the info window that attaches to the given marker on click.

        Args:
            w (_Writer): Writer used to write the info window.
            info_marker_index (int): Index of this info window.
        '''
        w.write('''
        var {info_window_name} = new google.maps.InfoWindow({{
            content: '{content}'
        }});

        {marker_name}.addListener('click', function() {{
            {info_window_name}.open(map, {marker_name});
        }});

        google.maps.event.addListener({marker_name}, 'click', function(){{
            if( prev_infowindow ){{
                prev_infowindow.close();
            }}

            {info_window_name}.open(map, {marker_name});
            prev_infowindow = {info_window_name}

        }});

        '''.format(
            info_window_name='info_window_%d' % info_marker_index,
            marker_name=self._marker_name,
            content=self._content.replace("'", "\\'").replace("\n", "\\n")  # (escape single quotes and newlines)
        ))
        w.write()

# GoogleMapPlotter
def write_point(self, w, lat, lng, color, title, precision, color_cache, label, info_window=None, draggable=None): # TODO: Bundle args into some Point or Marker class (counts as an API change).
    # Write the marker icon (if it isn't written already).
    marker_icon = _MarkerIcon(color)
    marker_icon.write(w, color_cache)

    # If this marker should have an info window, give it a unique name:
    marker_name = ('info_marker_%d' % self._num_info_markers) if info_window is not None else None

    # Write the actual marker:
    marker = _Marker(_format_LatLng(lat, lng, precision), name=marker_name, title=title, label=label, icon=marker_icon.name, draggable=draggable)
    marker.write(w)

    # Write the marker's info window, if specified:
    if info_window is not None:
        marker_info_window = _MarkerInfoWindow_mod(marker_name, info_window)
        marker_info_window.write(w, self._num_info_markers)
        self._num_info_markers += 1

    # TODO: When Point-writing is pulled into its own class, move _MarkerIcon, _Marker, and _MarkerInfoWindow initialization into _Point's constructor.


# GoogleMapPlotter
def write_map(self, w):
    w.write('var map = new google.maps.Map(document.getElementById("map_canvas"), {')
    w.indent()
    if self._map_styles:
        w.write('styles: %s,' % json.dumps(self._map_styles, indent=_INDENT_LEVEL))
    if self.map_type:
        w.write('mapTypeId: "%s",' % self.map_type.lower())
    if self._tilt is not None:
        w.write('tilt: %d,' % self._tilt)
    if self._scale_control:
        w.write('scaleControl: true,')
    w.write('zoom: %d,' % self.zoom)
    w.write('center: %s' % _format_LatLng(self.center[0], self.center[1]))
    w.dedent()
    w.write('});')
    w.write()
    #***
    w.write('var prev_infowindow = false;')
    w.write()
    #***
    if self._fit_bounds:
        w.write('map.fitBounds(%s);' % json.dumps(self._fit_bounds))
        w.write()

# GoogleMapPlotter
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