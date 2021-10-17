# Wisconsin Library Delivery Services & the Vehicle Routing Problem: A Case Study

In this project, I used [Vehicle Routing Problems](https://www.wikiwand.com/en/Vehicle_routing_problem) (VRPs) to model library delivery service route structures and investigate their feasibility. I based the VRPs on proposals developed by the [Delivery Workgroup](https://dpi.wi.gov/sites/default/files/imce/coland/pdf/PLSR_-_Delivery_Workgroup_Report.pdf) of the Wisconsin [Public Library System Redesign](https://dpi.wi.gov/coland/plsr-update) (PLSR) Project. The Workgroup designed their proposals to shift the statewide library delivery service from its current, centralized configuration toward a region-based model.

This was my Capstone Project for the [University of Wisconsin Data Science Master&#39;s Degree](https://datasciencedegree.wisconsin.edu/), which I completed in August 2021.

What follows is a brief project summary. I've also uploaded a copy of my [final project report](WI_Library_Delivery_Services_and_the_Vehicle_Routing_Problem.pdf) to this repository for any readers interested in the details of my research approach, methodology, and results.

## Overview

The PLSR Delivery Workgroup included two proposals in [their report](https://dpi.wi.gov/sites/default/files/imce/coland/pdf/PLSR_-_Delivery_Workgroup_Report.pdf): an "ideal" model and a "starter" model. For my project, I modeled all 15 regions from both of these proposals using the [vehicle routing solver](https://developers.google.com/optimization/routing) in the Google OR-Tools package for Python.

I set up each regional VRP so that every public, academic, school, and special library in the local service area received exactly one stop from only one vehicle in the delivery fleet. All the vehicles started and ended their routes at a single depot located in the region. I configured the solver to evaluate the cost of each route by its total duration and minimize the sum of route times for all vehicles. I then solved the VRPs multiple times using different combinations of metaheuristics, local search strategies, and values for vehicle capacity constraints.

## Research Questions

1. Is there a feasible route structure for each region where every library receives one stop, and each route takes less than the maximum route time suggested by the PLSR Delivery Workgroup (8-10 hours)?
2. For instances in which a feasible model exists, what is a route configuration that minimizes the cumulative route time of all vehicles?
3. What are the parameter values of an optimal regional route structure, particularly the number of vehicles required and the maximum allowed route time? Is it possible to find other optimal or near-optimal route configurations by changing the value of those parameters?

## Project Code

I wrote the project code using Python (3.9). I based my scripts on the examples in the [Google's online guide](https://developers.google.com/optimization/routing) to vehicle routing problems. I set up the [main program](wi_lib_vrp.py) to run from the command line with arguments to select the model region, set the VRP parameters, pick the solver metaheuristic and local search strategies, and choose from among multiple options for solution output.

I designed the program with an optional feature that automatically attempts to re-solve a VRP if the OR-Tools solver doesn't find a feasible solution with the initial parameter values. The program incrementally increases the number of vehicles in the regional fleet before each re-try, continuing until it either finds a solution or reaches a maximum of 15 vehicles.

The [file_descriptions.md](file_descriptions.md) document includes further details on the project code and other files included in this repository.

## Data Sources

The input data for the OR-Tools routing solver consisted of [distance and duration matrices](https://www.wikiwand.com/en/Distance_matrix#:~:text=In%20mathematics%2C%20computer%20science%20and,may%20not%20be%20a%20metric.) based on location data for each stop. I started collecting data by downloading public library addresses from the Wisconsin Department of Public Instruction [Public Library Directory](https://dpi.wi.gov/pld/directories/directory) as an Excel file. I then added addresses for academic, school, and special libraries based on information from their websites and Google Maps. I also used Google Maps to manually verify that each location matched the address data; if not, I substituted a Google PlusCode for a street address. Finally, I wrote a [short script](wi_lib_vrp_finalize_data.py) to geocode the addresses and assign each library to a region.

To create the distance and duration matrices, I used the Matrix API from [openrouteservice](https://openrouteservice.org/), which provides real-world, along-the-road measurements. I wrote a [utility program](wi_lib_vrp_matrix_build.py) to collect and store the matrix data as [pickle files](vrp_matrix_data), minimizing the number of API calls required. If needed, the functions in this program can also be called from the main script to generate the matrices at run time.

## Output Options

I developed four options for VRP solution output:

1. display the solution on the screen;
2. store the solution as a [text file](vrp_output/solution_files);
3. visualize the routes [on a map](vrp_output/map_files); and
4. create a [screenshot](vrp_output/screenshots) of the map and save it as a PNG file.

I created the route maps with the [gmplot](https://pypi.org/project/gmplot/) package for Python. Gmplot uses the [Google Maps JavaScript API](https://developers.google.com/maps/documentation/javascript/overview) to draw location markers and route directions (as well as other objects) on a Google Map. With minor modifications to the JavaScript generated by the package, I was able to get the map results I wanted showing the order of the stops for each route.

I've included examples of solution text files, route maps, and screenshots in the [vrp_output](vrp_output) subdirectories. The map files and screenshots are limited to model variants with no vehicle capacity constraints to save storage space, but the text files contain complete solutions for all the models I ran for this project. I've written a [guide to explain](model_id_codes.md) the codes I used to name the output files.


