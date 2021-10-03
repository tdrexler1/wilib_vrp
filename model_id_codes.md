## Model ID Codes

Model IDs comprise five components separated by underscores. Each component describes a characteristic of the model, its parameters, or the solution strategies used by the Google OR-Tools routing solver. A list of the possible component values and their meanings follows.

**Component 1** – Public Library System Redesign Delivery Workgroup proposal and region number
  *	possible values: 
    *	'idlX' – 'idl' = Delivery Workgroup ideal proposal, X = region number
    *	'strX' – 'str' = Delivery Workgroup starting point proposal, X = region number

**Component 2** – maximum route length parameter
  *	possible values:
    *	'08' = 8 hours
    *	'10' = 10 hours

**Component 3** – Google OR-Tools routing solver first solution strategy ("Routing Options | OR-Tools," n.d.)
  *	possible values:
    *	'01' = PATH_CHEAPEST_ARC
    *	'02' = SAVINGS
    *	'03' = SWEEP
    *	'04' = CHRISTOFIDES
    *	'05' = PARALLEL_CHEAPEST_INSERTION
    *	'06' = LOCAL_CHEAPEST_INSERTION
    *	'07' = GLOBAL_CHEAPEST_ARC
    *	'08' = LOCAL_CHEAPEST_ARC
    *	'09' = FIRST_UNBOUND_MIN_VALUE
    *	'10' = AUTOMATIC

**Component 4** – Google OR-Tools routing solver local search metaheuristic ("Routing Options | OR-Tools," n.d.)
  *	possible values:
    *	'01' = GREEDY_DESCENT
    *	'02' = GUIDED_LOCAL_SEARCH
    *	'03' = SIMULATED_ANNEALING
    *	'04' = TABU_SEARCH
    *	'05' = AUTOMATIC

**Component 5** – vehicle capacity parameter
  *	possible values:
    *	'040' = 40 containers
    *	'060' = 60 containers
    *	'200' = 200 containers
    *	'000' = capacity constraint removed
