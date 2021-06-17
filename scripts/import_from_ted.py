"""
MetAlert Search : Scripts - download (and import) data from TED
===================================

Copyright 2021 MET Norway

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import logging
from re import finditer
import sys
import textwrap
import mysql.connector

from collections.abc import Iterable

# needed for some additional funcitons only
import numpy as np
import json

logging.basicConfig(level="INFO")

def ted_to_geojson(tedids, properties=None):
    """
    Args:
        tedids (List(int)): List of Ted ids
        properties (dict, optional): Properties (Metadata) to be added.
            Potentially not interpreted in external codes.

    Returns:
        (dict): Data as a geoJSON FeatureCollection
    """
    if not isinstance(tedids, Iterable):
        raise TypeError("Query has to be a list.")

    areas = get_elements(ted_ids, cursor)
    [apply_fun_to_dictkey(d, fun=ted_coords_to_lonlat, key="corners")
        for d in areas]

    features = [feature_dict(area) for area in areas]
    collection = {
      "type": "FeatureCollection",
      "features": features
    }
    if properties is not None:
        collection["properties"] = properties
    return collection

def feature_dict(entry):
    """ Template dictionary for JSON feature from TED entry"""
    corners = [*entry["corners"], entry["corners"][0]] # create Linear Ring
    feature = {
    "type": "Feature",
    "geometry": {
        "type": "Polygon",
        "coordinates": [corners]
        },
    "properties": {
        "name": entry["name"],
        "ted-id": entry["id"],
        "description": entry["type"]
        }
    }
    return feature


def ted_coords_to_lonlat(coords):
    """ Transform coordinates from ted to (lon, lat).

    Args:
        coords (str): String of coordinates from the ted database e.g.
            "100 500:400 300: ..." given as "ilon0 ilat0: ilon1 ilat1: ...".

    Returns:
        list(tuple(float, float)): Coordinates as a list of (lon, lat) tuples in
            decimal degrees.
    """
    coords = coords.split(':')
    logging.debug('%s corners', len(coords))
    result = [_ted_to_decimal_degrees(point.split()) for point in coords]
    return result

def apply_fun_to_dictkey(dic, fun=ted_coords_to_lonlat, key="corner"):
    dic[key] = fun(dic[key])

def _ted_to_decimal_degrees(ted_tuple):
    """Converts ted to decimal degrees.

    Note:
        TED uses some integer representation unknown to me; found this code
        in `autotext`, and it works.

    Args:
        ted_tuple (Tuple[str, str]): Tuple of coordinates from TED

    Returns:
        Tuple[float, float]: Coordinates in decimal degrees
    """
    if len(ted_tuple) != 2:
        raise ValueError(f"Wrong format of {ted_tuple}")
    ted_tuple = [int(i) for i in ted_tuple]
    return tuple([int(i / 10000) + float(i % 10000) / 6000 for i in ted_tuple])
    # TODO: four decimal points only

def get_query(tedids, args="name,id,corners,type"):
    """Building a ted query, based on the ted-ids

    Args:
        tedids (List(int)): List of Ted ids
        args (str): Entry types to ask for in query, comma separated

    Returns:
        (str): mysql query for ted, querying args
    """
    if not isinstance(tedids, Iterable):
        raise TypeError("Query has to be a list.")
    query = f'select {args} from location where id in ({{}});'
    id_str = ",".join([f'"{i}"' for i in tedids])
    return query.format(id_str)

def get_elements(tedids, cursor, args="name,id,corners,type"):
    """Get elements from database

    Args:
        tedid (List(int)): List of Ted ids
        cursor: MySQL cursor
        args (str): Entry types to ask for in query, comma separated

    Returns:
        List[dict]: Values from database
    """
    if not isinstance(tedids, Iterable):
        raise TypeError("Query has to be a list.")
    query = get_query(tedids)
    cursor.execute(query)
    db_results = cursor.fetchall()

    result = []
    for item in db_results:
        res = {arg: item[i] for i, arg in enumerate(args.split(","))}
        result.append(res)

    return result

def plot_json(fn):
    """Plot json input from file."""
    import geopandas as gpd
    import contextily as ctx

    import matplotlib.pyplot as plt
    # from shapely.geometry import Polygon

    df = gpd.read_file(finditer)
    ax = df.plot(figsize=(10, 10), alpha=0.5, edgecolor='k')
    ctx.add_basemap(ax, crs=df.crs)
    plt.show()

def main():
    """
    Usage:
        python file.py [ted-id file] [fnout]
        - ted-id file contains ted ids separated by ':'
    """
    if len(sys.argv) != 3:
        raise RuntimeError("See Readme.")
    fntedid = sys.argv[1]

    try:
        # providing an arb. unknown user gives read-access
        gate = mysql.connector.connect(user='metsearch', password='',
                                       host='ted-b',
                                       database='ted',
                                       charset='utf8')
        cursor = gate.cursor()
        ted_ids = np.loadtxt(fntedid, delimiter=":", dtype=str)
        areas = ted_to_geojson(ted_ids)
        with open(sys.argv[2], 'w') as fout:
            json.dump(areas, fout)

    except mysql.connector.Error as err:
        print("Database Exception {} ".format(err))
    else:
        gate.close()


if __name__ == "__main__":
    main()
    # plot_json(sys.argv[1])
