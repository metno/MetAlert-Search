"""
MetAlert Search : Common Functions
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
import sys
import json
import logging

logger = logging.getLogger(__name__)


def safeMakeDir(path):
    """Create a folder and return if successful.

    Parameters
    ----------
    path : str
        The path to the folder to be created/checked.

    Returns
    -------
    bool
        True if successful, False otherwise.
    """
    if not isinstance(path, str):
        return False

    if os.path.isdir(path):
        return True

    try:
        os.mkdir(path)
    except Exception:
        logger.error("Could not create: %s" % str(path))
        logException()
        return False

    return True


def safeWriteString(path, data):
    """Write data to file and log exceptions.

    Parameters
    ----------
    path : str
        Path to the file to be created.
    data : Any
        Data to be dumped.

    Returns
    -------
    bool
        True if successful, False otherwise.
    """
    try:
        with open(path, mode="w", encoding="utf-8") as outFile:
            outFile.write(str(data))
        return True
    except Exception:
        logger.error("Could not write to file: %s", path)
        logException()
        return False


def safeWriteJson(path, data, **kwargs):
    """Write data to a json file and log exceptions.

    Parameters
    ----------
    path : str
        Path to the file to be created.
    data : list. dict
        Data to be dumped. Has to be serializable.
    **kwargs : dict
        Additional kwargs to json.dump. "ensure_ascii" defaults to
        False.

    Returns
    -------
    bool
        True if successful, False otherwise.
    """
    kwargs.setdefault("ensure_ascii", False)
    try:
        string = json.dumps(data, **kwargs)
        safeWriteString(path, string)
        return True
    except Exception:
        logger.error("Could not write to file: %s", path)
        logException()
        return False


def safeLoadString(path):
    """Load string from file and log exceptions.

    Parameters
    ----------
    fn : str
        Path to the file to be read.

    Returns
    -------
    str or None
        Data as string if successful, None otherwise.
    """
    try:
        with open(path, mode="r", encoding="utf-8") as inFile:
            return inFile.read()
    except Exception:
        logger.error("Could not read from file: %s", path)
        logException()
        return None


def safeLoadJson(path, **kwargs):
    """Load data from a json file and log exceptions.

    Parameters
    ----------
    path : str
        Path to the file to be read.
    **kwargs : dict
        Additional kwargs to json.loads

    Returns
    -------
    :obj:`object`
        Data from json file if successful, otherwise None.
    """
    try:
        string = safeLoadString(path)
        return json.loads(string, **kwargs)
    except Exception:
        logger.error("Could not deserialize json from file: %s", path)
        logException()
        return None


def logException():
    """Format and write the last exception to the logger object.

    Format and log the content of an exception message. Intended to be
    used in try/except structures to make the exception easier to read.
    """
    exType, exValue, _ = sys.exc_info()
    logger.error("%s: %s" % (exType.__name__, str(exValue).strip("'")))
