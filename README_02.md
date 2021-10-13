# Wisconsin Library Delivery Services & the Vehicle Routing Problem: A Case Study

In this project, I set up Vehicle Routing Problems (VRPs) to investigate the feasibility of regional library delivery routes. The VRP models were based on regional delivery service reconfigurations proposed by the Delivery Workgroup of the Wisconsin [Public Library System Redesign](https://dpi.wi.gov/coland/plsr-update) (PLSR) Project.

This was my Capstone Project for the [University of Wisconsin Data Science Master&#39;s Degree](https://datasciencedegree.wisconsin.edu/), which I completed in summer 2021.

## Overview

In their report, the PLSR [Delivery Workgroup](https://dpi.wi.gov/sites/default/files/imce/coland/pdf/PLSR_-_Delivery_Workgroup_Report.pdf) included "ideal" and "starter" proposals for redesigning statewide delivery library services. I modeled each of 15 regions in these models using the [vehicle routing solver](https://developers.google.com/optimization/routing) from the Google OR-Tools package.

In each regional VRP, all the routes started from and ended at the same depot while stopping once at every public, academic, school, and special library in the region. I configured the solver to evaluate the cost of each route by its duration and attempt to minimize the total route time for all vehicles.

For detailed descriptions

## Research Questions

1. Is there a feasible route structure for each region where every library receives one stop, and each route takes less than the maximum suggested route time (8-10 hours)?
2. For instances in which a feasible model exists, what is a route configuration that minimizes the cumulative route time of all vehicles?
3. What are the parameter values of an optimal regional route structure, particularly the number of vehicles required and the maximum allowed route time? Is it possible to find other optimal or near-optimal route configurations by changing the value of those parameters?

## Project Code

I wrote the project code using Python 3.9. I based my scripts on the examples in the [Google's online guide](https://developers.google.com/optimization/routing) to vehicle routing problems. I set up the [main program](wi_lib_vrp.py) to run from the command line with arguments to select the model region, set the VRP parameters, pick the solver metaheuristic and local search strategies, and choose from among multiple options for solution output.

I included an additional feature that allows the program to automatically increment the number of vehicles/routes if it is unable to find a feasible solution to the VRP using the initial parameters. The solver continues until it either finds a solution or reaches the maximum fleet size of 15 vehicles.

Further details regarding the project code and other files can be found in the  [file_descriptions.md](file_descriptions.md) document.

## Data Sources

I downloaded address data for public libraries from the Wisconsin Department of Public Instruction [Public Library Directory](https://dpi.wi.gov/pld/directories/directory) as an Excel file. I added data for academic, school, and special libraries based on information from their websites and Google Maps. I also used Google Maps to verify each location or, if necessary, obtain a Google PlusCode to substitute for libraries with mismatched addresses.

To create the distance and duration matrices for the OR-Tools solver, I used the Matrix API from [openrouteservice](https://openrouteservice.org/), which provides real-world, along-the-road data. I wrote a [utility program](wi_lib_vrp_matrix_build.py) to collect and store the matrix data as [pickle files](vrp_matrix_data) to minimize the number of API calls I had to make. If necessary, the functions in this program can also be called from the main script to generate the matrices at run time.

## Output Options

I developed four options for VRP solution output:

1. print the solution to the terminal;
2. store the solution as a [text file](vrp_output/solution_files);
3. visualize the routes [plotted on a Google Map](vrp_output/map_files); and
4. create a [screenshot](vrp_output/screenshots) of the map and save it as a PNG file.

Examples of the latter three options are included in the [vrp_output](vrp_output) subdirectories. To save space, the map files and screenshots are limited to model variants with no vehicle capacity constraints; the text files contain complete solutions for all the models I ran for this project. I've written a [brief guide](model_id_codes.md) to explain the codes in the output file names.

To create the route map visualizations, I used the [gmplot](https://pypi.org/project/gmplot/) package. To get the results I wanted, I found I needed to modify some of the JavaScript

