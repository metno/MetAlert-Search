"""
MetAlert Search : Main Config
=============================

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
import yaml
import logging

from ma_search.common import logException

logger = logging.getLogger(__name__)

class Config():
    """Main config class wrapping the config yaml file."""

    def __init__(self):

        # Internals
        self._pkgRoot = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        self._rawConf = {}

        # Config Settings
        # ===============
        # These should only be set from file.

        # Core Values
        self.dbProvider = None
        self.dataPath = None

        # SQLite Settings
        self.sqlitePath = None

        return

    def readConfig(self, configFile=None):
        """Read the config file.

        Parameters
        ----------
        configFile : str or None, optional
            The config file to be loaded. If None, pkgRoot/config.yaml
            is attempted loaded instead.

        Returns
        -------
        bool
            True if successful, False if anything failed.
        """
        if configFile is None:
            configFile = os.path.join(self._pkgRoot, "config.yaml")

        if not os.path.isfile(configFile):
            logger.error("Config file not found: %s" % configFile)
            return False

        try:
            with open(configFile, mode="r", encoding="utf8") as inFile:
                self._rawConf = yaml.safe_load(inFile)
            logger.debug("Read config from: %s" % configFile)
        except Exception:
            logger.error("Could not read file: %s" % configFile)
            logException()
            return False

        # Read Values
        self._readCoreSettings()
        self._readSQLiteSettings()

        valid = self._validateConfig()

        return valid

    ##
    #  Internal Functions
    ##

    def _readCoreSettings(self):
        """Read config values under 'main'."""
        conf = self._rawConf.get("main", {})

        self.dbProvider = conf.get("dbProvider", self.dbProvider)
        self.dataPath = conf.get("dataPath", self.dataPath)

        return

    def _readSQLiteSettings(self):
        """Read config values under 'sqlite'."""
        conf = self._rawConf.get("sqlite", {})

        self.sqlitePath = conf.get("sqlitePath", self.sqlitePath)

        return

    def _validateConfig(self):
        """Check config variable dependencies.

        This function should be called after all the read functions
        when all settings have been handled.

        Returns
        -------
        bool
            True if all settings passed check, False otherwise.
        """
        valid = True

        if not self._checkFolderExists(self.dataPath, "dataPath"):
            self.dataPath = None
            valid = False

        if self.dbProvider == "sqlite":
            if not self._checkFolderExists(self.sqlitePath, "sqlitePath"):
                self.sqlitePath = None
                valid = False

        return valid

    def _checkFolderExists(self, path, name):
        """Check if a folder exists.

        Parameters
        ----------
        path : str
            The path to be checked.
        name : str
            The setting name for use when reporting an error.

        Returns
        -------
        bool
            True if exists and is a string, False otherwise.
        """
        if isinstance(path, str):
            if os.path.isdir(path):
                return True
            else:
                logger.error("Cannot locate folder: %s" % path)
                return False
        else:
            logger.error("Setting '%s' must be a string" % name)
            return False

# END Class Config
