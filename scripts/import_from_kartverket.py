"""
MetAlert Search : Scripts - download (and import) data from kartverket
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

import json
import requests
import logging

# needed for some additional funcitons only
import pyproj

from shapely.geometry import shape, Point
from shapely.ops import transform

import geopandas as gpd

import matplotlib.pyplot as plt

logging.basicConfig(level="INFO")


def get_kartverket_data(coordsys_in=25833, coordsys_out=4326):
    """Transform Kartverket polygon data for Kommuner / Fylker

    The datasets have to be downloaded manually, see
    https://kartkatalog.geonorge.no/metadata?text=administrative%20grenser%20kommuner&organization=Kartverket
    or
    https://www.kartverket.no/api-og-data/grensedata

    Note:
        - The script assumes that one downloads the data as geoJSON. Due to
          limitations at the time of testing, it had to be downloaded as in
          the projection `EUREF89 UTM sone 33, 2d`, which corresponds to `EPSG
          code 25833`.
        - For historical data, see `Administrative enheter - historiske versjoner` at geonorge.

    Args:
        what (str): What information to get. Has to be in
            ["fylke", "kommune"]
        coordsys_in (int): Coordinate system of input as EPSG code. Default is
            25833, `EUREF89 UTM sone 33, 2d`
        coordsys_out (int): Coordinate system for output as EPSG code.
            Default is 4326, which is WGS84.

    Returns:
        (json): List of Json files with name, geometry, (...).

    """

    fn = "kartverket_data/Basisdata_0000_Norge_25833_Kommuner_GEOJSON.geojson"
    data = load_data(fn)

    crsin = pyproj.CRS(f'EPSG:{coordsys_in}')
    crsout = pyproj.CRS(f'EPSG:{coordsys_out}')

    # import geopandas
    # data = geopandas.read_file(fn) # doesn't work due to complexity

    df = gpd.GeoDataFrame.from_features(data['administrative_enheter.kommune']['features'], crs=crsin)
    df = df.to_crs(crsout)
    df["navn"] = df["navn"].apply(pd_convert_nested_name)
    df = df.dissolve(by='navn', as_index=False)

    return df


def pd_convert_nested_name(col):
    """Convert nested name from kartverket geoJSON to simple"""
    return col[0]["navn"]


def dump_data(request, fn='kartdata.json'):
    with open(fn, 'w') as f:
        json.dump(request, f, ensure_ascii=False)


def load_data(fn='kartdata.json'):
    with open(fn) as f:
        data = json.load(f)
    return data


# def find_multipolygons(data):
#     """ Find "true" multipolygons in kartverkets data.

#     Finds geoJson objects which more then one polygon in the same (
#     Multi)Polygon object

#     Args:
#         data (List[GeoJSON]) List of Fylke/Kommune geometries
#     """

#     for i, item in enumerate(data):
#         polygon = shape(item["omrade"])
#         if len(polygon.geoms) != 1:
#             if "fylkesnavn" in item:
#                 name_str = "fylkesnavn"
#             elif "kommunenavn" in item:
#                 name_str = "kommunenavn"
#             else:
#                 raise NotImplementedError
#             logging.info(f"{item[name_str]} (no. {i}) has {len(polygon.geoms)} polygons")


# def example_plot(sources):
#     """Example plot of Malik, a MultiPolygon and cal. of intersect. ratio"""
#     # example plot
#     i_data = 271
#     polygon1 = shape(sources["kommuner"][i_data]["omrade"])
#     for geom in polygon1.geoms:
#         plt.plot(*geom.exterior.xy)

#     # Interseciton of Malvik to Trøndelag
#     malvik = shape(sources["kommuner"][i_data]["omrade"])  # malvik
#     for item in sources["fylker"]:
#         if int(item["fylkesnummer"]) == 50:
#             print("bla", item["fylkesnummer"])
#             fylke = shape(item["omrade"])  # Trøndelag
#             continue
#     intersection = malvik.intersection(fylke)
#     print("ratio interseciton / kommune: ", intersection.area / fylke.area)
#     print("ratio interseciton / fylke: ", intersection.area / malvik.area)
#     plt.show()


if __name__ == "__main__":
    # sources = {"fylker": None, "kommuner": None}

    # # Get polygons and save to disk
    # for key in sources.keys():
    #     sources[key] = get_kartverket_data(key)
    #     dump_data(sources[key], f"kartverket_{key}.json")

    data = get_kartverket_data()
    data.to_file("test.geojson", driver='GeoJSON')

    # # read from disk instead
    # for key in sources.keys():
    #     sources[key] = load_data(f"kartverket_{key}.json")
    # example_plot(sources)

    # for key in sources.keys():
    #     data = sources[key]
    #     find_multipolygons(data)

