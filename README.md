# Wisconsin Library Delivery Services & the Vehicle Routing Problem: A Case Study

Using Vehicle Routing Problems (VRPs) to analyze the feasibility of statewide library delivery service reconfiguration proposals from the [Delivery Workgroup](https://dpi.wi.gov/sites/default/files/imce/coland/pdf/PLSR_-_Delivery_Workgroup_Report.pdf) of the Wisconsin [Public Library System Redesign](https://dpi.wi.gov/coland/plsr-update) (PLSR) Project.

This was my Capstone Project for the [University of Wisconsin Data Science Master&#39;s Degree](https://datasciencedegree.wisconsin.edu/), which I completed in summer 2021.

## Overview

For this project, I used the [vehicle routing solver](https://developers.google.com/optimization/routing) from the Google OR-Tools package to optimize delivery routes for a set of regional service territories. The territories were based on the proposed service models included in the PLSR [Delivery Workgroup Report](https://dpi.wi.gov/sites/default/files/imce/coland/pdf/PLSR_-_Delivery_Workgroup_Report.pdf). I modeled regions from both the "ideal" and "starter" proposals, creating a total of 15 VRPs.

In each regional VRP, delivery vehicle routes start and end at the same depot, with one service stop at every public, academic, school, and special library in the region. The cost of each route is evaluated by measuring its duration, with additional constraints on vehicle capacity and maximum route distance.

## Code & Functionality

I based the project code on the Python examples from Google's online guide to [vehicle routing problems](https://developers.google.com/optimization/routing). The [main script](wi_lib_vrp.py) is designed to run from the command line with arguments to select the regional model, list the VRP parameters, pick the solver strategies, and choose multiple options for solution output. An additional feature allows users to either specify the size of the regional fleet or let the program iteratively determine the minimum number of vehicles required to produce a feasible solution.

The ["file_descriptions.md"](file_descriptions.md) document describes the project code and other files in greater detail.

## Data Sources

For public libraries, I downloaded address data from the Wisconsin Department of Public Instruction [Public Library Directory](https://dpi.wi.gov/pld/directories/directory). I then added addresses (or, in some cases, PlusCodes) for academic, school, and special libraries manually using library websites and Google Maps.

To create the distance and duration matrices used by the OR-Tools solver, I utilized the Matrix API from [openrouteservice](https://openrouteservice.org/) which provides real-world, along-the-road data. I wrote a [utility script](wi_lib_vrp_matrix_build.py) that can store the matrix data as [pickle files](vrp_matrix_data) to minimize API calls. If necessary, the functions can also be called from the main script to generate the matrices at run time.

## Output Options

I included four options for VRP solution output:

1. display the solution on the terminal;
2. store the solution as a [text file](vrp_output/solution_files);
3. visualize the solution [plotted on Google Maps](vrp_output/map_files); and
4. create a [screenshot](vrp_output/screenshots) of the map plot saved as a PNG file.

Examples of the latter three options are included in the [vrp_output](vrp_output) subdirectories. To save space, the map files and screenshots are limited to model variants with no vehicle capacity constraints; the text files contain complete solutions for all the models I ran for this project. I've written a [brief guide](model_id_codes.md) to explain the codes used in the output file names.

<!-- TODO: edit/revise main readme -->
<!-- TODO: upload final report PDF with reasonable file name -->
<!-- TODO: upload any other project files? -->
<!-- TODO: update file_descriptions.md -->
