"""
MetAlert Search : Data Class
============================

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
import uuid
import json
import logging
import ma_search

from datetime import datetime

from ma_search.db import SQLiteDB
from ma_search.common import logException, safeMakeDir, checkUUID

logger = logging.getLogger(__name__)


class Data():

    def __init__(self):

        self.conf = ma_search.CONFIG

        self._db = None

        if self.conf.dbProvider == "sqlite":
            self._db = SQLiteDB()

        return

    ##
    #  Methods
    ##

    def addMapEntry(
        self, label, source, coordSystem, geoJson,
        validFrom=None, validTo=None, meta=None
    ):
        """Add a new map entry to the data store and index database.

        Parameters
        ----------
        data : dict
            A dictionary of the data to be added to the database.
        """
        newUUID = uuid.uuid4()
        self._saveMapEntry(
            newUUID, label, source, coordSystem, geoJson,
            validFrom, validTo, meta
        )

        return True

    def updateMapEntry(self, uuid, data):
        """Update a map entry in the data store and index database.

        Parameters
        ----------
        data : dict
            A dictionary of the data to be added to the database.
        uuid : str
            The UUID of the entry to be updated.
        """
        raise NotImplementedError

    ##
    #  Internal Functions
    ##

    def _saveMapEntry(
        self, recordUUID, label, source, coordSystem, geoJson,
        validFrom=None, validTo=None, meta=None
    ):
        """Internal function for handling the storage of map data.

        Parameters
        ----------
        """
        pUUID = None
        fromDate = None
        toDate = None

        pUUID = checkUUID(recordUUID)
        if pUUID is None:
            logger.error("The UUID '%s' is not valid" % str(recordUUID))
            return False

        if isinstance(validFrom, datetime):
            fromDate = validFrom.isoformat()

        if isinstance(validTo, datetime):
            toDate = validTo.isoformat()

        # Write Files
        # ===========

        if not safeMakeDir(self.conf.mapData):
            logger.error("Problems writing to data storage folder")
            return False

        subDirName = "data_" + pUUID[7]
        subDirPath = os.path.join(self.conf.mapData, subDirName)
        if not safeMakeDir(subDirPath):
            logger.error("Problems writing to data storage folder")
            return False

        mainFile = os.path.join(subDirPath, pUUID+".json")
        geoJsonFile = os.path.join(subDirPath, pUUID+".geojson")

        try:
            with open(mainFile, mode="w", encoding="utf-8") as outFile:
                json.dump({
                    "uuid": pUUID,
                    "label": str(label),
                    "source": str(source),
                    "validFrom": fromDate,
                    "validTo": toDate,
                    "coordSystem": str(coordSystem),
                    "meta": meta,
                }, outFile, indent=2)
        except Exception:
            logger.error("Failed to write file: %s", mainFile)
            logException()
            return False

        try:
            with open(geoJsonFile, mode="w", encoding="utf-8") as outFile:
                json.dump(geoJson, outFile, indent=2)
        except Exception:
            logger.error("Failed to write file: %s", geoJsonFile)
            logException()
            return False

        return True

# END Class Data
