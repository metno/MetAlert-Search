"""
MetAlert Search : Search API
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

from flask import Flask, request, jsonify

from ma_search.data import Data, Shape

app = Flask(__name__)
data = Data()

MSG_GEOJSON = (
    "Payload must contain an object named 'polygon' cotaining a "
    "valid geoJson Polygon or MultiPolygon\n"
)
MSG_VERTICAL = "The 'vertical' search parameter must be a list of 2 integers or floats\n"
MSG_CUTOFF = "The 'cutoff' search parameter must be a float in the interval (0.0, 1.0] \n"
MSG_MAXRES = "The 'maxres' search parameter must be an integer larger than 0\n"


@app.route("/v1/search/<target>", methods=["POST"])
def apiV1Search(target):
    """The main search entry point.
    """
    if target == "coffee":
        # Mock call for testing that the API is up and responds
        return "I'm a teapot\n", 418

    elif target not in ("map", "alert"):
        return f"No such search target '{target}'\n", 404

    # Decode payload
    payload = request.get_json(force=False, silent=True, cache=False)
    if not isinstance(payload, dict):
        return "Could not parse JSON payload\n", 400

    # Payload must contain a geojson
    geoJson = payload.get("polygon", None)
    shape = Shape.polygonFromGeoJson(geoJson)
    if shape is None:
        return MSG_GEOJSON, 400

    # Vertical range must be a list of two ints or floats
    vertical = payload.get("vertical", None)
    if vertical is not None:
        if not isinstance(vertical, list):
            return MSG_VERTICAL, 400
        if len(vertical) != 2:
            return MSG_VERTICAL, 400
        altitude = vertical[0]
        ceiling = vertical[1]
        if not (isinstance(altitude, (int, float)) and isinstance(ceiling, (int, float))):
            return MSG_VERTICAL, 400
        vertical = (altitude, ceiling)

    # Area cutoff parameter
    cutoff = payload.get("cutoff", 0.01)
    if not isinstance(cutoff, float):
        return MSG_CUTOFF, 400
    if not (cutoff > 0.0 and cutoff <= 1.0):
        return MSG_CUTOFF, 400

    # Max results parameter
    maxres = payload.get("maxres", 1000)
    if not isinstance(maxres, int):
        return MSG_MAXRES, 400
    if not maxres > 0:
        return MSG_MAXRES, 400

    # Run the search
    result = data.findOverlap(target, shape, vertical, cutoff, maxres)
    if result is None:
        return "Internal Server Error\n", 500

    return jsonify(result), 200
