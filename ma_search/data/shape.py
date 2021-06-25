"""
MetAlert Search : Polygon Class
===============================

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
from pathlib import Path
from uuid import UUID, uuid4

import ma_search
from shapely.geometry import MultiPolygon, Polygon, mapping, shape

logger = logging.getLogger(__name__)

class Shape():
    def __init__(self, uuid):
        """Keeps track, can lookup and manipulate (Multi)Polygons via their uuid

        Args:
            uuid (str): Unique identifyer UUID4
        """
        self.conf = ma_search.CONFIG
        self._uuid = uuid
        if not self._validateUuid():
            logger.error("UUID %s is not valid", self._uuid)
            return

        self._path = (Path(self.conf.dataPath) / self._uuid).with_suffix(".geojson")
        if not self._path.exists():
            logger.error("UUID file %s does not exist", self._path)

    @classmethod
    def fromGeoJSON(cls, data):
        """Returns Shape instance from a GeoJson input file

        Parameters
        ----------
        data : dict or Path or str
            Input data, either a single GeoJson feature, or only the geometry
            section of a single feature. If str or Path: Path to the file
            containing this dict.

        Returns
        -------
        :obj:`Shape` or None:
            A new instance of Shape(). Returns None for invalid input, e.g. not
            a Polygon.
        """
        uuid = uuid4()
        if cls.polygonFromGeoJson(data) is None:
            return None # tests that it

        path = (ma_search.CONFIG.dataPath / str(uuid)).with_suffix(".geojson")
        with path.open('w') as f:
            json.dump(data, f)

        poly = cls(str(uuid))
        return poly

    ##
    #  Methods
    ##

    def polygon(self, tolerance=0.0, cachedOnly=True):
        """Returns the polygon extracted from the geojson file.

        Parameters
        ----------
        tolerance : float
            The tolerance level to return. If 0, rereturns the "full"
            polygon. Assumes that the minimum tolerance is 1e-6.
        cachedOnly : bool
            If False, will generate the simplified polygon if tolerance
            is larger than zero. If True, will return None if the
            polygon is not in the cache.

        Returns
        -------
        :obj:`shapely.Polygon`, :obj:`shapely.MultiPolygon` or None
            Returns shape if it can be found, otherwise None.
        """
        if tolerance == 0.0:
            return self.polygonFromGeoJson(self._path)
        else:
            suffix = f".{round(tolerance * 1e6)}.geojson"
            path = (self._path.parent / self._path.stem).with_suffix(suffix)
            exists = path.exists()

            if exists:
                return self.polygonFromGeoJson(path)
            elif cachedOnly:
                logger.error("Polygon does not exist for tolerance %s", tolerance)
                return
            elif not exists:
                logger.info("Creating polygon %s with tolerance %s", self._uuid, tolerance)
                full = self.polygonFromGeoJson(self._path)
                simple = full.simplify(tolerance)
                with path.open('w') as f:
                    json.dump(mapping(simple), f)
                return simple

    def toGeoJson(self, **kwargs):
        """Return geometry as as GeoJson
        Parameters
        ----------
        kwargs : dict
            kwargs to pass to Shape.polygon()
        """
        geom = mapping(self.polygon(**kwargs))
        geoJson = {"type": "Feature",
                   "geometry": geom}
        return geoJson

    ##
    #  Static Methods
    ##

    @staticmethod
    def polygonFromGeoJson(data):
        """Returns the polygon extracted from the geojson file.

        Parameters
        ----------
        data : dict or Path or string

        Returns
        -------
        :obj:`shapely.Polygon`, :obj:`shapely.MultiPolygon` or None
            Returns shape if it can be found, otherwise None.
        """
        if isinstance(data, dict):
            pass
        elif isinstance(data, (Path, str)):
            path = Path(data)
            if not path.exists():
                logger.error("%s does not exist", path)
                return None
            with path.open() as f:
                data = json.load(f)
        else:
            logger.error("Input has to be dict, Path or string but is of type %s", type(data))
            return None

        if "geometry" in data:
            data = data["geometry"]
        try:
            geom = shape(data)
            if not isinstance(geom, (Polygon, MultiPolygon)):
                raise TypeError("data is not a polygon but %s", type(geom))
        except Exception as e:
            logger.error("Not a valid GeoJson(-like) dict. %s: %s", type(e).__name__, e)
            return None
        return geom

    @staticmethod
    def geoJsonFromPolygon(polygon, extra={}):
        """Returns geoJson from a shapely object

        Parameters
        ----------
        polygon : :obj:`shapely.Polygon`, :obj:`shapely.MultiPolygon`
            Shapely object (Polygon).
        extra : dict
            Additional information to add to the geoJson file by updating the
            dictionary.

        Returns
        -------
        dict
        """
        geoJson = {"type": "Feature",
                   "geometry": mapping(polygon)}
        if "type" in extra or "geometry" in extra:
            logging.warning("Cannot append extra arguments due to overlap in keys.")
            return geoJson
        else:
            geoJson.update(extra)
            return geoJson

    ##
    #  Internal Methods
    ##

    def _validateUuid(self):
        """Validates that a string is a valid uuid4."""
        if not isinstance(self._uuid, str):
            logger.error("UUID %s is not a string", self._uuid)
            return False

        try:
            val = UUID(self._uuid)
            if str(val) == self._uuid:
                return True
            else:
                logger.error("UUID %s is not valid", self._uuid)
                return False
        except Exception as e:
            logger.error("%s: %s", type(e).__name__, e)
            return False
# END Class Shape
