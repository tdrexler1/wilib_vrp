SETLOCAL EnableDelayedExpansion
FOR %%G IN (40, 60, 200, 0) DO (
    FOR %%H IN (8, 10) DO (
        FOR %%I IN (savings, christofides, parallel_cheapest_insertion, automatic) DO (
            python C:\Users\tdrex\PycharmProjects\wilib_vrp\wi_lib_vrp.py wi_library_directory_geo_reg.csv starter 1 duration 1 %%H 500 %%G 30 %%I automatic --vehicle_increment --text_file --map
        )
    )
)