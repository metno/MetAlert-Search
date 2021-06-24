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

import uuid
import logging

import ma_search

logger = logging.getLogger(__name__)

class Shape(): # pragma: no cover

    def __init__(self, uuid):

        self.conf = ma_search.CONFIG
        self._uuid = uuid

        # ToDo:
        # - Validate UUID
        # - Check that file exists

        return

    @classmethod
    def fromGeoJSON(cls, data):
        """
        Returns
        -------
        :obj:`Shape` :
            A new instance of Polygon()
        """
        newUUID = uuid.uuid4()
        # save geojson data to file named newUUID.geojson
        poly = cls(newUUID)
        return poly

    ##
    #  Methods
    ##

    def polygon(self, tolerance=0.0, cachedOnly=True):
        """Returns the polygon extracted from the geojson file.

        Parameters
        ----------
        tolerance : float
            The tolerance level to return. If 0, retunrs the full
            polygon.
        cachedOnly : bool
            If False, will generate the simplified polygon if tolerance
            is larger than zero. If True, will return None if the
            polygon is not in the cache.

        Returns
        -------
        :obj:`shapely.Polygon`, :obj:`shapely.MultiPolygon` or None
        """
        return

    ##
    #  Static Methods
    ##

    @staticmethod
    def polygonFromGeoJson(geoJson):
        """
        """
        return

    @staticmethod
    def geoJsonFromPolygon(polygon):
        """
        """
        return

# END Class Shape
