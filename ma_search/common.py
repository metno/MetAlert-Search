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


def logException():
    """Format and write the last exception to the logger object.

    Format and log the content of an exception message. Intended to be
    used in try/except structures to make the exception easier to read.
    """
    exType, exValue, _ = sys.exc_info()
    logger.error("%s: %s" % (exType.__name__, str(exValue).strip("'")))
