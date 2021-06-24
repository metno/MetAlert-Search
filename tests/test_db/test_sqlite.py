"""
MetAlert Search : SQLiteTest
==============================

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
import pytest

from datetime import datetime

from ma_search.db.sqlite import SQLiteDB

@pytest.mark.db
def testDBSQLite_Init(tmpConf, tmpDir):
    """Test class initialisation and creation of default DB.
    """
    dbFile = os.path.join(tmpDir, "index.db")

    tmpConf.dbProvider = "sqlite"
    tmpConf.sqlitePath = tmpDir

    # Check that the db was created
    theDB = SQLiteDB()
    assert theDB.conf.sqlitePath == tmpDir
    assert os.path.isfile(dbFile)
    assert theDB._isNew is True

    # Check that the two tables were created
    cursor = theDB._conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    cursor.close()
    assert ("MapData",) in tables
    assert ("AlertData",) in tables

    # Close and delete object
    del theDB

    # Re-open, and load the previously created DB
    theDB = SQLiteDB()
    assert os.path.isfile(dbFile)
    assert theDB._isNew is False

    # Cleanup
    os.unlink(dbFile)
    assert not os.path.isfile(dbFile)

# END Test testDBSQLite_Init

@pytest.mark.db
def testDBSQLite_EditMapRecord(tmpConf, tmpDir, caplog):
    """Test class initialisation and creation of default DB.
    """
    dbFile = os.path.join(tmpDir, "index.db")

    tmpConf.dbProvider = "sqlite"
    tmpConf.sqlitePath = tmpDir

    # Check that the db was created
    theDB = SQLiteDB()
    assert theDB.conf.sqlitePath == tmpDir
    assert os.path.isfile(dbFile)
    assert theDB._isNew is True

    # Test Error Checking
    # ===================
    newUUID = str(uuid.uuid4())

    # UUID Check
    caplog.clear()
    assert theDB.editMapRecord(
        cmd="insert", recordUUID="stuff", label="test label", source="test source",
        coordSystem="WGS84", west=-10, south=-9, east=8, north=7, area=272
    ) is False
    assert "The UUID 'stuff' is not valid" in caplog.text

    # South-North Boundaries
    caplog.clear()
    assert theDB.editMapRecord(
        cmd="insert", recordUUID=newUUID, label="test label", source="test source",
        coordSystem="WGS84", west=-10, south=-200, east=8, north=7, area=272
    ) is False
    assert "Coordinates must be in the range (-90 <= south < north <= 90)" in caplog.text

    caplog.clear()
    assert theDB.editMapRecord(
        cmd="insert", recordUUID=newUUID, label="test label", source="test source",
        coordSystem="WGS84", west=-10, south=-9, east=8, north=-17, area=272
    ) is False
    assert "Coordinates must be in the range (-90 <= south < north <= 90)" in caplog.text

    # East-West Boundaries
    caplog.clear()
    assert theDB.editMapRecord(
        cmd="insert", recordUUID=newUUID, label="test label", source="test source",
        coordSystem="WGS84", west=-200, south=-9, east=8, north=7, area=272
    ) is False
    assert "Coordinates must be in the range (-180 <= west < east <= 180)" in caplog.text

    caplog.clear()
    assert theDB.editMapRecord(
        cmd="insert", recordUUID=newUUID, label="test label", source="test source",
        coordSystem="WGS84", west=-10, south=-9, east=-18, north=7, area=272
    ) is False
    assert "Coordinates must be in the range (-180 <= west < east <= 180)" in caplog.text

    # Database Insert
    # ===============
    uuidOne = str(uuid.uuid4())
    uuidTwo = str(uuid.uuid4())

    # Insert Valid New Record
    assert theDB.editMapRecord(
        cmd="insert", recordUUID=uuidOne, label="test label", source="test source",
        coordSystem="WGS84", west=-10, south=-9, east=8, north=7, area=272,
        validFrom=datetime(2021, 1, 1, 0, 0, 0),
        validTo=datetime(2021, 12, 31, 23, 59, 59),
        meta={
            "admName": "test adm name",
            "admID": "test adm ID"
        }
    ) is True

    cursor = theDB._conn.execute("SELECT * FROM MapData;")
    theData = cursor.fetchall()
    assert theData[0] == (
        1, uuidOne, "test label", "test source", "test adm name", "test adm ID",
        "2021-01-01T00:00:00", "2021-12-31T23:59:59", "WGS84", -10.0, -9.0, 8.0, 7.0, 272.0
    )

    # Insert wo/optional
    assert theDB.editMapRecord(
        cmd="insert", recordUUID=uuidTwo, label="test label", source="test source",
        coordSystem="WGS84", west=-10, south=-9, east=8, north=7, area=272
    ) is True

    cursor = theDB._conn.execute("SELECT * FROM MapData;")
    theData = cursor.fetchall()
    assert theData[1] == (
        2, uuidTwo, "test label", "test source", None, None, None, None,
        "WGS84", -10.0, -9.0, 8.0, 7.0, 272.0
    )

    # Database Update
    # ===============
    assert theDB.editMapRecord(
        cmd="update", recordUUID=uuidTwo, label="new label", source="new source",
        coordSystem="WGS84", west=-11, south=-10, east=7, north=6, area=272,
        validFrom=datetime(2020, 1, 1, 0, 0, 0),
        validTo=datetime(2020, 12, 31, 23, 59, 59),
        meta={
            "admName": "new adm name",
            "admID": "new adm ID"
        }
    ) is True

    cursor = theDB._conn.execute("SELECT * FROM MapData;")
    theData = cursor.fetchall()
    assert theData[0] == ( # Unchanged
        1, uuidOne, "test label", "test source", "test adm name", "test adm ID",
        "2021-01-01T00:00:00", "2021-12-31T23:59:59", "WGS84", -10.0, -9.0, 8.0, 7.0, 272.0
    )
    assert theData[1] == ( # Updated
        2, uuidTwo, "new label", "new source", "new adm name", "new adm ID",
        "2020-01-01T00:00:00", "2020-12-31T23:59:59", "WGS84", -11.0, -10.0, 7.0, 6.0, 272.0
    )

    # SQL Error
    # =========

    # Non-Unique UUID
    caplog.clear()
    assert theDB.editMapRecord(
        cmd="insert", recordUUID=uuidTwo, label="test label", source="test source",
        coordSystem="WGS84", west=-10, south=-9, east=8, north=7, area=272
    ) is False
    assert "UNIQUE constraint failed: MapData.UUID" in caplog.text

    # Other
    # =====
    newUUID = str(uuid.uuid4())

    # Invalid Command
    caplog.clear()
    assert theDB.editMapRecord(
        cmd="blabla", recordUUID=newUUID, label="test label", source="test source",
        coordSystem="WGS84", west=-10, south=-9, east=8, north=7, area=272
    ) is False
    assert "Unknown command 'blabla'" in caplog.text

# END Test testDBSQLite_EditMapRecord
