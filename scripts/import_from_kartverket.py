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
import dataclasses
from dataclasses import dataclass, field
import datetime
from pathlib import Path
from typing import List, Union
from shapely.geometry import mapping

import dateutil.parser as dtparser
import geopandas as gpd


logging.basicConfig(level="INFO")


def get_kartverket_data(what, fn, crs_in, crs_out="epsg:4326"):
    """Transform Kartverket polygon data for Kommuner / Fylker

    The datasets have to be downloaded manually, see
    https://kartkatalog.geonorge.no/metadata?text=administrative%20grenser%20kommuner&organization=Kartverket
    or
    https://www.kartverket.no/api-og-data/grensedata

    Note:
        - The script assumes that one downloads the data as geoJSON. Due
          to limitations at the time of testing, it had to be downloaded
          as in the projection `EUREF89 UTM sone 33, 2d`, which
          corresponds to `EPSG code 25833`.
        - For historical data, see
          `Administrative enheter - historiske versjoner` at geonorge.

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
    # gather to Multipolygon by kommune/fylke number if necessary
    df = df.dissolve(by=number_str, as_index=False)
    df["administrativeName"] = df["navn"].apply(pd_convert_nested_name)
    df["administrativeID"] = df[number_str]

    return df


def pd_convert_nested_name(col):
    """Convert nested name from kartverket geoJSON to simple"""
    return col[0]["navn"]


def jsondefault(o):
    """Converts datetime. to isoformat when dumping json"""
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()


def dump_data(data, fn='kartdata.json', **kwargs):
    kwargs.setdefault("default", jsondefault)
    kwargs.setdefault("ensure_ascii", False)
    with open(fn, 'w') as f:
        json.dump(data, f, **kwargs)


def load_data(fn='kartdata.json'):
    with open(fn) as f:
        data = json.load(f)
    return data


@dataclass
class Sources:
    fn_in: Union[str, Path]
    fn_out: Union[str, Path]
    source: str
    valid_from: Union[datetime.datetime, str]
    valid_to: Union[datetime.datetime, str]
    crs_in: str

    crs_out: str = "EPSG:4326"
    labels: List[str] = field(default_factory=list)
    # administrativeName: Optional[str] = None
    # administrativeID: Optional[str] = None
    # geometry: Optional[Union[Polygon, MultiPolygon]] = None

    def __post_init__(self):
        if isinstance(self.valid_from, str):
            self.valid_from = "" if self.valid_from == "" else dtparser.parse(self.valid_from)
        if isinstance(self.valid_to, str):
            self.valid_to = "" if self.valid_to == "" else dtparser.parse(self.valid_to)


map_to_db_inv = {
    "label": "labels",
    "source": "source",
    "administrativeName": "administrativeName",
    "administrativeID": "administrativeID",
    "validFrom": "valid_from",
    "validTo": "valid_to",
    "polygon": "geometry",
    "coordinateSystem": "crs_out",
}


map_to_db = {v: k for k, v in map_to_db_inv.items()}


if __name__ == "__main__":
    datadir = Path("scripts/kartverket_data")
    outdir = Path("scripts/kartverket_data/out")
    outdir.mkdir(exist_ok=True)

    # Kommuner
    items = {
        "Kommune": [
            {"name": "Kommuner", "from": "2021", "to": ""},
            {"name": "Kommuner2020", "from": "2020", "to": "2021"},
            {"name": "Kommuner2019", "from": "2019", "to": "2020"}
        ],
        "Fylke": [
            {"name": "Fylker", "from": "2021", "to": ""},
            {"name": "Fylker2020", "from": "2020", "to": "2021"},
            {"name": "Fylker2019", "from": "2019", "to": "2020"}
        ]
    }
    for key, vals in items.items():
        for item in vals:
            entry = Sources(fn_in=(datadir
                                   / f"Basisdata_0000_Norge_25833_{item['name']}_GEOJSON.geojson"),
                            fn_out=outdir/f"test_{item['name']}",
                            valid_from=item["from"],
                            valid_to=item["to"],
                            crs_in="EPSG:25833",  # `EUREF89 UTM sone 33, 2d`
                            source="kartverket",
                            labels=key)
            data = get_kartverket_data(what=key.lower(), fn=entry.fn_in, crs_in=entry.crs_in)

            # TODO: convert shapely geometry to dict [only necessary for wr to file?]
            data["geometry"] = data["geometry"].apply(mapping)

            for key, val in dataclasses.asdict(entry).items():
                if key not in map_to_db:
                    continue
                if key in data.columns:
                    raise NotImplementedError(f"Key {key} would be overwritten")
                data[key] = val

            # Note: removes additional attributes
            data = data.filter(map_to_db.keys())
            data = data.rename(columns=map_to_db, errors="raise")

            for index, row in data.iterrows():
                row_dic = row.to_dict()
                dump_data(row_dic, f"{entry.fn_out}_{index}")
                raise RuntimeError("Just stop for 'debugging'")
