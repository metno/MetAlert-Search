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

import os
import logging
from uuid import UUID, uuid4

from shapely.geometry import MultiPolygon, Polygon, mapping, shape

import ma_search

from ma_search.common import safeLoadJson, safeWriteJson, logException

logger = logging.getLogger(__name__)


class Shape():

    def __init__(self, uuid):
        """Lookup and manipulate polygons via their uuid

        Parameters
        ----------
        uuid : str
            Unique identifier UUID
        """
        self.conf = ma_search.CONFIG
        self._uuid = uuid
        if not self._validateUuid():
            logger.error("UUID %s is not valid", self._uuid)
            return

        self._path = os.path.join(self.conf.dataPath, self._uuid+".geojson")
        if not os.path.isfile(self._path):
            logger.error("UUID file %s does not exist", self._path)
            return

        return

    @classmethod
    def fromGeoJSON(cls, data):
        """Returns Shape instance from a GeoJson dict or file

        Parameters
        ----------
        data : dict or Path or str
            Input data, either a single GeoJson feature, or only the
            geometry section of a single feature. If str or Path: path
            to the file containing this dict.

        Returns
        -------
        :obj:`Shape` or None:
            A new instance of Shape(). Returns None for invalid input,
            e.g. not a Polygon.
        """
        uuid = uuid4()
        if cls.polygonFromGeoJson(data) is None:
            return None

        path = os.path.join(ma_search.CONFIG.dataPath, str(uuid)+".geojson")
        if not safeWriteJson(path, data):
            logger.error("Cannot write GeoJson file %s", path)
            return None

        return cls(str(uuid))

    ##
    #  Methods
    ##

    def polygon(self, tolerance=0.0, cachedOnly=True):
        """Returns the polygon with a given tolerance.

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
        if not isinstance(tolerance, float):
            logger.error("Tolerance has to be float, but is %s", type(tolerance))
            return None
        elif tolerance == 0.0:
            return self.polygonFromGeoJson(self._path)
        else:
            path = self._path[:-8]+f".{round(tolerance * 1e6)}.geojson"
            exists = os.path.isfile(path)

            if exists:
                return self.polygonFromGeoJson(path)
            elif cachedOnly:
                logger.error("Polygon does not exist for tolerance %s", tolerance)
                return None
            elif not exists:
                logger.info("Creating polygon %s with tolerance %s", self._uuid, tolerance)
                full = self.polygonFromGeoJson(self._path)
                if full is None:
                    logger.error("Full polygon cannot be loaded from %s", self._path)
                    return None
                simple = full.simplify(tolerance)
                if not safeWriteJson(path, mapping(simple)):
                    logger.error("Cannot write simplified polygon to file")
                    return None
                return simple
            else:  # pragma: no cover
                return None  # not reachable

    def toGeoJson(self, **kwargs):
        """Return geometry as as GeoJson

        Parameters
        ----------
        kwargs : dict
            kwargs to pass to Shape.polygon()

        Returns
        -------
        dict
            Geometry as dict in GeoJson format
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
        """Returns the polygon extracted from a geojson dict or file.

        Parameters
        ----------
        data : dict or Path or str
            Input data, either a single GeoJson feature, or only the
            geometry section of a single feature. If str or Path: Path
            to the file containing this dict.

        Returns
        -------
        :obj:`shapely.Polygon`, :obj:`shapely.MultiPolygon` or None
            Returns shape if it can be found, otherwise None.
        """
        if isinstance(data, dict):
            pass
        elif isinstance(data, str):
            data = safeLoadJson(data)
            if data is None:
                return None
        else:
            logger.error("Input has to be dict or string but is of type %s", type(data))
            return None

        if "geometry" in data:
            data = data["geometry"]

        try:
            geom = shape(data)
            if not isinstance(geom, (Polygon, MultiPolygon)):
                raise TypeError("data is not a polygon but %s", type(geom))
            return geom
        except Exception:
            logger.error("Not a valid GeoJson(-like) dict")
            logException()
            return None

    @staticmethod
    def geoJsonFromPolygon(polygon, extra={}):
        """Returns geoJson from a shapely object

        Parameters
        ----------
        polygon : :obj:`shapely.Polygon`, :obj:`shapely.MultiPolygon`
            Shapely object (Polygon).
        extra : dict
            Additional information to add to the geoJson file by
            updating the dictionary.

        Returns
        -------
        dict
            GeoJson dict
        """
        geoJson = {"type": "Feature",
                   "geometry": mapping(polygon)}
        if "type" in extra or "geometry" in extra:
            logging.warning("Cannot append extra arguments due to overlap in keys")
            return geoJson
        else:
            geoJson.update(extra)
            return geoJson

    ##
    #  Internal Methods
    ##

    def _validateUuid(self):
        """Validates that a string is a valid uuid.

        Returns
        -------
        bool
            True if attribute _uuid is a valid uuid, otherwise False.
        """
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
        except Exception:
            logException()
            return False

# END Class Shape
