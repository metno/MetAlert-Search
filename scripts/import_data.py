""" Download (and import) data from kartverket """

import json
import requests
import logging

# needed for some additional funcitons only
from shapely.geometry import shape
import matplotlib.pyplot as plt

logging.basicConfig(level="INFO")


def get_kartverket_data(what, coordinatesys=4362):
    """Gets Kartverket polygon data for Kommuner / Fylker

    Will return the detailed polygons. Boundary boxes can be loaded separatly.
    See also: https://ws.geonorge.no/kommuneinfo/v1/#/

    Args:
        what (str): What information to get. Has to be in
            ["fylke", "kommune"]
        coordinatesys (int): Coordinate system for output. Default is
            4326, which is WGS84

    Returns:
        (json): List of Json files with name, geometry, (...). See
            Kartverket's API for more information.

    """
    if what not in ["fylker", "kommuner"]:
        raise NotImplementedError(f"`what`={what} not supported.")

    if what == "fylker":
        number_str = "fylkesnummer"
    elif what == "kommuner":
        number_str = "kommunenummer"

    url = f"https://ws.geonorge.no/kommuneinfo/v1/{what}?filtrer={number_str}"
    headers = {'accept': 'application/json'}
    req = requests.get(url, headers=headers)
    if req.status_code != 200:
        raise RuntimeError(f"Status code: {req.status_code}")
    data = req.json()

    bounds = []
    url2 = (f"https://ws.geonorge.no/kommuneinfo/v1/{what}/{{}}/omrade"
            f"?utkoordsys={coordinatesys}")
    for item in data:
        no = item[number_str]
        area = requests.get(url2.format(no), headers=headers)
        if area.status_code != 200:
            raise RuntimeError(f"Status code: {area.status_code}")
        bounds.append(area.json())

    logging.info(f"Reveiced {len(bounds)} {what} objects from kartverket")
    return bounds


def dump_data(request, fn='kartdata.json'):
    with open(fn, 'w') as f:
        json.dump(request, f, ensure_ascii=False)


def load_data(fn='kartdata.json'):
    with open(fn) as f:
        data = json.load(f)
    return data


def find_multipolygons(data):
    """ Find "true" multipolygons in kartverkets data.

    Finds geoJson objects which more then one polygon in the same (
    Multi)Polygon object

    Args:
        data (List[GeoJSON]) List of Fylke/Kommune geometries
    """

    for i, item in enumerate(data):
        polygon = shape(item["omrade"])
        if len(polygon.geoms) != 1:
            if "fylkesnavn" in item:
                name_str = "fylkesnavn"
            elif "kommunenavn" in item:
                name_str = "kommunenavn"
            else:
                raise NotImplementedError
            logging.info(f"{item[name_str]} (no. {i}) has {len(polygon.geoms)} polygons")


if __name__ == "__main__":
    sources = {"fylker": None, "kommuner": None}

    for key in sources.keys():
        sources[key] = get_kartverket_data(key)
        dump_data(sources[key], f"kartverket_{key}.json")

    # for key in sources.keys():
    #     sources[key] = load_data(f"kartverket_{key}.json")

    for key in sources.keys():
        data = sources[key]
        find_multipolygons(data)

    # example plot
    i_data = 271
    polygon1 = shape(sources["kommuner"][i_data]["omrade"])
    for geom in polygon1.geoms:
        plt.plot(*geom.exterior.xy)
    plt.show()