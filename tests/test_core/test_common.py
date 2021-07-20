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

from ma_search.common import (
    safeMakeDir, safeWriteString, safeWriteJson, safeLoadString,
    safeLoadJson, checkUUID
)


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


@pytest.mark.core
def testCoreCommon_SafeWriteString(tmpDir, caplog, monkeypatch):
    """Test the safeWriteString function."""
    newFile = Path(tmpDir) / "file.txt"
    string = "dummy text \n\n  \n øä."

    # Wrong type
    caplog.clear()
    assert safeWriteString(None, string) is False
    assert "path should be string or pathlib.Path" in caplog.text

    # Success
    assert safeWriteString(newFile, string) is True
    assert newFile.read_text() == string

    # Try again, should result in success (overwrite)
    assert safeWriteString(newFile, string) is True
    assert newFile.read_text() == string

    # Try again with str, should result in success
    assert safeWriteString(str(newFile), string) is True
    assert newFile.read_text() == string

    # Typecheck of string
    caplog.clear()
    assert safeWriteString(newFile, ["", ""]) is False
    assert "Data should be string but is" in caplog.text

    # Check catching exception
    caplog.clear()
    with monkeypatch.context() as mp:
        mp.setattr(Path, "write_text", causeOSError)
        assert safeWriteString(newFile, string) is False
        assert f"Could not write to file: {newFile}" in caplog.text


@pytest.mark.core
@pytest.mark.parametrize(
    "data, exp", [
        ("dummy øab", True),
        (["a", "b"], True),
        ({"a": 5, "b": [1, 2, "s"]}, True),
        (Path("dummy"), False)
    ]
)
def testCoreCommon_safeWriteJson(data, exp, tmpDir, caplog):
    """Test the safeWriteJson function."""
    newFile = Path(tmpDir) / "file.txt"

    # Check execution
    caplog.clear()
    assert safeWriteJson(newFile, data) is exp
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
    assert safeLoadString(None) is None
    assert "path should be str or pathlib.Path" in caplog.text

    # Success
    assert safeLoadString(newFile) == string

    # Try again with str, should result in success
    assert safeLoadString(str(newFile)) == string

    # Check catching exception
    caplog.clear()
    with monkeypatch.context() as m:
        m.setattr(Path, "read_text", causeOSError)
        assert safeLoadString(newFile) is None
        assert f"Could not read from file: {newFile}" in caplog.text


@pytest.mark.core
@pytest.mark.parametrize("data", ["dummy øab", ["a", "b"], {"a": 5, "b": [1, 2, "s"]}])
def testCoreCommon_safeLoadJson(data, tmpDir, caplog):
    """Test the safeLoadJson function."""
    newFile = Path(tmpDir) / "file.txt"
    with newFile.open("w", encoding="UTF-8") as f:
        json.dump(data, f)

    # Check execution
    caplog.clear()
    assert safeLoadJson(newFile) == data

    # Catch exceptions: string is not json conform
    string = "[{,,]."
    newFile.write_text(string)
    caplog.clear()
    assert safeLoadJson(newFile) is None
    assert f"Could not deserialise json from file: {newFile}" in caplog.text
    assert "JSONDecodeError" in caplog.text

# END Test testCoreCommon_SafeMakeDir


@pytest.mark.core
def testCoreCommon_CheckUUID():
    """Test the validateUUID function."""
    testUUID = "e1600641-e537-4d40-8d2f-2fd2c7c457c6"
    assert checkUUID(None) is None
    assert checkUUID("xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx") is None
    assert checkUUID("e1600641e5374d408d2f2fd2c7c457c6") == testUUID
    assert checkUUID("e1600641-e537-4d40-8d2f-2fd2c7c457c6") == testUUID

# END Test testCoreCommon_CheckUUID
