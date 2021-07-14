import gmplot
import webbrowser


# Google GENERAL MAPS API key - works for maps_javascript_api & directions_api

def map_vrp_routes(route_array, stop_data, gmaps_api_key):

    for route in route_array:

        origin = (stop_data.loc[route[0], 'latitude'], stop_data.loc[route[0], 'longitude'])
        print(origin)


    '''gmap = gmplot.GoogleMapPlotter(43.04955, -89.39237, 15, apikey=gmaps_api_key)
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
    # webbrowser.open('file:\\' + filepath)'''




