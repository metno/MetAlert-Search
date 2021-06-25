"""
MetAlert Search : Data Tests
============================

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
from pathlib import Path

import pytest
import shapely.geometry as geometry
from ma_search.data.shape import Shape
from shapely.geometry import MultiPolygon, Polygon


@pytest.mark.data
def testDataShape_Init(tmpConf, tmpDir, caplog):

    dataPath = Path(tmpDir) / "data"
    dataPath.mkdir(exist_ok=True)
    tmpConf.dataPath = dataPath

    # initialization runs
    shape = Shape("")
    shape._validateUuid4 = lambda: None
    assert isinstance(shape, Shape)

    # check error if file does not exist
    caplog.clear()
    uuid = '33d0c48f-b58c-4b1a-b224-e93b03393cb3'
    shape = Shape(uuid)
    assert "does not exist" in caplog.text

    # but runs if it exists
    Path(dataPath/uuid).with_suffix(".geojson").touch()
    caplog.clear()
    shape = Shape(uuid)
    assert caplog.text == ""

    # shape._validateUuid4 = lambda: None

@pytest.mark.parametrize("fn",
    ["simple_Fylker_0.json", "simple_Kommuner_0.json", "simple_Kommuner_291.json"]) # noqa
@pytest.mark.data
def testDataShape_FromGeoJson(fn, tmpConf, tmpDir, caplog, monkeypatch):
    """ Checks that geojson file is stored and Shape instance is created"""
    dataPath = Path(tmpDir) / "data"
    dataPath.mkdir(exist_ok=True)
    tmpConf.dataPath = dataPath

    fn = Path("tests/test_data/data") / fn
    with fn.open() as f:
        data = json.load(f)
        data = data["polygon"]

    # correct instance created
    shape = Shape.fromGeoJSON(data)
    assert isinstance(shape, Shape)
    assert shape._path.exists()

    # returns None if not valid input
    monkeypatch.setattr(Shape, "polygonFromGeoJson", lambda x: None)
    shape = Shape.fromGeoJSON("")
    assert shape is None


@pytest.mark.data
def testDataShape_Polygon(tmpConf, tmpDir, caplog):
    """ Checks that geojson file is stored and Shape instance is created"""
    dataPath = Path(tmpDir) / "data"
    dataPath.mkdir(exist_ok=True)
    tmpConf.dataPath = dataPath

    fn = "simple_Fylker_0.json"
    fn = Path("tests/test_data/data") / fn
    with fn.open() as f:
        data = json.load(f)
        data = data["polygon"]

    uuid = '33d0c48f-b58c-4b1a-b224-e93b03393cb3'
    shape = Shape(uuid)

    # create file ans see if it is returned:
    path = dataPath / f'{uuid}.geojson'
    with path.open('w') as f:
        json.dump(data, f)
    result = shape.polygon()
    assert isinstance(result, (Polygon, MultiPolygon))

    # error if it does exist (default)
    caplog.clear()
    tolerance = 50.5
    tolerance_str = str(50_500_000)
    fnjson = (dataPath / f'{uuid}.{tolerance_str}.geojson')
    # TODO: replace by saveunlink (missing_ok not available in py3.7)
    if fnjson.exists():
        fnjson.unlink()
    result = shape.polygon(tolerance=tolerance)
    assert "Polygon does not exist for tolerance" in caplog.text

    # but create it, if cachedOnly=False
    caplog.clear()
    if fnjson.exists():
        fnjson.unlink()
    result = shape.polygon(tolerance=50.5, cachedOnly=False)
    assert "Creating polygon" in caplog.text
    assert fnjson.exists()

    # now it exists -- check that it is loaded
    shape.polygonFromGeoJson = lambda path: path
    result = shape.polygon(tolerance=50.5, cachedOnly=False)
    assert result == fnjson


@pytest.mark.parametrize("fn",
    ["simple_Fylker_0.json", "simple_Kommuner_0.json", "simple_Kommuner_291.json"]) # noqa
@pytest.mark.data
def testDataShape_ToGeoJson(fn, tmpConf, tmpDir):
    """ Checks that geojson file is stored and Shape instance is created"""
    dataPath = Path(tmpDir) / "data"
    dataPath.mkdir(exist_ok=True)
    tmpConf.dataPath = dataPath

    fn = Path("tests/test_data/data") / fn
    with fn.open() as f:
        data = json.load(f)
        data = data["polygon"]

    shape = Shape.fromGeoJSON(data)
    result = shape.toGeoJson()
    expected = {"type": "Feature", "geometry": data}
    # TODO:
    # hacky comparison, but convert tuples to lists
    result = eval(result.__repr__().replace("(", "[").replace(")", "]"))
    assert result == expected


@pytest.mark.parametrize("file, typ", [("simple_Fylker_0.json", Polygon),
                                       ("simple_Kommuner_0.json", Polygon),
                                       ("simple_Kommuner_291.json", MultiPolygon)])
@pytest.mark.data
def testDataShape_PolygonFromGeoJson(file, typ, tmpConf, tmpDir, caplog):
    """ Checks that geojson file is stored and Shape instance is created"""
    dataPath = Path(tmpDir) / "data"
    dataPath.mkdir(exist_ok=True)
    tmpConf.dataPath = dataPath

    fn = Path("tests/test_data/data") / file
    with fn.open() as f:
        data = json.load(f)
        data = data["polygon"]
        fn_geodata = dataPath / file
        with fn_geodata.open('w') as f:
            json.dump(data, f)

    # correct instance created
    shape = Shape.polygonFromGeoJson(data)
    assert isinstance(shape, typ)
    assert Shape.polygonFromGeoJson(data) == Shape.polygonFromGeoJson(fn_geodata)

    # works also on True geoJson
    data_true_geoJson = {"type": "Feature",
                         "geometry": data,
                         "properties": {"name": "Dinagat Islands"}}
    shape = Shape.polygonFromGeoJson(data_true_geoJson)
    assert isinstance(shape, typ)

    # input typechecks
    data_true_geoJson = {"type": "Feature",
                         "geometry": data,
                         "properties": {"name": "Dinagat Islands"}}
    caplog.clear()
    shape = Shape.polygonFromGeoJson([(0, 1), (1, 0), (0, 1)])
    assert shape is None
    assert "Input has to be dict" in caplog.text

    # error if not (Multipolygon)
    caplog.clear()
    shape = Shape.polygonFromGeoJson({"type": "Point", "coordinates": [125.6, 10.1]})
    assert shape is None
    assert "Not a valid GeoJson" in caplog.text

    # Err if path does not exist
    caplog.clear()
    shape = Shape.polygonFromGeoJson("nopath/to/file")
    assert "does not exist" in caplog.text


@pytest.mark.parametrize("fn",
    ["simple_Fylker_0.json", "simple_Kommuner_0.json", "simple_Kommuner_291.json"]) # noqa
@pytest.mark.data
def testDataShape_GeoJsonFromPolygon(fn, tmpConf, tmpDir, caplog):
    """ Checks that geojson file is stored and Shape instance is created"""
    dataPath = Path(tmpDir) / "data"
    dataPath.mkdir(exist_ok=True)
    tmpConf.dataPath = dataPath

    fn = Path("tests/test_data/data") / fn
    with fn.open() as f:
        data = json.load(f)
        data = data["polygon"]

    # plain comparison
    data = geometry.shape(data)
    expected = {"type": "Feature", "geometry": geometry.mapping(data)}
    result = Shape.geoJsonFromPolygon(data)
    assert result == expected

    # added arguments
    pars = {"parameters": {"name": "foo"}, "crs" : 123}
    expected = {"type": "Feature", "geometry": geometry.mapping(data),
                "parameters": {"name": "foo"}, "crs" : 123}
    result = Shape.geoJsonFromPolygon(data, pars)
    assert result == expected

    # warn if special key
    pars = {"geometry": 123, "crs" : 123}
    expected = {"type": "Feature", "geometry": geometry.mapping(data)}
    caplog.clear()
    result = Shape.geoJsonFromPolygon(data, pars)
    assert result == expected
    assert "Cannot append" in caplog.text


@pytest.mark.data
@pytest.mark.parametrize("uuid,expected,logtext",
    [(None, False, "is not a string"), # noqa # not a string
     ('33d0c48f-b58c-4b1a-b224-e93b03393cb3', True, ""), # gen by uuid4
     ('33d0c48fb58c4b1ab224e93b03393cb3', False, ""), # missing '-' character
     ('0', False, "ValueError")]) # check catching error
def testDataShape_ValidateUudi4(uuid, expected, logtext, caplog, tmpConf, tmpDir):
    """Test that the UUIDs are validated or errors are logged.
    """
    dataPath = Path(tmpDir) / "data"
    dataPath.mkdir(exist_ok=True)
    tmpConf.dataPath = dataPath

    shape = Shape(uuid)
    caplog.clear()

    result = shape._validateUuid()
    assert result == expected
    if not result:
        assert logtext in caplog.text
# END Test testDataShape_Init
