# wilib_vrp
Vehicle Routing Problems with time and capacity constraints. Modeling regional delivery hub proposals from the [Delivery Workgroup Report](https://dpi.wi.gov/sites/default/files/imce/coland/pdf/PLSR_-_Delivery_Workgroup_Report.pdf) of the [Wisconsin Public Library System Redesign Project](https://dpi.wi.gov/coland/plsr-update).

This is my Capstone Project for the [University of Wisconsin Data Science Master's Degree](https://datasciencedegree.wisconsin.edu/), completed in summer of 2021.

The project uses the [Vehicle Routing solver](https://developers.google.com/optimization/routing) included in the Google OR-Tools package to find an optimal set of routes for multiple delivery vehicles. In this case, the route stops represent libraries (public, academic, etc.) in the proposed service region, with all routes originating from and returning to a single hub. The primary constraint for each Vehicle Routing Problem (VRP) was time, with additional constraints on maximum route distance and vehicle capacity. The project goal was to solve the regional VRPs by incrementing the number of vehicles in the delivery fleet until a feasible solution was identified.
