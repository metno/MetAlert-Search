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
import pytest

from ma_search import maintenance
from ma_search.utils import ingestCap


@pytest.mark.utils
def testUtil_Maintenance(filesDir):
    """Tests Maintenance function in ma_search.__init__
    """
    with pytest.raises(SystemExit):
        maintenance(["ingest_cap"])
    maintenance(["filename", "ingest_cap", filesDir])


@pytest.mark.utils
def testUtil_IngestCap(filesDir):
    """Tests ingestCap function in ma_search.utils, mainly covering
    lines, since ingestCap should be non-failing
    """
    with pytest.raises(SystemExit):
        ingestCap(["--notACommand"])
    with pytest.raises(SystemExit):
        ingestCap(["-h"])

    # Folder input
    ingestCap([filesDir])
    ingestCap(["--overwrite", filesDir])
    ingestCap(["--overwrite", "--recursive", filesDir])

    # Single file input
    filePath = os.path.join(filesDir, "mock.cap.xml")
    ingestCap([filePath])
    ingestCap(["--overwrite", filePath])

    # Path to file that does not exist
    ingestCap([os.path.join(filesDir, "nonExistentFile.xml")])
