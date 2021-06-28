import folium
import webbrowser
import os
import gmplot
import yaml

#filepath = 'C:\\Users\\zzzlib\\PycharmProjects\\wilib_vrp\\map.html'

#map_osm = folium.Map(location=[43.04955, -89.39237], zoom_start=20)
#map_osm.save(filepath)
#webbrowser.open('file:\\' + filepath)

# Google GENERAL MAPS API key

try:
    with open(os.path.expanduser('~/google_maps_api_key.yml'), 'r') as conf:
        conf_data = yaml.full_load(conf)
        maps_javascript_api_key = conf_data['google_maps']['maps_javascript_api_key']
        directions_api_key = conf_data['google_maps']['directions_api_key']
        geocoding_api_key = conf_data['google_maps']['geocoding_api_key']
        general_maps_api_key = conf_data['google_maps']['general_maps_api_key']
except OSError as e:
    print(e)

origin = gmplot.GoogleMapPlotter.geocode('1601 Gilson St, Madison, WI 53715', apikey=geocoding_api_key)
destination = gmplot.GoogleMapPlotter.geocode('430 E High St, Milton, WI 53563', apikey=geocoding_api_key)
waypoint_01 = gmplot.GoogleMapPlotter.geocode('605 Eclipse Blvd, Beloit, WI 53511', apikey=geocoding_api_key)
waypoint_02 = gmplot.GoogleMapPlotter.geocode('316 S Main St, Janesville, WI 53545', apikey=geocoding_api_key)
#print(f'origin: {origin}, destination: {destination}')
#print(f'waypoint_01: {waypoint_01}, waypoint_02: {waypoint_02}')

#origin: (43.0495234, -89.39236960000001), destination: (42.7735095, -88.94400519999999)
#waypoint_01: (42.5194485, -89.0312247), waypoint_02: (42.6791323, -89.01897869999999)

gmap = gmplot.GoogleMapPlotter(43.04955, -89.39237, 15, apikey=general_maps_api_key)
gmap.directions(
    origin,
    destination,
    waypoints=[
        waypoint_01,
        waypoint_02
    ],
    route_color='blue'
)
gmap.directions(
    waypoint_02,
    origin,
    waypoints=[
        destination,
        waypoint_01
    ],
    route_color='green'
)

gmap.draw("gmap.html")

filepath = 'C:/Users/tdrex/PycharmProjects/wilib_vrp/gmap.html'

# https://stackoverflow.com/questions/22445217/python-webbrowser-open-to-open-chrome-browser
chrome_path = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s'
webbrowser.get(chrome_path).open('file:\\' + filepath)
#webbrowser.open('file:\\' + filepath)