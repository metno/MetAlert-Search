"""
MetAlert Search : Data Class Tests
==================================

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
import json
import shutil
import pytest

from tools import writeFile, causeOSError

from ma_search.data import Data


@pytest.mark.data
def testDataData_IngestAlertFile(monkeypatch, tmpConf, fncDir):
    """Test class initialisation."""
    tmpConf.dataPath = fncDir
    tmpConf.dbProvider = "sqlite"
    tmpConf.sqlitePath = fncDir

    data = Data()
    assert data.conf.dataPath == fncDir

    # Not parseable
    assert data.ingestAlertFile(None) is False

    # Empty CAP file
    testCap = os.path.join(fncDir, "test.cap.xml")
    writeFile(testCap, "<xml/>")
    assert data.ingestAlertFile(testCap) is False

    # No Polygon
    testCap = os.path.join(fncDir, "test.cap.xml")
    writeFile(testCap, (
        "<alert>"
        "<identifier>mockAlert</identifier>"
        "</alert>"
    ))
    assert data.ingestAlertFile(testCap) is False

    # Invalid Polygon
    testCap = os.path.join(fncDir, "test.cap.xml")
    writeFile(testCap, (
        "<alert>"
        "<identifier>mockAlert</identifier>"
        "<info>"
        "<area>"
        "<polygon>1,2 3,?</polygon>"
        "</area>"
        "</info>"
        "</alert>"
    ))
    assert data.ingestAlertFile(testCap) is False

    # Make a valid file
    testCap = os.path.join(fncDir, "good.cap.xml")
    writeFile(testCap, (
        "<alert>"
        "<identifier>mockAlert</identifier>"
        "<sent>2021-09-27T16:00:00Z</sent>"
        "<info>"
        "<area>"
        "<polygon>1,1 1,2 2,2 2,1 1,1</polygon>"
        "<altitude>0</altitude>"
        "<ceiling>1</ceiling>"
        "</area>"
        "</info>"
        "</alert>"
    ))

    # Can't make path
    with monkeypatch.context() as mp:
        mp.setattr("os.makedirs", causeOSError)
        assert data.ingestAlertFile(testCap) is False

    # Save properly
    assert data.ingestAlertFile(testCap) is True

    # Try to overwrite, and fail
    assert data.ingestAlertFile(testCap) is False

    # Allow overwrite
    assert data.ingestAlertFile(testCap, doReplace=True) is True

    # Check the JSON file
    jsonFile = os.path.join(
        fncDir, "alert_4", "alert_f", "a35e85f4-b0d1-5b1f-9db0-79007f49be07.json"
    )
    assert os.path.isfile(jsonFile)
    with open(jsonFile, mode="r") as inFile:
        jsonData = json.load(inFile)

    assert jsonData["identifier"] == "mockAlert"
    assert jsonData["source"] == testCap
    assert jsonData["polygon"]["type"] == "Polygon"
    assert jsonData["polygon"]["coordinates"] == [[
        [1.0, 1.0], [2.0, 1.0], [2.0, 2.0], [1.0, 2.0], [1.0, 1.0]
    ]]
    assert jsonData["altitude"] == 0.0
    assert jsonData["ceiling"] == 1.0
    assert jsonData["area"] == 1.0
    assert jsonData["bounds"]["east"] == 2.0
    assert jsonData["bounds"]["west"] == 1.0
    assert jsonData["bounds"]["north"] == 2.0
    assert jsonData["bounds"]["south"] == 1.0

# END Test testDataData_IngestAlertFile


@pytest.mark.data
def testDataData_IndexAlertMetaFile(tmpConf, fncDir, filesDir):
    """Test the indexAlertMetaFile method."""
    tmpConf.dataPath = fncDir
    tmpConf.dbProvider = None
    tmpConf.sqlitePath = None
    jsonFile = os.path.join(
        filesDir, "test_archive", "a35e85f4-b0d1-5b1f-9db0-79007f49be07.json"
    )

    # Before DB init
    data = Data()
    assert data.conf.dataPath == fncDir
    assert data.indexAlertMetaFile(jsonFile) is False

    # Init DB
    tmpConf.dbProvider = "sqlite"
    tmpConf.sqlitePath = fncDir
    data = Data()
    assert data.conf.dataPath == fncDir
    assert data.conf.dbProvider == "sqlite"
    assert data.conf.sqlitePath == fncDir

    # No such file
    assert data.indexAlertMetaFile(os.path.join(fncDir, "nowhere")) is False

    # Wrong UUID format
    testFile = os.path.join(fncDir, "a35e85f4b0d15b1f9db079007f49be07.json")
    writeFile(testFile, "")
    assert data.indexAlertMetaFile(testFile) is False

    # Wrong extension
    testFile = os.path.join(fncDir, "a35e85f4-b0d1-5b1f-9db0-79007f49be07.txt")
    writeFile(testFile, "")
    assert data.indexAlertMetaFile(testFile) is False

    # Invalid UUID
    testFile = os.path.join(fncDir, "a35e85f4-b0d1-5b1f-9db0-79007f49bXXX.json")
    writeFile(testFile, "")
    assert data.indexAlertMetaFile(testFile) is False

    # Load a valid file
    assert data.indexAlertMetaFile(jsonFile) is True

    # Load a valid file, but pass invalid data
    assert data.indexAlertMetaFile(jsonFile, data={}) is False

# END Test testDataData_IndexAlertMetaFile


@pytest.mark.data
def testDataData_RebuildAlertIndex(tmpConf, fncDir, filesDir):
    """Test the rebuildAlertIndex method."""
    tmpConf.dataPath = fncDir
    tmpConf.dbProvider = None
    tmpConf.sqlitePath = None

    # Before DB init
    data = Data()
    assert data.conf.dataPath == fncDir
    assert data.rebuildAlertIndex() is False

    # Init DB
    tmpConf.dbProvider = "sqlite"
    tmpConf.sqlitePath = fncDir
    data = Data()
    assert data.conf.dataPath == fncDir
    assert data.conf.dbProvider == "sqlite"
    assert data.conf.sqlitePath == fncDir

    # DB failure
    os.rename(os.path.join(fncDir, "index.db"), os.path.join(fncDir, "index.tmp"))
    assert data.rebuildAlertIndex() is False
    os.rename(os.path.join(fncDir, "index.tmp"), os.path.join(fncDir, "index.db"))

    # Build a mock archive
    dirsOne = os.path.join(fncDir, "alert_6", "alert_d")
    dirsTwo = os.path.join(fncDir, "alert_4", "alert_f")
    os.makedirs(dirsOne)
    os.makedirs(dirsTwo)
    fileOne = "957773d6-bc0d-5a72-be5e-27801d28e82b.json"
    fileTwo = "a35e85f4-b0d1-5b1f-9db0-79007f49be07.json"
    shutil.copyfile(
        os.path.join(filesDir, "test_archive", fileOne), os.path.join(dirsOne, fileOne)
    )
    shutil.copyfile(
        os.path.join(filesDir, "test_archive", fileTwo), os.path.join(dirsTwo, fileTwo)
    )

    # Add some junk files and folders
    mockOne = os.path.join(fncDir, "stuff")
    mockTwo = os.path.join(fncDir, "alert_6", "stuff")
    mockFile = os.path.join(fncDir, "alert_6", "alert_d", "something.txt")
    os.makedirs(mockOne)
    os.makedirs(mockTwo)
    writeFile(mockFile, "Hi!")

    # Reindex
    assert data.rebuildAlertIndex() is True

# END Test testDataData_RebuildAlertIndex
