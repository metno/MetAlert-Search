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
import pytest

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
