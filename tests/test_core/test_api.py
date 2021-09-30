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

import pytest

from ma_search.api import app


@pytest.fixture(scope="function")
def client():
    """Create an instance of the API."""
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
