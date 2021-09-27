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
import uuid
import sqlite3
import logging

from datetime import datetime

from ma_search.db.dbsuper import Database
from ma_search.common import logException

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
        """Close the database when the object is destroyed."""
        if isinstance(self._conn, sqlite3.Connection):
            logger.debug("Closing database connection")
            self._conn.commit()
            self._conn.close()
        return

    ##
    #  Data Methods
    ##

    def editMapRecord(
        self, cmd, recordUUID, label, source, coordSystem, west, south, east, north, area,
        validFrom=None, validTo=None, meta=None
    ):
        """Insert or update a map record in the database.

        Parameters
        ----------
        cmd : str
            The command to be run on the database. Must be either "insert",
            "update" or "replace".
        recordUUID : str
            The UUID of the dataset to be added or modified.
        label : str
            A user-defined label for the record.
        source : str
            A user-defined source description for the record.
        coordSystem : str
            The coordinate system (datum) used for this record.
        west, south, east, north, area : float
            The coordinates in degrees of the bounding rectangle, and the area
            of it as reported by shapely.
        validFrom, validTo : datetime or None, optional
            The validity range of the record.
        meta : dict or None, optional
            A dictionary of meta data values to be added. Currently accepted
            are "admName" and "admID". Other values will be ignored.

        Returns
        -------
        bool :
            True if successful, otherwise False
        """
        pUUID = None
        fromDate = None
        toDate = None
        admName = None
        admID = None
        valid = True

        try:
            pUUID = str(uuid.UUID(recordUUID))
        except Exception:
            logger.error("The UUID '%s' is not valid" % str(recordUUID))
            logException()
            valid = False

        if not (-90.0 <= south < north <= 90.0):
            logger.error("Coordinates must be in the range (-90 <= south < north <= 90)")
            valid = False

        if not (-180.0 <= west < east <= 180.0):
            logger.error("Coordinates must be in the range (-180 <= west < east <= 180)")
            valid = False

        if isinstance(validFrom, datetime):
            fromDate = validFrom.isoformat()

        if isinstance(validTo, datetime):
            toDate = validTo.isoformat()

        if isinstance(meta, dict):
            admName = meta.get("admName", None)
            admID = meta.get("admID", None)

        if not valid:
            logger.error("Incorrect parameters provided to editMapEntry")
            return False

        if cmd in ("insert", "replace"):
            try:
                self._conn.execute((
                    f"{cmd.upper()} INTO MapData ("
                    "UUID, Label, Source, AdmName, AdmID, ValidFrom, ValidTo, "
                    "CoordSystem, BoundWest, BoundSouth, BoundEast, BoundNorth, Area"
                    ") VALUES ("
                    "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?"
                    ");"
                ), (
                    pUUID, label, source, admName, admID, fromDate, toDate,
                    coordSystem, west, south, east, north, area
                ))
                self._conn.commit()
            except Exception:
                logException()
                return False

        elif cmd == "update":
            try:
                self._conn.execute((
                    "UPDATE MapData SET "
                    "Label = ?, "
                    "Source = ?, "
                    "AdmName = ?, "
                    "AdmID = ?, "
                    "ValidFrom = ?, "
                    "ValidTo = ?, "
                    "CoordSystem = ?, "
                    "BoundWest = ?, "
                    "BoundSouth = ?, "
                    "BoundEast = ?, "
                    "BoundNorth = ?, "
                    "Area = ? "
                    "WHERE UUID = '%s'"
                ) % str(pUUID), (
                    label, source, admName, admID, fromDate, toDate,
                    coordSystem, west, south, east, north, area
                ))
            except Exception:
                logException()
                return False

        else:
            logger.error("Unknown command '%s'" % cmd)
            return False

        return True

    def editAlertRecord(
        self, cmd, recordUUID, identifier, sentDate, sourcePath, coordSystem,
        west, south, east, north, altitude, ceiling, area
    ):
        """Insert or update a map record in the database.

        Parameters
        ----------
        cmd : str
            The command to be run on the database. Must be either "insert",
            "update" or "replace".
        recordUUID : str
            The UUID of the dataset to be added or modified.
        identifier : str
            The unique identifier from the alert itself.
        sentDate : datetime
            The timestamp of when the alert was sent
        sourcePath : str
            The path to the CAP file.
        coordSystem : str
            The coordinate system (datum) used for this record.
        west, south, east, north, altitude, ceiling, area : float
            The coordinates in degrees of the bounding rectangle, the altitude
            and ceiling of the alert, and the area of the polygon as reported
            by shapely.

        Returns
        -------
        bool :
            True if successful, otherwise False
        """
        pUUID = None
        valid = True

        try:
            pUUID = str(uuid.UUID(recordUUID))
        except Exception:
            logger.error("The UUID '%s' is not valid" % str(recordUUID))
            logException()
            valid = False

        if not (-90.0 <= south < north <= 90.0):
            logger.error("Coordinates must be in the range (-90 <= south < north <= 90)")
            valid = False

        if not (-180.0 <= west < east <= 180.0):
            logger.error("Coordinates must be in the range (-180 <= west < east <= 180)")
            valid = False

        if ceiling < altitude:
            logger.error("Ceiling must be greater or equal to altitude")
            valid = False

        if isinstance(sentDate, datetime):
            sentDate = sentDate.isoformat()
        else:
            logger.error("SentDate must be a datetime object")
            valid = False

        if not valid:
            logger.error("Incorrect parameters provided to editMapEntry")
            return False

        if cmd in ("insert", "replace"):
            try:
                self._conn.execute((
                    f"{cmd.upper()} INTO AlertData ("
                    "UUID, Identifier, SentDate, SourcePath, CoordSystem, "
                    "BoundWest, BoundSouth, BoundEast, BoundNorth, Altitude, Ceiling, Area"
                    ") VALUES ("
                    "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?"
                    ");"
                ), (
                    pUUID, identifier, sentDate, sourcePath, coordSystem,
                    west, south, east, north, altitude, ceiling, area
                ))
                self._conn.commit()
            except Exception:
                logException()
                return False

        elif cmd == "update":
            try:
                self._conn.execute((
                    "UPDATE AlertData SET "
                    "Identifier = ?, "
                    "SentDate = ?, "
                    "SourcePath = ?, "
                    "CoordSystem = ?, "
                    "BoundWest = ?, "
                    "BoundSouth = ?, "
                    "BoundEast = ?, "
                    "BoundNorth = ?, "
                    "Altitude = ?, "
                    "Ceiling = ?, "
                    "Area = ? "
                    "WHERE UUID = '%s'"
                ) % str(pUUID), (
                    identifier, sentDate, sourcePath, coordSystem,
                    west, south, east, north, altitude, ceiling, area
                ))
            except Exception:
                logException()
                return False

        else:
            logger.error("Unknown command '%s'" % cmd)
            return False

        return True

    ##
    #  Internal Functions
    ##

    def _checkDB(self):
        """Check the structure of the database files."""
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
                "  'Label'       TEXT NOT NULL,\n"
                "  'Source'      TEXT NOT NULL,\n"
                "  'AdmName'     TEXT,\n"
                "  'AdmID'       TEXT,\n"
                "  'ValidFrom'   TEXT,\n"
                "  'ValidTo'     TEXT,\n"
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

        except Exception:
            logException()
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
                "  'Identifier'  TEXT NOT NULL,\n"
                "  'SentDate'    TEXT NOT NULL,\n"
                "  'SourcePath'  TEXT NOT NULL,\n"
                "  'CoordSystem' TEXT NOT NULL,\n"
                "  'BoundWest'   REAL NOT NULL,\n"
                "  'BoundSouth'  REAL NOT NULL,\n"
                "  'BoundEast'   REAL NOT NULL,\n"
                "  'BoundNorth'  REAL NOT NULL,\n"
                "  'Altitude'    REAL NOT NULL,\n"
                "  'Ceiling'     REAL NOT NULL,\n"
                "  'Area'        REAL NOT NULL,\n"
                "  PRIMARY KEY('ID' AUTOINCREMENT)\n"
                ");\n"
            )
            self._conn.commit()

        except Exception:
            logException()
            return False

        return True

# END Class SQLiteDB
