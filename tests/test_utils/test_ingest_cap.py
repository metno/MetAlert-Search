"""
MetAlert Search : Cap Ingestor Util Tests
=========================================

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

from tools import writeFile

from ma_search.utils import ingestCap


@pytest.mark.utils
def testUtil_IngestCap(filesDir, fncDir, tmpConf, caplog):
    """Tests ingestCap function in ma_search.utils, mainly covering
    lines, since ingestCap should be non-failing
    """
    tmpConf.dataPath = fncDir

    # Make a valid file
    testCap = os.path.join(fncDir, "good.cap.xml")
    writeFile(testCap, (
        "<alert>"
        "<identifier>mockAlert</identifier>"
        "<info>"
        "<area>"
        "<polygon>1,1 1,2 2,2 2,1 1,1</polygon>"
        "<altitude>0</altitude>"
        "<ceiling>1</ceiling>"
        "</area>"
        "</info>"
        "</alert>"
    ))

    with pytest.raises(SystemExit):
        ingestCap(["--notACommand"])
    with pytest.raises(SystemExit):
        ingestCap(["-h"])

    ingestCap([testCap])

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

    # Ingest again
    caplog.clear()
    ingestCap([testCap])
    assert (
        "CAP file with identifier 'mockAlert' already exists and is not being overwritten"
    ) in caplog.text

    # Ingest overwrite
    caplog.clear()
    ingestCap(["--overwrite", testCap])
    assert (
        "CAP file with identifier 'mockAlert' already exists and is not being overwritten"
    ) not in caplog.text

    # Path to file that does not exist
    ingestCap([os.path.join(filesDir, "nonExistentFile.xml")])
