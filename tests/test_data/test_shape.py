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
import pytest
from pathlib import Path

import shapely.geometry as geometry
from shapely.geometry import MultiPolygon, Polygon

import ma_search
from ma_search.data.shape import Shape


@pytest.mark.data
def testDataShape_Init(tmpConf, tmpDir, caplog):
    """Tests class initialisation."""
    dataPath = Path(tmpDir) / "data"
    dataPath.mkdir(exist_ok=True)
    tmpConf.dataPath = dataPath

    # Check error if invalid UUID
    caplog.clear()
    Shape(None)
    assert "UUID 'None' is not valid" in caplog.text

    # Check error if file does not exist
    caplog.clear()
    uuid = "33d0c48f-b58c-4b1a-b224-e93b03393cb3"
    Shape(uuid)
    assert "does not exist" in caplog.text

    # Check that it is or of the file exists
    Path(dataPath/uuid).with_suffix(".geojson").touch()
    caplog.clear()
    Shape(uuid)
    assert caplog.text == ""

# END Test testDataShape_Init


@pytest.mark.parametrize(
    "fn", ["simple_Fylker_0.json", "simple_Kommuner_0.json", "simple_Kommuner_291.json"]
)
@pytest.mark.data
def testDataShape_FromGeoJson(fn, tmpConf, tmpDir, filesDir, caplog, monkeypatch):
    """Checks storing of geojson file and Shape instance creation."""
    dataPath = Path(tmpDir) / "data"
    dataPath.mkdir(exist_ok=True)
    tmpConf.dataPath = dataPath

    fn = Path(filesDir) / fn
    with fn.open() as f:
        data = json.load(f)
        data = data["polygon"]

    # Correct instance created
    shape = Shape.fromGeoJSON(data)
    assert isinstance(shape, Shape)
    assert shape._path.exists()

    # Returns None if not valid input
    with monkeypatch.context() as m:
        m.setattr(Shape, "polygonFromGeoJson", lambda x: None)
        shape = Shape.fromGeoJSON("")
        assert shape is None

    # Returns None if file cannot be written
    with monkeypatch.context() as m:
        m.setattr(ma_search.data.shape, "safeWriteJson", lambda *args: False, raising=True)
        caplog.clear()
        assert Shape.fromGeoJSON(data) is None
        assert "Cannot write GeoJson file" in caplog.text

# END Test testDataShape_FromGeoJson


@pytest.mark.data
def testDataShape_Polygon(tmpConf, tmpDir, caplog, filesDir, monkeypatch):
    """Checks that Polygon is found or created."""
    dataPath = Path(tmpDir) / "data"
    dataPath.mkdir(exist_ok=True)
    tmpConf.dataPath = dataPath

    fn = "simple_Fylker_0.json"
    fn = Path(filesDir) / fn
    with fn.open() as f:
        data = json.load(f)
        data = data["polygon"]

    uuid = "33d0c48f-b58c-4b1a-b224-e93b03393cb3"
    shape = Shape(uuid)

    # Check typecheck of tolerance
    caplog.clear()
    assert shape.polygon(tolerance="0.c8") is None
    assert "Tolerance has to be float" in caplog.text

    # Create file ans see if it is returned:
    path = dataPath / f'{uuid}.geojson'
    with path.open('w') as f:
        json.dump(data, f)
    result = shape.polygon()
    assert isinstance(result, (Polygon, MultiPolygon))

    # Error if it does not exist (default)
    caplog.clear()
    tolerance = 50.5
    tolerance_str = str(50_500_000)
    fnjson = (dataPath / f"{uuid}.{tolerance_str}.geojson")
    # `Missing_ok` not available >py3.8 so we do this with an if test
    if fnjson.exists():
        fnjson.unlink()
    result = shape.polygon(tolerance=tolerance)
    assert "Polygon does not exist for tolerance" in caplog.text

    # Create it, if cachedOnly=False
    caplog.clear()
    if fnjson.exists():
        fnjson.unlink()
    result = shape.polygon(tolerance=tolerance, cachedOnly=False)
    assert "Creating polygon" in caplog.text
    assert fnjson.exists()

    # Now it exists, so check that it is loaded
    with monkeypatch.context() as m:
        m.setattr(shape, "polygonFromGeoJson", lambda path: path, raising=True)
        shape.polygon(tolerance=50.5, cachedOnly=False)  # Makes sure file exists
        result = shape.polygon(tolerance=50.5)
        assert result == fnjson

    # Check that errors are catched if issues reading "full" file
    if fnjson.exists():
        fnjson.unlink()
    with monkeypatch.context() as m:
        m.setattr(shape, "polygonFromGeoJson", lambda path: None, raising=True)
        caplog.clear()
        result = shape.polygon(tolerance=50.5, cachedOnly=False)
        assert result is None
        assert "Full polygon cannot be loaded" in caplog.text

    # Check that errors are catched if issues writing simplified polygon
    if fnjson.exists():
        fnjson.unlink()
    with monkeypatch.context() as m:
        m.setattr(ma_search.data.shape, "safeWriteJson", lambda *args: False, raising=True)
        caplog.clear()
        result = shape.polygon(tolerance=50.5, cachedOnly=False)
        assert result is None
        assert "Cannot write simplified polygon to file" in caplog.text

# END Test testDataShape_Polygon


@pytest.mark.parametrize(
    "fn", ["simple_Fylker_0.json", "simple_Kommuner_0.json", "simple_Kommuner_291.json"]
)
@pytest.mark.data
def testDataShape_ToGeoJson(fn, tmpConf, tmpDir, filesDir):
    """Checks storing of geojson file and Shape instance creation."""
    dataPath = Path(tmpDir) / "data"
    dataPath.mkdir(exist_ok=True)
    tmpConf.dataPath = dataPath

    fn = Path(filesDir) / fn
    with fn.open() as f:
        data = json.load(f)
        data = data["polygon"]

    shape = Shape.fromGeoJSON(data)
    result = shape.toGeoJson()
    expected = {"type": "Feature", "geometry": data}
    # TODO: Hacky comparison, but convert tuples to lists
    result = eval(result.__repr__().replace("(", "[").replace(")", "]"))
    assert result == expected

# END Test testDataShape_ToGeoJson


@pytest.mark.parametrize(
    "fname, typ", [
        ("simple_Fylker_0.json", Polygon),
        ("simple_Kommuner_0.json", Polygon),
        ("simple_Kommuner_291.json", MultiPolygon)
    ]
)
@pytest.mark.data
def testDataShape_PolygonFromGeoJson(fname, typ, tmpConf, tmpDir, filesDir, caplog):
    """Checks storing of geojson file and Polygon creation."""
    dataPath = Path(tmpDir) / "data"
    dataPath.mkdir(exist_ok=True)
    tmpConf.dataPath = dataPath

    fn = Path(filesDir) / fname
    with fn.open() as f:
        data = json.load(f)
        data = data["polygon"]
        fn_geodata = dataPath / fname
        with fn_geodata.open('w') as f:
            json.dump(data, f)

    # Correct instance created
    shape = Shape.polygonFromGeoJson(data)
    assert isinstance(shape, typ)
    assert Shape.polygonFromGeoJson(data) == Shape.polygonFromGeoJson(fn_geodata)

    # Works also on True geoJson
    data_true_geoJson = {
        "type": "Feature",
        "geometry": data,
        "properties": {"name": "Dinagat Islands"}
    }
    shape = Shape.polygonFromGeoJson(data_true_geoJson)
    assert isinstance(shape, typ)

    # Input typechecks
    data_true_geoJson = {
        "type": "Feature",
        "geometry": data,
        "properties": {"name": "Dinagat Islands"}
    }
    caplog.clear()
    shape = Shape.polygonFromGeoJson([(0, 1), (1, 0), (0, 1)])
    assert shape is None
    assert "Input has to be dict" in caplog.text

    # Error if not (Multipolygon)
    caplog.clear()
    shape = Shape.polygonFromGeoJson({"type": "Point", "coordinates": [125.6, 10.1]})
    assert shape is None
    assert "Not a valid GeoJson" in caplog.text

    # Error if path does not exist
    caplog.clear()
    assert Shape.polygonFromGeoJson("nopath/to/file") is None
    assert "Could not read from file" in caplog.text

# END Test testDataShape_PolygonFromGeoJson


@pytest.mark.parametrize(
    "fn", ["simple_Fylker_0.json", "simple_Kommuner_0.json", "simple_Kommuner_291.json"]
)
@pytest.mark.data
def testDataShape_GeoJsonFromPolygon(fn, tmpConf, tmpDir, filesDir, caplog):
    """Checks storing of geojson file and Shape instance creation."""
    dataPath = Path(tmpDir) / "data"
    dataPath.mkdir(exist_ok=True)
    tmpConf.dataPath = dataPath

    fn = Path(filesDir) / fn
    with fn.open() as f:
        data = json.load(f)
        data = data["polygon"]

    # Plain comparison
    data = geometry.shape(data)
    expected = {"type": "Feature", "geometry": geometry.mapping(data)}
    result = Shape.geoJsonFromPolygon(data)
    assert result == expected

    # Added arguments
    pars = {"parameters": {"name": "foo"}, "crs": 123}
    expected = {
        "type": "Feature",
        "geometry": geometry.mapping(data),
        "parameters": {"name": "foo"},
        "crs": 123
    }
    result = Shape.geoJsonFromPolygon(data, pars)
    assert result == expected

    # Warn if special key
    pars = {"geometry": 123, "crs": 123}
    expected = {"type": "Feature", "geometry": geometry.mapping(data)}
    caplog.clear()
    result = Shape.geoJsonFromPolygon(data, pars)
    assert result == expected
    assert "Cannot append" in caplog.text

# END Test testDataShape_GeoJsonFromPolygon
