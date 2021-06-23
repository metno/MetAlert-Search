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

import logging
import ma_search

from datetime import datetime

from ma_search.db import SQLiteDB

logger = logging.getLogger(__name__)

MAP_DICT = {
    "label": (str, True),
    "source": (str, True),
    "administrativeName": (str, False),
    "administrativeID": (str, False),
    "validFrom": (datetime, False),
    "validTo": (datetime, False),
    "polygon": ((dict, list), False),
    "coordinateSystem": (str, True),
}

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

    def addMapEntry(self, data):
        """Add a new map entry to the database.
        Must be implemented in subclass.

        Parameters
        ----------
        data : dict
            A dictionary of the data to be added to the database.
        """
        raise NotImplementedError

    def updateMapEntry(self, uuid, data):
        """Update a map entry in the database.
        Must be implemented in subclass.

        Parameters
        ----------
        data : dict
            A dictionary of the data to be added to the database.
        uuid : str
            The UUID of the entry to be updated
        """
        raise NotImplementedError

    ##
    #  Internal Functions
    ##

    def _validateMapDict(self, data):
        """
        """
        valid = True
        for key, req in MAP_DICT.items():
            valid &= key in data
            value = data[key]
            if not isinstance(value, req[0]):
                valid &= req[1] and value is None

        return valid

# END Class Data
