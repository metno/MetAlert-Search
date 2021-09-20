## Scripts

- Import of Polygons from other sources:


    - `import_from_ted.py`: Imports additional, MET defined polygons from TED database. Needs to be run on a machine
        where TED is available, and requires a list of colon separated TED ids. In the following example 
        we use `fjell.ids`a set of mountain regions in Norway: 
        ``` bash
        # fjell.ids
        0701:0702:0703:0705:0706:0707:0708:0710
        ```
        Run the script with following command: ``python import_from_ted.py fjell.ids``.

    - `import_from_kartverket.py`: Imports boundary data for administrative districts (kommuner and
         fylker) of Norway. Requires manual download of datasets. See function docstrings for more
         imformation.
