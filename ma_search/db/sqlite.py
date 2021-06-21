"""
MetAlert Search : SQLite DB Wrapper
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

import os
import sqlite3
import logging

from ma_search.db.dbsuper import Database

logger = logging.getLogger(__name__)

class SQLiteDB(Database):

    def __init__(self):
        super().__init__()

        self._conn = None
        self._dbFile = None
        self._isNew = False

        if isinstance(self.conf.sqlitePath, str):
            self._dbFile = os.path.join(self.conf.sqlitePath, "index.db")
            self._isNew = not os.path.isfile(self._dbFile)
            self._conn = sqlite3.connect(self._dbFile)
            self._checkDB()

        return

    def __del__(self):
        """Close the database when the object is destroyed.
        """
        if isinstance(self._conn, sqlite3.Connection):
            logger.debug("Closing database connection")
            self._conn.commit()
            self._conn.close()

        return

    ##
    #  Data Methods
    ##

    def addMapEntry(self, data):
        """Add a new map entry to the database.
        Must be implemented in subclass.

        Parameters
        ----------
        data : dict
            A dictionary of the data to be added to the database.

        Returns
        -------
        bool :
            True if successful, otherwise False
        """
        return True

    def updateMapEntry(self, uuid, data):
        """Update a map entry in the database.
        Must be implemented in subclass.

        Parameters
        ----------
        data : dict
            A dictionary of the data to be added to the database.
        uuid : str
            The UUID of the entry to be updated

        Returns
        -------
        bool :
            True if successful, otherwise False
        """
        return True

    ##
    #  Internal Functions
    ##

    def _checkDB(self):
        """Check the structure of the database files.
        """
        if self._isNew:
            self._createMapTable()
            self._createAlertTable()

        return

    def _createMapTable(self):
        """Create the lookup table for map regions.

        Returns
        -------
        bool
            True if successful, otherwise False
        """
        if not isinstance(self._conn, sqlite3.Connection):
            logger.error("No database connection open")
            return False

        try:
            self._conn.execute(
                "CREATE TABLE 'MapData' (\n"
                "  'ID'          INTEGER NOT NULL,\n"
                "  'UUID'        TEXT NOT NULL UNIQUE,\n"
                "  'Name'        TEXT NOT NULL,\n"
                "  'AdmName'     TEXT,\n"
                "  'ValidFrom'   TEXT,\n"
                "  'ValidTo'     TEXT,\n"
                "  'Source'      TEXT NOT NULL,\n"
                "  'CoordSystem' TEXT NOT NULL,\n"
                "  'BoundWest'   REAL NOT NULL,\n"
                "  'BoundSouth'  REAL NOT NULL,\n"
                "  'BoundEast'   REAL NOT NULL,\n"
                "  'BoundNorth'  REAL NOT NULL,\n"
                "  'Area'        REAL NOT NULL,\n"
                "  PRIMARY KEY('ID' AUTOINCREMENT)\n"
                ");\n"
            )
            self._conn.commit()

        except Exception as e:
            logger.error(str(e))
            return False

        return True

    def _createAlertTable(self):
        """Create the lookup table for alerts.

        Returns
        -------
        bool
            True if successful, otherwise False
        """
        if not isinstance(self._conn, sqlite3.Connection):
            logger.error("No database connection open")
            return False

        try:
            self._conn.execute(
                "CREATE TABLE 'AlertData' (\n"
                "  'ID'          INTEGER NOT NULL,\n"
                "  'UUID'        TEXT NOT NULL UNIQUE,\n"
                "  'Name'        TEXT NOT NULL,\n"
                "  'RefDate'     TEXT,\n"
                "  'Source'      TEXT NOT NULL,\n"
                "  'CoordSystem' TEXT NOT NULL,\n"
                "  'BoundWest'   REAL NOT NULL,\n"
                "  'BoundSouth'  REAL NOT NULL,\n"
                "  'BoundEast'   REAL NOT NULL,\n"
                "  'BoundNorth'  REAL NOT NULL,\n"
                "  'Area'        REAL NOT NULL,\n"
                "  PRIMARY KEY('ID' AUTOINCREMENT)\n"
                ");\n"
            )
            self._conn.commit()

        except Exception as e:
            logger.error(str(e))
            return False

        return True

# END Class SQLiteDB
