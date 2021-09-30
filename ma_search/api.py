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

from flask import Flask

from ma_search.data import Data

api = Flask(__name__)
data = Data()


@api.route("/v1/search/<target>", methods=["POST"])
def apiV1Search(target):
    """The main search entry point.
    """
    if target == "coffee":
        return "I'm a teapot", 418
    elif target not in ("map", "cap"):
        return f"No such search target '{target}'", 404

    return "Yay!", 200
