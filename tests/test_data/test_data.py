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
