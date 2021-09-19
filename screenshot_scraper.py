import time
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options  # chromedriver must be in PATH

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# DONE: experiment with image size for each region; automate
# TODO: copy relevant code to wi_lib_vrp_route_viz.py
# DONE: create screenshots for each map; are these files a reasonable size? Not really - limit Github post to sampling

def screenshot_map(route_map, output_dir):
    """
    Uses a headless Chrome browser to open Google Map file and take a screenshot,
    saved as a PNG image file.

    * Note: requires 'chromedriver' for 'selenium' package, which must be added to PATH

    :param route_map: HTML file of Google Map with routes & stop markers.
    :type route_map: HTML file
    :param output_dir: Path to directory where PNG image files will be saved.
    :type output_dir: str
    """

    # Selenium documentation:
    # https://selenium-python.readthedocs.io/index.html
    # https://www.selenium.dev/selenium/docs/api/py/index.html
    # https://www.selenium.dev/documentation/

    # configure headless Chrome browser
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    # construct output file name from map file name
    png_filepath = output_dir + os.path.basename(route_map)[:-4] + 'png'

    # use selenium webdriver to open map file & save screenshot
    driver = webdriver.Chrome(options=chrome_options)

    win_size_dict = {
        'idl1': (600, 750),
        'idl2': (500, 650),
        'idl3': (1000, 1000),
        'idl4': (900, 900),
        'idl5': (850, 650),
        'idl6': (950, 700),
        'idl7': (1000, 850),
        'str1': (750, 500),
        'str2': (900, 800),
        'str3': (900, 900),
        'str4': (1000, 1000),
        'str5': (800, 800),
        'str6': (850, 650),
        'str7': (500, 650),
        'str8': (700, 500)
    }
    map_region = os.path.basename(route_map)[0:4]
    #print(f'{map_region}, {win_size_dict[map_region][0]}, {win_size_dict[map_region][1]}, {type(win_size_dict[map_region][0])}')

    driver.set_window_size(win_size_dict[map_region][0], win_size_dict[map_region][1])
    #driver.set_window_size(1024, 768)
    #driver.set_window_size(800, 600)

    driver.get(route_map)
    # https://stackoverflow.com/a/27112797
    element_list = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, 'gmnoprint'))
    )
    element_list.append(driver.find_element_by_class_name('gm-fullscreen-control'))

    for delete_element in element_list:

        try:
            # https://stackoverflow.com/q/22515012
            driver.execute_script("""
            var element = arguments[0];
            element.parentNode.removeChild(element);
            """, delete_element)

        except:
            # https://stackoverflow.com/a/36013523, https://www.selenium.dev/exceptions/#stale_element_reference
            element_list.remove(delete_element)

    # https://stackoverflow.com/a/58264507, https://stackoverflow.com/a/58981854
    time.sleep(15)

    map_element = driver.find_element_by_id('map_canvas')
    map_element.screenshot(png_filepath)

vrp_output_path = '.\\vrp_output\\'

# construct output file path & create directory if necessary
screenshot_file_path = vrp_output_path + 'screenshots\\'

if not os.path.isdir(screenshot_file_path):
    os.makedirs(screenshot_file_path)

# generate PNG file
for map_file in os.listdir(vrp_output_path + 'map_files\\'):
    print(f'{map_file[:-5]}...', end='')
    route_map_filepath = os.path.abspath(vrp_output_path + 'map_files\\' + map_file)
    screenshot_map(route_map_filepath, screenshot_file_path)
    print(f'screenshot complete')


# map_file = 'idl5_10_05_05_200.html'
# route_map_filepath = os.path.abspath(vrp_output_path + 'map_files\\' + map_file)
# screenshot_map(route_map_filepath, screenshot_file_path)