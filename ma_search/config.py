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

logger = logging.getLogger(__name__)

class Config():

    def __init__(self):

        # Paths
        self.pkgRoot = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

        # Core Values
        self.dbProvider = None

        # SQLite Settings
        self.sqlitePath = None

        # Internals
        self._rawConf = {}

        return

    def readConfig(self, configFile=None):
        """Read the config file. If the configFile variable is not set,
        the class will look for the file in the source root folder.
        """
        if configFile is None:
            configFile = os.path.join(self.pkgRoot, "config.yaml")

        if not os.path.isfile(configFile):
            logger.error("Config file not found: %s" % configFile)
            return False

        try:
            with open(configFile, mode="r", encoding="utf8") as inFile:
                self._rawConf = yaml.safe_load(inFile)
            logger.debug("Read config from: %s" % configFile)
        except Exception as e:
            logger.error("Could not read file: %s" % configFile)
            logger.error(str(e))
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
        """Read config values under 'main'.
        """
        conf = self._rawConf.get("main", {})

        self.dbProvider = conf.get("dbProvider", self.dbProvider)

        return

    def _readSQLiteSettings(self):
        """Read config values under 'sqlite'.
        """
        conf = self._rawConf.get("sqlite", {})

        self.sqlitePath = conf.get("sqlitePath", self.sqlitePath)

        return

    def _validateConfig(self):
        """Check config variable dependencies. It needs to be called after all
        the read functions when all settings have been handled.
        """
        valid = True

        if self.dbProvider == "sqlite":
            sqliteDir = os.path.dirname(self.sqlitePath)
            if not os.path.isdir(sqliteDir):
                logger.error("Cannot locate folder: %s" % sqliteDir)
                valid = False

        return valid

# END Class Config
