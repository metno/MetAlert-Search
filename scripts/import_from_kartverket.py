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
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Union

import dateutil.parser as dtparser
import geopandas as gpd
import matplotlib.pyplot as plt


logging.basicConfig(level="INFO")


def get_kartverket_data(what, fn, crs_in, crs_out="epsg:4326"):
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
        crs_in (str or int): Coordinate system of input.
        crs_out (str or int): Coordinate system for output.
            Default is "epsg:4326", which is WGS84.

    Returns:
        (json): List of Json files with name, geometry, (...).

    """
    if what == "fylke":
        number_str = "fylkesnummer"
    elif what == "kommune":
        number_str = "kommunenummer"

    logging.info("Processing data for %s", fn)
    data = load_data(fn)

    base_key = next(iter(data)).split(".")[0]
    # data = geopandas.read_file(fn) # doesn't work due to complexity
    df = gpd.GeoDataFrame.from_features(data[f'{base_key}.{what}']['features'],
         crs=crs_in)
    df = df.to_crs(crs_out)
    df["navn"] = df["navn"].apply(pd_convert_nested_name)
    # gather to Multipolygon by kommune/fylke number if necessary
    df = df.dissolve(by=number_str, as_index=False)

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

@dataclass
class Sources:
    fn_in: Union[str, Path]
    fn_out: Union[str, Path]
    valid_from: Union[datetime, str]
    valid_to: Union[datetime, str]
    crs_in: str
    crs_out: str = "EPSG:4326"
    labels: List[str] = field(default_factory=list)

    def __post_init__(self):
        if isinstance(self.valid_from, str):
            self.valid_from = "" if self.valid_from == "" else dtparser.parse(self.valid_from)
        if isinstance(self.valid_to, str):
            self.valid_to = "" if self.valid_to == "" else dtparser.parse(self.valid_to)

if __name__ == "__main__":
    datadir = Path("scripts/kartverket_data")
    outdir = Path("scripts/kartverket_data/out")
    outdir.mkdir(exist_ok=True)

    # Kommuner
    what = "Kommune"
    items = [{"name":"Kommuner", "from": "2021", "to": ""},
                {"name":"Kommuner2020", "from": "2019", "to": "2020"},
                {"name":"Kommuner2019", "from": "2019", "to": "2020"}]
    for item in items:
        entry = Sources(fn_in=datadir/f"Basisdata_0000_Norge_25833_{item['name']}_GEOJSON.geojson",
                        fn_out=outdir/f"test_{item['name']}.geojson",
                        valid_from = item["from"],
                        valid_to = item["to"],
                        crs_in="EPSG:25833", #`EUREF89 UTM sone 33, 2d`
                        labels=what)
        data = get_kartverket_data(what=what.lower(), fn=entry.fn_in, crs_in=entry.crs_in)
        data.to_file(entry.fn_out, driver='GeoJSON')
        # data.plot()
        # data[data.geom_type == "MultiPolygon"].plot()
        # plt.show()


    # Fylker
    what = "Fylke"
    items = [{"name":"Fylker", "from": "2021", "to": ""},
             {"name":"Fylker2020", "from": "2019", "to": "2020"},
             {"name":"Fylker2019", "from": "2019", "to": "2020"}]
    for item in items:
        entry = Sources(fn_in=datadir/f"Basisdata_0000_Norge_25833_{item['name']}_GEOJSON.geojson",
                        fn_out=outdir/f"test_{item['name']}.geojson",
                        valid_from = item["from"],
                        valid_to = item["to"],
                        crs_in="EPSG:25833", #`EUREF89 UTM sone 33, 2d`
                        labels=what)
        data = get_kartverket_data(what=what.lower(), fn=entry.fn_in, crs_in=entry.crs_in)
        data.to_file(entry.fn_out, driver='GeoJSON')
        # data.plot()
        # plt.show()
