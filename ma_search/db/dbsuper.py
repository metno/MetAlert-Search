"""
MetAlert Search : Database Superclass
=====================================

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

import logging

import ma_search

logger = logging.getLogger(__name__)

class Database():

    def __init__(self):

        self.conf = ma_search.CONFIG

        return

    ##
    #  Methods
    ##

    def addMapEntry(self, data):
        """Add a new map entry to the database.
        Must be implemented in subclass.

        Parameters
        ----------
        data : dict
            A dictionary of the data to be added to the database.
        """
        raise NotImplementedError

    def updateMapEntry(self, uuid, data):
        """Update a map entry in the database.
        Must be implemented in subclass.

        Parameters
        ----------
        data : dict
            A dictionary of the data to be added to the database.
        uuid : str
            The UUID of the entry to be updated
        """
        raise NotImplementedError

# END Class Database