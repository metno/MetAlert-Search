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
import json
import pytest

from tools import readFile, writeFile, causeOSError

from ma_search.common import (
    checkFloat, preparePath, safeMakeDir, safeMakeDirs, safeWriteString,
    safeWriteJson, safeLoadString, safeLoadJson, checkUUID
)


@pytest.mark.core
def testCoreCommon_CheckFloat():
    """Test the checkFloat function."""
    assert checkFloat(None, 3.0, True) is None
    assert checkFloat("None", 3.0, True) is None
    assert checkFloat(None, 3.0, False) == 3.0
    assert checkFloat(1, 3, False) == 1.0
    assert checkFloat(1.0, 3, False) == 1.0
    assert checkFloat(True, 3, False) == 1.0

# END Test testCoreCommon_CheckFloat


@pytest.mark.core
def testCoreCommon_PreparePath(fncDir, monkeypatch):
    """Test the preparePath function."""
    # Wrong type
    assert preparePath(os.path.join(fncDir, "whatever"), "test", None) is None
    assert preparePath(fncDir, "test", None) is None
    assert preparePath(fncDir, "test", "0123456789abcdef") is None

    # Valid Path
    tUUID = "85892716-b07a-4717-9685-331d582ad734"
    tPath = os.path.join(fncDir, "test_6", "test_1")
    assert preparePath(fncDir, "test", tUUID) == tPath

    # Second Pass
    assert preparePath(fncDir, "test", tUUID) == tPath

    # Make safeMakeDirs fail
    with monkeypatch.context() as mp:
        mp.setattr(os, "makedirs", causeOSError)
        assert preparePath(fncDir, "test", tUUID) is None

# END Test testCoreCommon_PreparePath


@pytest.mark.core
def testCoreCommon_SafeMakeDir(fncDir, caplog):
    """Test the safeMakeDir function."""
    newDir = os.path.join(fncDir, "safemakedir")
    newFile = os.path.join(fncDir, "safemakedir", "file.txt")

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


@pytest.mark.core
def testCoreCommon_SafeMakeDirs(fncDir, caplog):
    """Test the safeMakeDirs function."""
    newDir = os.path.join(fncDir, "safemakedirs")
    newFile = os.path.join(fncDir, "safemakedirs", "file.txt")

    # Wrong type
    assert safeMakeDir(None) is False

    # Success
    assert safeMakeDirs(newDir) is True
    assert os.path.isdir(newDir)

    # Try again, should result in success
    assert safeMakeDirs(newDir) is True
    assert os.path.isdir(newDir)

    # Make a dir where a file exists
    writeFile(newFile, "stuff")
    assert os.path.isfile(newFile)
    caplog.clear()
    assert safeMakeDirs(newFile) is False
    assert "Could not create folders: %s" % newFile in caplog.text

# END Test testCoreCommon_SafeMakeDirs


@pytest.mark.core
def testCoreCommon_SafeWriteString(fncDir, caplog, monkeypatch):
    """Test the safeWriteString function."""
    newFile = os.path.join(fncDir, "file.txt")
    string = "test text \n\n  \n øä."

    # Wrong type
    caplog.clear()
    assert safeWriteString(None, string) is False
    assert "Could not write to file" in caplog.text

    # Success
    assert safeWriteString(newFile, string) is True
    assert readFile(newFile) == string

    # Try again, should result in success (overwrite)
    assert safeWriteString(newFile, string) is True
    assert readFile(newFile) == string

    # Other datatypes
    caplog.clear()
    assert safeWriteString(newFile, ["", ""]) is True
    assert readFile(newFile) == str(["", ""])

    # Check catching exception
    caplog.clear()
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)
        assert safeWriteString(newFile, string) is False
        assert "Could not write to file" in caplog.text

# END Test testCoreCommon_SafeWriteString


@pytest.mark.core
def testCoreCommon_SafeWriteJson(fncDir, caplog):
    """Test the safeWriteJson function."""
    newFile = os.path.join(fncDir, "file.txt")

    # Check execution
    assert safeWriteJson(newFile, "dummy øab") is True
    assert safeWriteJson(newFile, ["a", "b"]) is True
    assert safeWriteJson(newFile, {"a": 5, "b": [1, 2, "s"]}) is True

    # Non-serialisable
    class mockClass:
        pass

    caplog.clear()
    assert safeWriteJson(newFile, mockClass) is False
    assert "Could not write to file" in caplog.text

# END Test testCoreCommon_SafeWriteJson


@pytest.mark.core
def testCoreCommon_SafeLoadString(fncDir, caplog, monkeypatch):
    """Test the safeLoadString function."""
    newFile = os.path.join(fncDir, "file.txt")
    string = "mock text \n\n  \n øä."
    writeFile(newFile, string)

    # Wrong type
    caplog.clear()
    assert safeLoadString(None) is None
    assert "Could not read from file" in caplog.text

    # Success
    assert safeLoadString(newFile) == string

    # Try again with str, should result in success
    assert safeLoadString(str(newFile)) == string

    # Check catching exception
    caplog.clear()
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)
        assert safeLoadString(newFile) is None
        assert "Could not read from file" in caplog.text

# END Test testCoreCommon_SafeLoadString


@pytest.mark.core
def testCoreCommon_SafeLoadJson(fncDir, caplog):
    """Test the safeLoadJson function."""
    newFile = os.path.join(fncDir, "file.txt")

    # Check execution
    data = "dummy øab"
    writeFile(newFile, json.dumps(data))
    assert safeLoadJson(newFile) == data

    data = ["a", "b"]
    writeFile(newFile, json.dumps(data))
    assert safeLoadJson(newFile) == data

    data = {"a": 5, "b": [1, 2, "s"]}
    writeFile(newFile, json.dumps(data))
    assert safeLoadJson(newFile) == data

    # catch exceptions -- string is not json conform
    string = "[{,,]."
    writeFile(newFile, string)
    caplog.clear()
    assert safeLoadJson(newFile) is None
    assert f"Could not deserialize json from file: {newFile}" in caplog.text
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
