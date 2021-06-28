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

import json
import os
import pytest

from pathlib import Path

from tools import writeFile, causeOSError

import ma_search.common as co

@pytest.mark.core
def testCoreCommon_SafeMakeDir(tmpDir, caplog):
    """Test the safeMakeDir function."""
    newDir = os.path.join(tmpDir, "safemakedir")
    newFile = os.path.join(tmpDir, "safemakedir", "file.txt")
    # Wrong type
    assert co.safeMakeDir(None) is False

    # Success
    assert co.safeMakeDir(newDir) is True
    assert os.path.isdir(newDir)

    # Try again, should result in success
    assert co.safeMakeDir(newDir) is True
    assert os.path.isdir(newDir)

    # Make a dir where a file exists
    writeFile(newFile, "stuff")
    assert os.path.isfile(newFile)
    caplog.clear()
    assert co.safeMakeDir(newFile) is False
    assert "Could not create: %s" % newFile in caplog.text


@pytest.mark.core
def testCoreCommon_SafeWriteString(tmpDir, caplog, monkeypatch):
    """Test the safeWriteString function."""
    newFile = Path(tmpDir) / "file.txt"
    string = "dummy text \n\n  \n øä."

    # Wrong type
    caplog.clear()
    assert co.safeWriteString(None, string) is False
    assert "path should be string or pathlib.Path" in caplog.text

    # Success
    assert co.safeWriteString(newFile, string) is True
    assert newFile.read_text() == string

    # Try again, should result in success (overwrite)
    assert co.safeWriteString(newFile, string) is True
    assert newFile.read_text() == string

    # Try again with str, should result in success
    assert co.safeWriteString(str(newFile), string) is True
    assert newFile.read_text() == string

    # Typecheck of string
    caplog.clear()
    assert co.safeWriteString(newFile, ["", ""]) is False
    assert "Data should be string but is" in caplog.text

    # Check catching exception
    caplog.clear()
    with monkeypatch.context() as m:
        m.setattr(Path, "write_text", causeOSError)
        assert co.safeWriteString(newFile, string) is False
        assert f"Could not write to file: {newFile}" in caplog.text

@pytest.mark.parametrize("data, exp",
                         [("dummy øab", True),
                          (["a", "b"], True),
                          ({"a": 5, "b": [1, 2, "s"]}, True),
                          (Path("dummy"), False)])
@pytest.mark.core
def testCoreCommon_safeWriteJson(data, exp, tmpDir, caplog):
    """Test the safeWriteJson function."""
    newFile = Path(tmpDir) / "file.txt"

    # check execution
    caplog.clear()
    assert co.safeWriteJson(newFile, data) is exp
    if exp is False:
        assert "Could not write to file" in caplog.text

@pytest.mark.core
def testCoreCommon_SafeLoadString(tmpDir, caplog, monkeypatch):
    """Test the safeLoadString function."""
    newFile = Path(tmpDir) / "file.txt"
    string = "dummy text \n\n  \n øä."
    newFile.write_text(string)

    # Wrong type
    caplog.clear()
    assert co.safeLoadString(None) is None
    assert "path should be str or pathlib.Path" in caplog.text

    # Success
    assert co.safeLoadString(newFile) == string

    # Try again with str, should result in success
    assert co.safeLoadString(str(newFile)) == string

    # Check catching exception
    caplog.clear()
    with monkeypatch.context() as m:
        m.setattr(Path, "read_text", causeOSError)
        assert co.safeLoadString(newFile) is None
        assert f"Could not read from file: {newFile}" in caplog.text

@pytest.mark.parametrize("data",
                         ["dummy øab", ["a", "b"], {"a": 5, "b": [1, 2, "s"]}])
@pytest.mark.core
def testCoreCommon_safeLoadJson(data, tmpDir, caplog):
    """Test the safeLoadJson function."""
    newFile = Path(tmpDir) / "file.txt"
    with newFile.open("w", encoding="UTF-8") as f:
        json.dump(data, f)

    # check execution
    caplog.clear()
    assert co.safeLoadJson(newFile) == data

    # catch exceptions -- string is not json conform
    string = "[{,,]."
    newFile.write_text(string)
    caplog.clear()
    assert co.safeLoadJson(newFile) is None
    assert f"Could not deserialize json from file: {newFile}" in caplog.text
    assert "JSONDecodeError" in caplog.text

# END Test testCoreCommon_SafeMakeDir
