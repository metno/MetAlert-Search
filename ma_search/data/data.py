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
import logging
import ma_search

from ma_search.data.capxml import CapXML
from ma_search.data.shape import Shape
from ma_search.common import preparePath, safeWriteJson

logger = logging.getLogger(__name__)

UUID_NS = uuid.uuid5(uuid.NAMESPACE_URL, "metalert.met.no")


class Data():

    def __init__(self):
        self.conf = ma_search.CONFIG
        return

    def ingestAlertFile(self, path, doReplace=False):
        """Ingest a CAP file, generate the meta data JSON files and
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
        safeWriteJson(jFile, {
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
        }, indent=2)

        return True

    def indexAlertCacheFile(self, path, data=None):
        pass

    def rebuildAlertIndex(self):
        pass

# END Class Data
