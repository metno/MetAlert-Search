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
import uuid
import pytest

from tools import writeFile

from ma_search.utils import ingestCap
from ma_search.common import preparePath

UUID_NS = uuid.uuid5(uuid.NAMESPACE_URL, "metalert.met.no")


class MockCap:
    def __init__(self, identifier):
        self.identifier = identifier
        return

    def write(self, path):
        # Make a valid file
        writeFile(path, (
            "<alert>"
            "<identifier>"+self.identifier+"</identifier>"
            "<info>"
            "<area>"
            "<polygon>1,1 1,2 2,2 2,1 1,1</polygon>"
            "<altitude>0</altitude>"
            "<ceiling>1</ceiling>"
            "</area>"
            "</info>"
            "</alert>"
        ))

    def validate(self, jsonFile, sourcePath):
        with open(jsonFile, mode="r") as inFile:
            jsonData = json.load(inFile)

        assert jsonData["identifier"] == self.identifier
        assert jsonData["source"] == sourcePath
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

    def namespacePath(self, directory):
        fUUID = str(uuid.uuid5(UUID_NS, self.identifier))
        fPath = preparePath(directory, "alert", fUUID)
        return os.path.join(fPath,  f"{fUUID}.json")


@pytest.mark.utils
def testUtil_IngestCap(filesDir, fncDir, tmpConf, caplog):
    """Tests ingestCap function in ma_search.utils, mainly covering
    lines, since ingestCap should be non-failing
    """
    tmpConf.dataPath = fncDir

    with pytest.raises(SystemExit):
        ingestCap(["--notACommand"])
    with pytest.raises(SystemExit):
        ingestCap(["-h"])
    mockAlert = MockCap("mockAlert")

    testCap = os.path.join(fncDir, "good.cap.xml")
    mockAlert.write(testCap)
    ingestCap([testCap])

    # Check the JSON file
    jsonFile = mockAlert.namespacePath(fncDir)
    assert os.path.isfile(jsonFile)
    mockAlert.validate(jsonFile, testCap)

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

    # Ingest directory
    caplog.clear()
    ingestCap([fncDir])
    assert (
        "CAP file with identifier 'mockAlert' already exists and is not being overwritten"
    ) in caplog.text

    # Ingest recursive
    caplog.clear()
    os.makedirs(os.path.join(fncDir, "tmp"))
    testAnotherCap = os.path.join(fncDir, "tmp", "gooder.cap.xml")
    mockAlert2 = MockCap("mockerAlert")
    mockAlert2.write(testAnotherCap)

    ingestCap(["--recursive", fncDir])
    assert (
        "CAP file with identifier 'mockAlert' already exists and is not being overwritten"
    ) in caplog.text
    assert (
        "CAP file with identifier 'mockerAlert' already exists and is not being overwritten"
    ) not in caplog.text

    # Check the JSON files
    jsonFile = mockAlert.namespacePath(fncDir)
    assert os.path.isfile(jsonFile)
    mockAlert.validate(jsonFile, testCap)

    jsonFile = mockAlert2.namespacePath(fncDir)
    assert os.path.isfile(jsonFile)
    mockAlert2.validate(jsonFile, testAnotherCap)

    # Path to file that does not exist
    ingestCap([os.path.join(filesDir, "nonExistentFile.xml")])
