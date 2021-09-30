"""
MetAlert Search : API Tests
===========================

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

from ma_search.data import Data
from ma_search.api import app

MSG_GEOJSON = (
    b"Payload must contain an object named 'polygon' cotaining a "
    b"valid geoJson Polygon or MultiPolygon\n"
)
MSG_VERTICAL = b"The 'vertical' search parameter must be a list of 2 integers or floats\n"
MSG_CUTOFF = b"The 'cutoff' search parameter must be a float in the interval (0.0, 1.0] \n"
MSG_MAXRES = b"The 'maxres' search parameter must be an integer larger than 0\n"


@pytest.fixture(scope="function")
def client(tmpConf, fncDir, monkeypatch):
    """Create an instance of the API."""
    tmpConf.dataPath = fncDir
    tmpConf.dbProvider = "sqlite"
    tmpConf.sqlitePath = fncDir
    mockData = Data()
    monkeypatch.setattr("ma_search.api.data", mockData)

    with app.test_client() as client:
        yield client

    return


@pytest.mark.core
def testCoreApi_OtherEndPoints(client):
    """Test the various unused endpoints."""
    # Get is not allowed
    assert client.get("/v1/search/coffee").status_code == 405

    # Check posts
    assert client.post("/").status_code == 404
    assert client.post("/v1").status_code == 404
    assert client.post("/v1/search").status_code == 404
    assert client.post("/v1/search/coffee").status_code == 418
    assert client.post("/v1/search/whatever").status_code == 404

# END Test testCoreApi_OtherEndPoints


@pytest.mark.core
def testCoreApi_SearchAlert(client, monkeypatch):
    """Test search/alert endpoints."""
    # Missing payload
    response = client.post("/v1/search/alert")
    assert response.status_code == 400
    assert response.data == b"Could not parse JSON payload\n"

    # Missing GeoJson
    response = client.post("/v1/search/alert", json={})
    assert response.status_code == 400
    assert response.data == MSG_GEOJSON

    # Create a test polygon
    geoJson = {
        "type": "Polygon",
        "coordinates": [
            [[0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5], [0.5, 0.5]]
        ]
    }

    # Defaults
    response = client.post("/v1/search/alert", json={"polygon": geoJson})
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["maxres"] == 1000
    assert result["records"] == 0
    assert result["results"] == []

    # Vertical : Wrong Data Type
    response = client.post("/v1/search/alert", json={
        "polygon": geoJson,
        "vertical": "abcdef",
    })
    assert response.status_code == 400

    # Vertical : Wrong Length
    response = client.post("/v1/search/alert", json={
        "polygon": geoJson,
        "vertical": [1],
    })
    assert response.status_code == 400

    # Vertical : Wrong Values
    response = client.post("/v1/search/alert", json={
        "polygon": geoJson,
        "vertical": ["1", "2"],
    })
    assert response.status_code == 400

    # Vertical : Valid
    response = client.post("/v1/search/alert", json={
        "polygon": geoJson,
        "vertical": [0, 1],
    })
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["maxres"] == 1000
    assert result["records"] == 0
    assert result["results"] == []

    # Cutoff : Wrong Data Type
    response = client.post("/v1/search/alert", json={
        "polygon": geoJson,
        "vertical": [0, 1],
        "cutoff": "abc",
    })
    assert response.status_code == 400

    # Cutoff : Out of Range
    response = client.post("/v1/search/alert", json={
        "polygon": geoJson,
        "vertical": [0, 1],
        "cutoff": -1.0,
    })
    assert response.status_code == 400
    response = client.post("/v1/search/alert", json={
        "polygon": geoJson,
        "vertical": [0, 1],
        "cutoff": 2.0,
    })
    assert response.status_code == 400

    # Cutoff : Valid
    response = client.post("/v1/search/alert", json={
        "polygon": geoJson,
        "vertical": [0, 1],
        "cutoff": 0.5,
    })
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["maxres"] == 1000
    assert result["records"] == 0
    assert result["results"] == []

    # Maxres : Wrong Data Type
    response = client.post("/v1/search/alert", json={
        "polygon": geoJson,
        "vertical": [0, 1],
        "cutoff": 0.5,
        "maxres": "abc",
    })
    assert response.status_code == 400

    # Maxres : Out of Range
    response = client.post("/v1/search/alert", json={
        "polygon": geoJson,
        "vertical": [0, 1],
        "cutoff": 0.5,
        "maxres": -5,
    })
    assert response.status_code == 400

    # Maxres : Valid
    response = client.post("/v1/search/alert", json={
        "polygon": geoJson,
        "vertical": [0, 1],
        "cutoff": 0.5,
        "maxres": 100
    })
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["maxres"] == 100
    assert result["records"] == 0
    assert result["results"] == []

    # Internal Server Error
    with monkeypatch.context() as mp:
        mp.setattr("ma_search.api.data.findOverlap", lambda *a: None)
        response = client.post("/v1/search/alert", json={"polygon": geoJson})
        assert response.status_code == 500

# END Test testCoreApi_SearchAlert
