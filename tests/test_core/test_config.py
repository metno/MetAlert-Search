"""
MetAlert Search : Config Class Test
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
import pytest

from tools import causeOSError, writeFile

from ma_search.config import Config

@pytest.mark.core
def testCoreConfig_ReadFile(tmpDir, monkeypatch):
    """Test reading config file.
    """
    theConf = Config()

    # Read some values and see that we get them
    confFile = os.path.join(tmpDir, "config.yaml")
    writeFile(confFile, (
        "groupOne:\n"
        "  keyOne: 1\n"
        "  keyTwo: two\n"
        "  keyThree: null\n"
        "  keyFour:\n"
        "    - value1\n"
        "    - value2\n"
    ))

    # Fake path
    assert theConf.readConfig(configFile="not_a_real_file") is False

    # Cause the open command to fail
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)
        assert theConf.readConfig(configFile=confFile) is False

    # Successful raw read
    assert theConf.readConfig(configFile=confFile) is True

    # Check the values read
    assert theConf._rawConf["groupOne"]["keyOne"] == 1
    assert theConf._rawConf["groupOne"]["keyTwo"] == "two"
    assert theConf._rawConf["groupOne"]["keyThree"] is None
    assert theConf._rawConf["groupOne"]["keyFour"] == ["value1", "value2"]

    # Read with no file path set, but a folder that contains the test file
    theConf._pkgRoot = tmpDir
    assert theConf.readConfig(configFile=None) is True
    assert theConf._rawConf["groupOne"]["keyOne"] == 1
    assert theConf._rawConf["groupOne"]["keyTwo"] == "two"
    assert theConf._rawConf["groupOne"]["keyThree"] is None
    assert theConf._rawConf["groupOne"]["keyFour"] == ["value1", "value2"]

# END Test testCoreConfig_ReadFile

@pytest.mark.core
def testCoreConfig_Validate(tmpDir, caplog):
    """Test that the class reads all settings and validates them.
    """
    theConf = Config()

    # SQLite Settings
    theConf.dbProvider = "sqlite"

    # Wrong type
    caplog.clear()
    theConf.sqlitePath = None
    assert theConf._validateConfig() is False
    assert "Setting 'sqlitePath' must be a string" in caplog.text

    # Not a valid path
    caplog.clear()
    theConf.sqlitePath = "/not/a/valid/path/"
    assert theConf._validateConfig() is False
    assert "Cannot locate folder:" in caplog.text

    # Folder exists (the file does not need to exist)
    theConf.sqlitePath = tmpDir
    assert theConf._validateConfig() is True

# END Test testCoreConfig_Validate
