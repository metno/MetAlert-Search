"""
MetAlert Search : Package Init Test
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
import logging

import ma_search

from tools import readFile

from ma_search.config import Config

@pytest.mark.core
def testCoreInit_Init():
    """Test the package initialisation.
    """
    assert ma_search.__version__
    assert isinstance(ma_search.CONFIG, Config)

# END Test testCoreInit_Init

@pytest.mark.core
def testCoreInit_Logger(tmpDir):
    """Test the logger initialisation.
    """
    os.environ["MA_SEARCH_LOGLEVEL"] = "DEBUG"
    logger = logging.getLogger(__name__)
    ma_search._initLogging(logger)
    assert logger.getEffectiveLevel() == logging.DEBUG

    os.environ["MA_SEARCH_LOGLEVEL"] = "INVALID"
    logger = logging.getLogger(__name__)
    ma_search._initLogging(logger)
    assert logger.getEffectiveLevel() == logging.INFO

    # Test log file
    logFile = os.path.join(tmpDir, "test.log")
    if os.path.isfile(logFile):
        os.unlink(logFile)

    os.environ["MA_SEARCH_LOGLEVEL"] = "DEBUG"
    os.environ["MA_SEARCH_LOGFILE"] = logFile
    logger = logging.getLogger(__name__)
    ma_search._initLogging(logger)
    assert os.path.isfile(logFile)
    logger.debug("Some log message")
    assert readFile(logFile).strip().endswith("Some log message")

# END Test testCoreInit_Logger

@pytest.mark.core
def testCoreInit_ApiMain(monkeypatch, rootDir):
    """Test the API entry point function
    """
    # class mockAPI():
    #     def __init__(self):
    #         pass

    #     def run(self):
    #         return

    exampleConf = os.path.join(rootDir, "example_config.yaml")
    monkeypatch.setenv("MA_SEARCH_CONFIG", exampleConf)
    # monkeypatch.setattr("ma_search.api.App", mockAPI)

    # Invalid config
    with pytest.raises(SystemExit) as sysExit:
        ma_search.apiMain()

    assert sysExit.type == SystemExit
    assert sysExit.value.code == 1

    # Valid config
    monkeypatch.setattr(Config, "_validateConfig", lambda *a: True)
    with pytest.raises(SystemExit) as sysExit:
        ma_search.apiMain()

    assert sysExit.type == SystemExit
    assert sysExit.value.code is None

# END Test testCoreInit_ApiMain
