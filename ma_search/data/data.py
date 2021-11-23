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

import json
import os
import uuid
import logging
import ma_search

from shapely.geometry import Polygon, MultiPolygon

from ma_search.db import SQLiteDB
from ma_search.data.capxml import CapXML
from ma_search.data.shape import Shape
from ma_search.common import (
    logException, parseDateString, preparePath, safeLoadJson, safeWriteJson, checkUUID
)

logger = logging.getLogger(__name__)

UUID_NS = uuid.uuid5(uuid.NAMESPACE_URL, "metalert.met.no")


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

    def findOverlap(self, target, shape, vertical=None, cutoff=0.01, maxres=1000):
        """Parse a search dictionary and get values.
        """
        if self._db is None:
            logger.error("No database specified or available")
            return None

        if not isinstance(shape, (Polygon, MultiPolygon)):
            logger.error("Parameter 'shape' must be a shapely polygon")
            return None

        area = shape.area
        west, south, east, north = shape.bounds

        # First Pass: DB Lookup
        # =====================

        passTwo = {}
        if target == "map":
            pass
            # passOne = self._db.searchBounds(target, west, south, east, north)
            # for entry in passOne:
            #     if len(entry) == 14:
            #         recUUID = entry[1]
            #         recArea = entry[13]
            #         passTwo[recUUID] = recArea

        elif target == "alert":
            passOne = self._db.searchBounds(target, west, south, east, north)
            for entry in passOne:
                if len(entry) == 13:
                    recUUID = entry[1]
                    recZMin = entry[10]
                    recZMax = entry[11]
                    recArea = entry[12]
                    if vertical is None:
                        passTwo[recUUID] = recArea
                    else:
                        if vertical[0] < recZMax and vertical[1] > recZMin:
                            passTwo[recUUID] = recArea

        # Second Pass: Polygon Overlap
        # ============================

        result = {
            "records": 0,
            "maxres": maxres,
            "results": [],
        }

        if target == "map":
            pass

        elif target == "alert":
            for recNum, (recUUID, recArea) in enumerate(passTwo.items()):
                if recNum >= maxres:
                    break
                data = self._getFileData(target, recUUID)
                logger.error(str(data))
                recShape = Shape.polygonFromGeoJson(data.get("polygon", {}))
                if recShape is not None:
                    isectShape = shape.intersection(recShape)
                    overlap = isectShape.area / area
                    if overlap >= cutoff:
                        data["overlap"] = overlap
                        result["results"].append(data)

            result["records"] = len(result["results"])

        return result

    ##
    #  Alert (CAP) File Methods
    ##

    def ingestAlertFile(self, path, doReplace=False):
        """Ingest a CAP file, generate the meta data JSON file and
        add it to the index database.
        """
        try:
            capData = CapXML(path)
        except Exception:
            logger.error("Could not parse CAP file: %s", str(path))
            return False

        # Check the extracted data
        # ========================

        identifier = capData["identifier"]
        if identifier is None:
            logger.error("CAP file has no identifier: %s", str(path))
            return False

        geoJson = capData.asGeoJson()
        if geoJson is None:
            logger.error("CAP file has no polygon: %s", str(path))
            return False

        shape = Shape.polygonFromGeoJson(geoJson)
        if shape is None:
            logger.error("Could not parse polygon: %s", str(path))
            return False

        # Save Meta Data
        fUUID = str(uuid.uuid5(UUID_NS, identifier))
        fPath = preparePath(self.conf.dataPath, "alert", fUUID)
        if fPath is None:
            logger.error("Could not create storage path")
            return False

        # Save the data
        # =============

        jFile = os.path.join(fPath, f"{fUUID}.json")
        if os.path.isfile(jFile) and not doReplace:
            logger.warning(
                "CAP file with identifier '%s' already exists and is not being overwritten",
                identifier
            )
            return False

        area = shape.area
        west, south, east, north = shape.bounds
        jData = {
            "identifier": identifier,
            "source": path,
            "sent": capData["sent"],
            "areaDesc": capData["areaDesc"],
            "polygon": geoJson["geometry"],
            "altitude": capData["altitude"],
            "ceiling": capData["ceiling"],
            "area": area,
            "bounds": {
                "west": west,
                "east": east,
                "north": north,
                "south": south
            }
        }

        status = True
        status &= safeWriteJson(jFile, jData, indent=2)
        status &= self.indexAlertMetaFile(jFile, data=jData, doReplace=doReplace)

        return status

    def indexAlertMetaFile(self, path, data=None, doReplace=False):
        """Add an alert meta file to the index database. The file must
        exist, but if the data variable is set, the file isn't read.
        """
        if self._db is None:
            logger.error("No database specified or available")
            return False

        if not os.path.isfile(path):
            logger.error("No such file: %s", path)
            return False

        jsonFile = os.path.basename(path)
        fileUUID = jsonFile[:36]
        if not (len(jsonFile) == 41 and jsonFile.endswith(".json") and checkUUID(fileUUID)):
            logger.error("Skipping unknown file: %s", path)
            return False

        if data is None:
            with open(path, mode="r") as inFile:
                data = json.load(inFile)

        bounds = data.get("bounds", {})
        dbStat = self._db.editAlertRecord(
            cmd="replace" if doReplace else "insert",
            recordUUID=fileUUID,
            identifier=data.get("identifier", None),
            sentDate=parseDateString(data.get("sent", None)),
            sourcePath=data.get("source", None),
            coordSystem="WGS84",
            west=bounds.get("west", 0.0),
            south=bounds.get("south", 0.0),
            east=bounds.get("east", 0.0),
            north=bounds.get("north", 0.0),
            altitude=data.get("altitude", 0.0),
            ceiling=data.get("ceiling", 0.0),
            area=data.get("area", 0.0)
        )
        if dbStat:
            logger.info("Indexed file: %s", path)
        else:
            logger.error("Failed to index file: %s", path)

        return dbStat

    def rebuildAlertIndex(self):
        """Rebuild the index of alert files saved in the data cache
        folder.
        """
        if self._db is None:
            logger.error("No database specified or available")
            return False

        if not self._db.purgeAlertTable():
            logger.error("Could not clear old database")
            return False

        for dirOne in os.listdir(self.conf.dataPath):
            pathOne = os.path.join(self.conf.dataPath, dirOne)
            if not (os.path.isdir(pathOne) and dirOne.startswith("alert_")):
                logger.info("Skipping: %s", pathOne)
                continue
            for dirTwo in os.listdir(pathOne):
                pathTwo = os.path.join(pathOne, dirTwo)
                if not (os.path.isdir(pathTwo) and dirTwo.startswith("alert_")):
                    logger.info("Skipping: %s", dirTwo)
                    continue
                for jsonFile in os.listdir(pathTwo):
                    jsonPath = os.path.join(pathTwo, jsonFile)
                    if not (os.path.isfile(jsonPath) and jsonFile.endswith(".json")):
                        logger.info("Skipping: %s", dirTwo)
                        continue
                    self.indexAlertMetaFile(jsonPath)

        return True

    ##
    #  Map File Methods
    ##

    def ingestMapFile(self, path, doReplace=False):
        """Ingest a map file, generate the meta data JSON file and
        add it to the index database.
        """

        # TO DO, to be called by import_from_kartverket?
        pass

    def indexMap(self, path, data=None, doReplace=False):
        """Add a map file to the map database. The file must
        exist, but if the data variable is set, the file isn't read.
        """

        if self._db is None:
            logger.error("No database specified or available")
            return False

        if not os.path.isfile(path):
            logger.error("No such file: %s", path)
            return False

        if data is None:
            with open(path, mode="r") as inFile:
                data = json.load(inFile)

        shape = Shape.polygonFromGeoJson(data.get("polygon", {}))
        if shape is None:
            logger.error("No database specified or available")
            return False

        bounds = shape.bounds

        fileUUID = str(uuid.uuid5(UUID_NS, data.get("administrativeID")))

        dbStat = self._db.editMapRecord(
            cmd="replace" if doReplace else "insert",
            # FileUUID should be created in IngestMapFile
            recordUUID=fileUUID,
            label=data.get("label"),
            source=path,
            coordSystem="WGS84",
            west=bounds.get("west", 0.0),
            south=bounds.get("south", 0.0),
            east=bounds.get("east", 0.0),
            north=bounds.get("north", 0.0),
            area=shape.area,
            validFrom=data.get("validFrom", None),
            validTo=data.get("validTo", None),
            meta={"admName": data.get("administrativeName", None),
                  "admID": data.get("administrativeID", None)}
        )

        if dbStat:
            logger.info("Indexed file: %s", path)
        else:
            logger.error("Failed to index file: %s", path)

        return dbStat

    ##
    #  Internal Functions
    ##

    def _getFileData(self, target, fUUID):
        """Load data from a file based on its uuid."""
        try:
            dirOne = f"{target}_{fUUID[7]}"
            dirTwo = f"{target}_{fUUID[6]}"
            filePath = os.path.join(self.conf.dataPath, dirOne, dirTwo, f"{fUUID}.json")
            return safeLoadJson(filePath)
        except Exception:
            logException()
            return {}

# END Class Data
