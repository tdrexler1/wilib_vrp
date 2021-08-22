
from gmplot.gmplot import GoogleMapPlotter, _Route, _MarkerInfoWindow, _Marker

from gmplot.utility import _get_value, _INDENT_LEVEL
from gmplot.gmplot import _format_LatLng
from gmplot.gmplot import _MarkerIcon

import json

"""
Overwrite gmplot '_Route' class to accept keyword argument for route color (hex value or supported color name).

Adds DirectionsRenderer to Google Map to draw route polyline between stops. Allows options for color, line weight,
and opacity. Also suppresses default markers, which are replaced with gmplot markers in same locations. 
"""
class _Route_mod(_Route):

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
        							strokeColor: "%s",
        							strokeOpacity: 1.0,
        							strokeWeight: 3,
        						}, suppressMarkers: true 
        					}).setDirections(response);
                        }
                    });
                    
                    await new Promise(r => setTimeout(r, 500));
                ''' % self._route_color)
        w.write()


"""
Overwrite gmplot '_MarkerInfoWindow' class to add event listeners for marker clicks.

InfoWindow opens when marker is clicked and closes if another marker is clicked (only one InfoWindow open at a time). 
"""
class _MarkerInfoWindow_mod(_MarkerInfoWindow):
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


"""
Overwrite gmplot '_Marker' class to accept keyword arguments specifying marker label text color, font family,
font size, and font weight.

Allows adjustments to text color based on color of marker for readability.
"""
class _Marker_mod(_Marker):
    def __init__(self, position, **kwargs):
        '''
        Args:
            position (str): JavaScript code that represents the position of the marker.

        Optional:

        Args:
            name (str): JavaScript name of the marker.
            title (str): Hover-over title of the marker.
            label (str): Label displayed on the marker.
            icon (str): JavaScript code that represents the icon.
            draggable (bool): Whether or not the marker is draggable.
        '''
        self._position = position
        self._name = kwargs.get('name')
        self._title = kwargs.get('title')
        self._label = kwargs.get('label')
        self._icon = kwargs.get('icon')
        self._draggable = kwargs.get('draggable')
        self._label_color = kwargs.get('label_color')
        self._label_font_family = kwargs.get('label_font_family')
        self._label_font_size = kwargs.get('label_font_size')
        self._label_font_weight = kwargs.get('label_font_weight')

    def write(self, w):
        '''
        Write the marker.

        Args:
            w (_Writer): Writer used to write the marker.
        '''
        if self._name is not None: w.write('var %s = ' % self._name, end_in_newline=False)

        w.write('new google.maps.Marker({')
        w.indent()
        w.write('position: %s,' % self._position)

        if self._title is not None: w.write('title: "%s",' % self._title)
        if self._label is not None:
            w.write('label: {')
            w.indent()
            w.write('text: "%s",' % self._label)
            w.write('color: "%s",' % self._label_color)
            if self._label_font_family is not None:
                w.write('fontFamily: "%s"' % self._label_font_family)
            if self._label_font_size is not None:
                w.write('fontSize: "%s",' % self._label_font_size)
            if self._label_font_weight is not None:
                w.write('fontWeight: "%s"' % self._label_font_weight)
            w.dedent()
            w.write('},')
        if self._icon is not None: w.write('icon: %s,' % self._icon)
        if self._draggable is not None: w.write('draggable: %s,' % str(self._draggable).lower())

        w.write('map: map')
        w.dedent()
        w.write('});')
        w.write()
        # ***
        w.write('map_bounds.extend(%s);' % self._position)
        w.write()


class GoogleMapPlotter_mod(GoogleMapPlotter):
    """
    Overrides gmplot GoogleMapPlotter method to use '_Marker_mod' class and accept additional keyword arguments.
    """
    def write_point(self, w, lat, lng, color, title, precision, color_cache, label, info_window=None, draggable=None,
                    label_color=None, label_font_family=None, label_font_size=None, label_font_weight=None ): # TODO: Bundle args into some Point or Marker class (counts as an API change).

        # Write the marker icon (if it isn't written already).
        marker_icon = _MarkerIcon(color)
        marker_icon.write(w, color_cache)

        # If this marker should have an info window, give it a unique name:
        marker_name = ('info_marker_%d' % self._num_info_markers) if info_window is not None else None

        # Write the actual marker:
        marker = _Marker_mod(_format_LatLng(lat, lng, precision), name=marker_name, title=title, label=label,
                             icon=marker_icon.name, draggable=draggable,
                             label_color=label_color, label_font_family=label_font_family,
                             label_font_size=label_font_size, label_font_weight=label_font_weight)
        marker.write(w)

        # Write the marker's info window, if specified:
        if info_window is not None:
            marker_info_window = _MarkerInfoWindow_mod(marker_name, info_window)
            marker_info_window.write(w, self._num_info_markers)
            self._num_info_markers += 1

        # TODO: When Point-writing is pulled into its own class, move _MarkerIcon, _Marker, and _MarkerInfoWindow initialization into _Point's constructor.


    """
    Overrides gmplot GoogleMapPlotter method to accept additional keyword arguments for '_Marker_mod' class.
    """
    def marker(self, lat, lng, color='#FF0000', c=None, title=None, precision=6, label=None, **kwargs):
        '''
        Display a marker.

        Args:
            lat (float): Latitude of the marker.
            lng (float): Longitude of the marker.

        Optional:

        Args:
            color/c (str): Marker color. Can be hex ('#00FFFF'), named ('cyan'), or matplotlib-like ('c'). Defaults to red.
            title (str): Hover-over title of the marker.
            precision (int): Number of digits after the decimal to round to for lat/lng values. Defaults to 6.
            label (str): Label displayed on the marker.
            info_window (str): HTML content to be displayed in a pop-up `info window`_.
            draggable (bool): Whether or not the marker is `draggable`_.

        .. _info window: https://developers.google.com/maps/documentation/javascript/infowindows
        .. _draggable: https://developers.google.com/maps/documentation/javascript/markers#draggable

        Usage::

            import gmplot
            apikey = '' # (your API key here)
            gmap = gmplot.GoogleMapPlotter(37.766956, -122.438481, 13, apikey=apikey)

            gmap.marker(37.793575, -122.464334, label='H', info_window="<a href='https://www.presidio.gov/'>The Presidio</a>")
            gmap.marker(37.768442, -122.441472, color='green', title='Buena Vista Park')
            gmap.marker(37.783333, -122.439494, precision=2, color='#FFD700')

            gmap.draw('map.html')

        .. image:: GoogleMapPlotter.marker.png
        '''
        self.points.append(
            (lat, lng, c or color, title, precision, label, kwargs.get('info_window'), kwargs.get('draggable'),
             kwargs.get('label_color'), kwargs.get('label_font_family'), kwargs.get('label_font_size'), kwargs.get('label_font_weight')))


    """
    Overrides gmplot GoogleMapPlotter method to accept additional keyword arguments for '_Marker_mod' class.
    """
    def write_points(self, w, color_cache=set()):
        # TODO: Having a mutable set as a default parameter is done on purpose for backward compatibility.
        #       Should get rid of this in next major version (counts as an API change of course).
        self._num_info_markers = 0  # TODO: Instead of resetting the count here, point writing should be refactored into its own class (counts as an API change).
        for point in self.points:
            self.write_point(w, point[0], point[1], point[2], point[3], point[4], color_cache, point[5], point[6],
                             point[7], point[8], point[9], point[10], point[11])  # TODO: Not maintainable.


    """
    Overrides gmplot GoogleMapPlotter method to add JavaScript line initializing the 'prev_infowindow' variable, used
    to track whether a marker InfoWindow is currently open (see '_MarkerInfoWindow_mod' class above)
    """
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
        # ***
        w.write('var prev_infowindow = false;')
        w.write()
        w.write('var map_bounds = new google.maps.LatLngBounds();')
        w.write()

        # ***
        # if self._fit_bounds:
        #     w.write('map.fitBounds(%s);' % json.dumps(self._fit_bounds))
        #     w.write()


    """
    Overrides gmplot GoogleMapPlotter method to use '_Route_mod' class.
    """
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


    """
    Overrides gmplot GoogleMapPlotter method to allow timeouts between directions requests.
    """
    def _write_html(self, w):
        '''
        Write the HTML map.

        Args:
            w (_Writer): Writer used to write the HTML map.
        '''
        color_cache = set()

        w.write('''
            <html>
            <head>
            <meta name="viewport" content="initial-scale=1.0, user-scalable=no" />
            <meta http-equiv="content-type" content="text/html; charset=UTF-8" />
            <title>{title}</title>
            <script type="text/javascript" src="https://maps.googleapis.com/maps/api/js?libraries=visualization{key}"></script>
            <script type="text/javascript">
        '''.format(title=self.title, key=('&key=%s' % self.apikey if self.apikey else '')))
        w.indent()
        ###w.write('function initialize() {')
        w.write('async function initialize() {')
        w.indent()
        self.write_map(w)
        self.write_grids(w)
        self.write_points(w, color_cache)
        self.write_paths(w)
        self.write_symbols(w)
        self.write_shapes(w)
        self.write_heatmap(w)
        self.write_ground_overlay(w)
        [route.write(w) for route in self._routes]
        [text.write(w) for text in self._text_labels]
        if self._marker_dropper: self._marker_dropper.write(w, color_cache)
        # ***
        w.write('map.fitBounds(map_bounds);')
        w.write()
        # ***
        w.dedent()
        w.write('}')
        w.dedent()
        w.write('''
            </script>
            </head>
            <body style="margin:0px; padding:0px;" onload="initialize()">
                <div id="map_canvas" style="width: 100%; height: 100%;" />
            </body>
            </html>
        ''')