"""
MetAlert Search : CapXML Tests
==============================

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
import lxml
import pytest

from tools import writeFile

from ma_search.data.capxml import CapXML


@pytest.mark.data
def testDataCap_Init(filesDir):
    """Test class initialisation."""
    with pytest.raises(OSError):
        CapXML("NONE")

    dataPath = os.path.join(filesDir, "METfare-20210921T070421.cap.xml")
    cap = CapXML(dataPath)

    assert cap._captree is not None
    assert isinstance(cap._captree, lxml.etree._ElementTree)
    assert cap["identifier"] == "2.49.0.1.578.0.210921070421906.1705"
    assert cap["WrongName"] is None

# END Test testDataCap_Init


@pytest.mark.data
def testDataCap_ParseInfo(filesDir):
    """Test parseInfo method with a correctly formatted capxml-file,
    and a capxml-file with missing entries.
    """
    succPath = os.path.join(filesDir, "mock.cap.xml")
    failPath = os.path.join(filesDir, "mockFailing.cap.xml")

    cap = CapXML(succPath)

    # Check variables explicitly parsed
    assert cap["identifier"] == "mockAlert"
    assert cap["sent"] == "2001-03-04T05:06:07+00:00"
    assert cap["polygon"] == [[(12., 34.), (56., 78.)]]
    assert cap["circle"] == [(1.234, 5.67, 89)]
    assert cap["geocode"] == [("value1", "123"), ("value2", "123")]
    assert cap["areaDesc"] == {"no": "Area1"}
    assert cap["altitude"] == 200.
    assert cap["ceiling"] == 100.

    cap = CapXML(failPath)

    # Check variables explicitly parsed
    assert cap["identifier"] is None
    assert cap["sent"] is None
    assert cap["polygon"] == [[(0.0, 1.23)]]
    assert cap["circle"] == [(1.234, 5.67, 0)]
    assert cap["geocode"] == [("value1", "123")]
    assert cap["areaDesc"] == {"en": "Area1"}
    assert cap["altitude"] is None
    assert cap["ceiling"] is None

# END Test testDataCap_ParseInfo


@pytest.mark.data
def testDataCap_AsGeoJson(filesDir, fncDir):
    """Test the asGeoJson method of the CapXML class."""
    # No Polygon
    emptyFile = os.path.join(fncDir, "empty.xml")
    writeFile(emptyFile, "<xml/>")
    cap = CapXML(emptyFile)
    assert cap["polygon"] is None
    assert cap.asGeoJson() is None

    # Polygon
    cap = CapXML(os.path.join(filesDir, "mock.cap.xml"))
    assert cap["polygon"] == [
        [(12.0, 34.0), (56.0, 78.0)]
    ]
    assert cap.asGeoJson() == {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [(34.0, 12.0), (78.0, 56.0)]
            ]
        }
    }

    # MultiPolygon
    cap = CapXML(os.path.join(filesDir, "mockMulti.cap.xml"))
    assert cap["polygon"] == [
        [(12.0, 34.0), (56.0, 78.0)],
        [(87.0, 65.0), (43.0, 21.0)]
    ]
    assert cap.asGeoJson() == {
        "type": "Feature",
        "geometry": {
            "type": "MultiPolygon",
            "coordinates": [
                [(34.0, 12.0), (78.0, 56.0)],
                [(65.0, 87.0), (21.0, 43.0)]
            ]
        }
    }

# END Test testDataCap_AsGeoJson
