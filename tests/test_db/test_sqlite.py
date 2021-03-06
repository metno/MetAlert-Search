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

    Should check that the tables are created, but the create functions
    are tested separately.
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
def testDBSQLite_CreateTable(tmpConf, tmpDir, caplog):
    """Check that the table create functions can handle exceptions."""
    dbFile = os.path.join(tmpDir, "index.db")

    tmpConf.dbProvider = "sqlite"
    tmpConf.sqlitePath = tmpDir

    # Check that the db was created
    theDB = SQLiteDB()
    assert theDB.conf.sqlitePath == tmpDir
    assert os.path.isfile(dbFile)
    assert theDB._isNew is True

    # Close the DB and delete it, and check that new tables cannot be created
    theDB._conn.close()
    os.unlink(dbFile)
    assert not os.path.isfile(dbFile)

    caplog.clear()
    assert theDB._createMapTable() is False
    assert "Cannot operate on a closed database." in caplog.text

    caplog.clear()
    assert theDB._createAlertTable() is False
    assert "Cannot operate on a closed database." in caplog.text

    # DB connection set to None
    theDB._conn = None

    caplog.clear()
    assert theDB._createMapTable() is False
    assert "No database connection open" in caplog.text

    caplog.clear()
    assert theDB._createAlertTable() is False
    assert "No database connection open" in caplog.text

# END Test testDBSQLite_CreateTable


@pytest.mark.db
def testDBSQLite_DropTable(caplog, tmpConf, fncDir):
    """Test dropping tables DB."""
    dbFile = os.path.join(fncDir, "index.db")

    tmpConf.dbProvider = "sqlite"
    tmpConf.sqlitePath = fncDir

    # Check that the db was created
    theDB = SQLiteDB()
    assert theDB.conf.sqlitePath == fncDir
    assert os.path.isfile(dbFile)
    assert theDB._isNew is True

    # Check that the two tables were created
    cursor = theDB._conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    cursor.close()
    assert ("MapData",) in tables
    assert ("AlertData",) in tables

    # Block the sqlite execute command
    os.rename(os.path.join(fncDir, "index.db"), os.path.join(fncDir, "index.tmp"))
    assert theDB._dropMapTable() is False
    assert theDB._dropAlertTable() is False
    os.rename(os.path.join(fncDir, "index.tmp"), os.path.join(fncDir, "index.db"))

    # Drop the tables
    assert theDB._dropMapTable() is True
    assert theDB._dropAlertTable() is True

    # Check that the two tables are gone
    cursor = theDB._conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    cursor.close()
    assert ("MapData",) not in tables
    assert ("AlertData",) not in tables

    # Run the Purge twice. Should fail first and pass second
    assert theDB.purgeMapTable() is False
    assert theDB.purgeMapTable() is True
    assert theDB.purgeAlertTable() is False
    assert theDB.purgeAlertTable() is True

    # Check that the two tables were created again
    cursor = theDB._conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    cursor.close()
    assert ("MapData",) in tables
    assert ("AlertData",) in tables

    # DB connection set to None
    theDB._conn = None

    caplog.clear()
    assert theDB._dropMapTable() is False
    assert "No database connection open" in caplog.text

    caplog.clear()
    assert theDB._dropAlertTable() is False
    assert "No database connection open" in caplog.text

    # Cleanup
    os.unlink(dbFile)
    assert not os.path.isfile(dbFile)

# END Test testDBSQLite_DropTable


@pytest.mark.db
def testDBSQLite_SearchBounds(tmpConf, fncDir):
    """Test searchBounds function."""
    dbFile = os.path.join(fncDir, "index.db")

    tmpConf.dataPath = fncDir
    tmpConf.dbProvider = "sqlite"
    tmpConf.sqlitePath = fncDir

    theDB = SQLiteDB()
    assert theDB.conf.sqlitePath == fncDir
    assert os.path.isfile(dbFile)

    # MapData Table
    # =============

    # Insert some data
    uuidOne = str(uuid.uuid4())
    uuidTwo = str(uuid.uuid4())
    assert theDB.editMapRecord(
        cmd="insert", recordUUID=uuidOne, label="test label", source="test source",
        coordSystem="WGS84", west=1, south=1, east=5, north=5, area=16,
    ) is True
    assert theDB.editMapRecord(
        cmd="insert", recordUUID=uuidTwo, label="test label", source="test source",
        coordSystem="WGS84", west=6, south=6, east=10, north=10, area=16,
    ) is True

    cursor = theDB._conn.execute("SELECT ID FROM MapData;")
    records = cursor.fetchall()
    cursor.close()
    assert len(records) == 2

    # Search
    assert theDB.searchBounds("map", 0, 0, 3, 3)[0][1] == uuidOne
    assert theDB.searchBounds("map", 7, 7, 9, 9)[0][1] == uuidTwo
    assert len(theDB.searchBounds("map", 0, 0, 9, 9)) == 2

    # AlertData Table
    # ===============

    # Insert some data
    uuidOne = str(uuid.uuid4())
    uuidTwo = str(uuid.uuid4())
    mockDate = datetime(2021, 1, 1, 12, 0, 0)
    assert theDB.editAlertRecord(
        cmd="insert", recordUUID=uuidOne, identifier="mockAlert", sentDate=mockDate,
        sourcePath="mock.cap.xml", coordSystem="WGS84",
        west=1, south=1, east=5, north=5, altitude=100, ceiling=200, area=16
    ) is True
    assert theDB.editAlertRecord(
        cmd="insert", recordUUID=uuidTwo, identifier="mockAlert", sentDate=mockDate,
        sourcePath="mock.cap.xml", coordSystem="WGS84",
        west=6, south=6, east=10, north=10, altitude=100, ceiling=200, area=16
    ) is True

    cursor = theDB._conn.execute("SELECT ID FROM MapData;")
    records = cursor.fetchall()
    cursor.close()
    assert len(records) == 2

    # Search
    assert theDB.searchBounds("alert", 0, 0, 3, 3)[0][1] == uuidOne
    assert theDB.searchBounds("alert", 7, 7, 9, 9)[0][1] == uuidTwo
    assert len(theDB.searchBounds("alert", 0, 0, 9, 9)) == 2

    # Test Error
    theConn = theDB._conn
    theDB._conn = None
    assert theDB.searchBounds("map", 0, 0, 3, 3) is None
    assert theDB.searchBounds("alert", 0, 0, 3, 3) is None
    theDB._conn = theConn

    del theConn

# END Test testDBSQLite_SearchBounds


@pytest.mark.db
def testDBSQLite_EditMapRecord(tmpConf, fncDir, caplog):
    """Test MapData table INSERT and UPDATE."""
    dbFile = os.path.join(fncDir, "index.db")

    tmpConf.dbProvider = "sqlite"
    tmpConf.sqlitePath = fncDir

    # Check that the db was created
    theDB = SQLiteDB()
    assert theDB.conf.sqlitePath == fncDir
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
    assert theData[0] == (  # Unchanged
        1, uuidOne, "test label", "test source", "test adm name", "test adm ID",
        "2021-01-01T00:00:00", "2021-12-31T23:59:59", "WGS84", -10.0, -9.0, 8.0, 7.0, 272.0
    )
    assert theData[1] == (  # Updated
        2, uuidTwo, "new label", "new source", "new adm name", "new adm ID",
        "2020-01-01T00:00:00", "2020-12-31T23:59:59", "WGS84", -11.0, -10.0, 7.0, 6.0, 272.0
    )

    # SQL Error
    # =========

    # Insert: Non-unique UUID
    caplog.clear()
    assert theDB.editMapRecord(
        cmd="insert", recordUUID=uuidTwo, label="test label", source="test source",
        coordSystem="WGS84", west=-10, south=-9, east=8, north=7, area=272
    ) is False
    assert "UNIQUE constraint failed: MapData.UUID" in caplog.text

    # Update: Set a required argument to None
    caplog.clear()
    assert theDB.editMapRecord(
        cmd="update", recordUUID=uuidTwo, label=None, source="test source",
        coordSystem="WGS84", west=-10, south=-9, east=8, north=7, area=272
    ) is False
    assert "NOT NULL constraint failed: MapData.Label" in caplog.text

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


@pytest.mark.db
def testDBSQLite_EditAlertRecord(tmpConf, fncDir, caplog):
    """Test MapAlert table INSERT and UPDATE."""
    dbFile = os.path.join(fncDir, "index.db")

    tmpConf.dbProvider = "sqlite"
    tmpConf.sqlitePath = fncDir

    # Check that the db was created
    theDB = SQLiteDB()
    assert theDB.conf.sqlitePath == fncDir
    assert os.path.isfile(dbFile)
    assert theDB._isNew is True

    # Test Error Checking
    # ===================
    newUUID = str(uuid.uuid4())
    mockDate = datetime(2021, 1, 1, 12, 0, 0)

    # UUID Check
    caplog.clear()
    assert theDB.editAlertRecord(
        cmd="insert", recordUUID="stuff", identifier="mockAlert", sentDate=mockDate,
        sourcePath="mock.cap.xml", coordSystem="WGS84",
        west=-10, south=-9, east=8, north=7, altitude=100, ceiling=200, area=272
    ) is False
    assert "The UUID 'stuff' is not valid" in caplog.text

    # South-North Boundaries
    caplog.clear()
    assert theDB.editAlertRecord(
        cmd="insert", recordUUID=newUUID, identifier="mockAlert", sentDate=mockDate,
        sourcePath="mock.cap.xml", coordSystem="WGS84",
        west=-10, south=-200, east=8, north=7, altitude=100, ceiling=200, area=272
    ) is False
    assert "Coordinates must be in the range (-90 <= south < north <= 90)" in caplog.text

    caplog.clear()
    assert theDB.editAlertRecord(
        cmd="insert", recordUUID=newUUID, identifier="mockAlert", sentDate=mockDate,
        sourcePath="mock.cap.xml", coordSystem="WGS84",
        west=-10, south=-9, east=8, north=-17, altitude=100, ceiling=200, area=272
    ) is False
    assert "Coordinates must be in the range (-90 <= south < north <= 90)" in caplog.text

    # East-West Boundaries
    caplog.clear()
    assert theDB.editAlertRecord(
        cmd="insert", recordUUID=newUUID, identifier="mockAlert", sentDate=mockDate,
        sourcePath="mock.cap.xml", coordSystem="WGS84",
        west=-200, south=-9, east=8, north=7, altitude=100, ceiling=200, area=272
    ) is False
    assert "Coordinates must be in the range (-180 <= west < east <= 180)" in caplog.text

    caplog.clear()
    assert theDB.editAlertRecord(
        cmd="insert", recordUUID=newUUID, identifier="mockAlert", sentDate=mockDate,
        sourcePath="mock.cap.xml", coordSystem="WGS84",
        west=-10, south=-9, east=-18, north=7, altitude=100, ceiling=200, area=272
    ) is False
    assert "Coordinates must be in the range (-180 <= west < east <= 180)" in caplog.text

    # Altitue-Ceiling
    caplog.clear()
    assert theDB.editAlertRecord(
        cmd="insert", recordUUID=newUUID, identifier="mockAlert", sentDate=mockDate,
        sourcePath="mock.cap.xml", coordSystem="WGS84",
        west=-10, south=-9, east=-8, north=7, altitude=300, ceiling=200, area=272
    ) is False
    assert "Ceiling must be greater or equal to altitude" in caplog.text

    # Wrong DateTime
    caplog.clear()
    assert theDB.editAlertRecord(
        cmd="insert", recordUUID=newUUID, identifier="mockAlert", sentDate=None,
        sourcePath="mock.cap.xml", coordSystem="WGS84",
        west=-10, south=-9, east=-8, north=7, altitude=100, ceiling=200, area=272
    ) is False
    assert "SentDate must be a datetime object" in caplog.text

    # Database Insert
    # ===============
    newUUID = str(uuid.uuid4())

    # Insert Valid New Record
    assert theDB.editAlertRecord(
        cmd="insert", recordUUID=newUUID, identifier="mockAlert", sentDate=mockDate,
        sourcePath="mock.cap.xml", coordSystem="WGS84",
        west=-10, south=-9, east=8, north=7, altitude=100, ceiling=200, area=272
    ) is True

    cursor = theDB._conn.execute("SELECT * FROM AlertData;")
    theData = cursor.fetchall()
    assert theData[0] == (
        1, newUUID, "mockAlert", mockDate.isoformat(), "mock.cap.xml", "WGS84",
        -10.0, -9.0, 8.0, 7.0, 100.0, 200.0, 272.0
    )

    # Database Update
    # ===============
    assert theDB.editAlertRecord(
        cmd="update", recordUUID=newUUID, identifier="mockAlert2", sentDate=mockDate,
        sourcePath="mock2.cap.xml", coordSystem="WGS84",
        west=-11, south=-10, east=7, north=6, altitude=50, ceiling=150, area=272
    ) is True

    cursor = theDB._conn.execute("SELECT * FROM AlertData;")
    theData = cursor.fetchall()
    assert theData[0] == (
        1, newUUID, "mockAlert2", mockDate.isoformat(), "mock2.cap.xml", "WGS84",
        -11.0, -10.0, 7.0, 6.0, 50.0, 150.0, 272.0
    )

    # SQL Error
    # =========

    # Insert: Non-unique UUID
    caplog.clear()
    assert theDB.editAlertRecord(
        cmd="insert", recordUUID=newUUID, identifier="mockAlert", sentDate=mockDate,
        sourcePath="mock.cap.xml", coordSystem="WGS84",
        west=-10, south=-9, east=8, north=7, altitude=100, ceiling=200, area=272
    ) is False
    assert "UNIQUE constraint failed: AlertData.UUID" in caplog.text

    # Update: Set a required argument to None
    caplog.clear()
    assert theDB.editAlertRecord(
        cmd="update", recordUUID=newUUID, identifier=None, sentDate=mockDate,
        sourcePath="mock.cap.xml", coordSystem="WGS84",
        west=-10, south=-9, east=8, north=7, altitude=100, ceiling=200, area=272
    ) is False
    assert "NOT NULL constraint failed: AlertData.Identifier" in caplog.text

    # Other
    # =====
    newUUID = str(uuid.uuid4())

    # Invalid Command
    caplog.clear()
    assert theDB.editAlertRecord(
        cmd="blabla", recordUUID=newUUID, identifier=None, sentDate=mockDate,
        sourcePath="mock.cap.xml", coordSystem="WGS84",
        west=-10, south=-9, east=8, north=7, altitude=100, ceiling=200, area=272
    ) is False
    assert "Unknown command 'blabla'" in caplog.text

# END Test testDBSQLite_AlertMapRecord
