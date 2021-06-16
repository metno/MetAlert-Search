"""
MetAlert Search : Main Package Init
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
import logging

from ma_search.config import Config

__package__ = "ma_search"
__version__ = "0.0.1"

def _initLogging(logObj):
    """Call to initialise logging
    """
    # Read environment variables
    wantLevel = os.environ.get("MA_SEARCH_LOGLEVEL", "INFO")
    logFile = os.environ.get("MA_SEARCH_LOGFILE", None)

    # Determine log level and format
    if hasattr(logging, wantLevel):
        logLevel = getattr(logging, wantLevel)
    else:
        print("Invalid logging level '%s' in environment variable MA_SEARCH_LOGLEVEL" % wantLevel)
        logLevel = logging.INFO

    if logLevel < logging.INFO:
        msgFormat = "[{asctime:}] {name:>28}:{lineno:<4d} {levelname:8s} {message:}"
    else:
        msgFormat = "{levelname:8s} {message:}"

    logFormat = logging.Formatter(fmt=msgFormat, style="{")
    logObj.setLevel(logLevel)

    # Create stream handlers
    hStdOut = logging.StreamHandler()
    hStdOut.setLevel(logLevel)
    hStdOut.setFormatter(logFormat)
    logObj.addHandler(hStdOut)

    if logFile is not None:
        hFile = logging.FileHandler(logFile, encoding="utf-8")
        hFile.setLevel(logLevel)
        hFile.setFormatter(logFormat)
        logObj.addHandler(hFile)

    return

# Logging Setup
# Must be called before the CONFIG object is created
logger = logging.getLogger(__name__)
_initLogging(logger)

# Create config object
CONFIG = Config()
