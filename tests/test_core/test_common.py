"""
MetAlert Search : Common Functions Tests
========================================

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

from tools import writeFile

from ma_search.common import safeMakeDir

@pytest.mark.core
def testCoreCommon_SafeMakeDir(tmpDir, caplog):
    """Test the safeMakeDir function."""
    newDir = os.path.join(tmpDir, "safemakedir")
    newFile = os.path.join(tmpDir, "safemakedir", "file.txt")
    # Wrong type
    assert safeMakeDir(None) is False

    # Success
    assert safeMakeDir(newDir) is True
    assert os.path.isdir(newDir)

    # Try again, should result in success
    assert safeMakeDir(newDir) is True
    assert os.path.isdir(newDir)

    # Make a dir where a file exists
    writeFile(newFile, "stuff")
    assert os.path.isfile(newFile)
    caplog.clear()
    assert safeMakeDir(newFile) is False
    assert "Could not create: %s" % newFile in caplog.text

# END Test testCoreCommon_SafeMakeDir
