"""
MetAlert Search : CapXML Class
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

from lxml import etree

from ma_search.common import checkFloat


class CapXML():

    def __init__(self, capfile):

        self._captree = etree.parse(capfile)

        self._info = {}
        self._info["areaDesc"] = {}
        capRoot = self._captree.getroot()

        for capElem in capRoot:
            if self._localname(capElem) == "identifier":
                self._info["identifier"] = capElem.text
            elif self._localname(capElem) == "sent":
                self._info["sent"] = capElem.text
            elif self._localname(capElem) == "info":
                self._parseInfo(capElem)

        return

    def __getitem__(self, str):
        """Return any item of the main data dictionary."""
        return self._info.get(str, None)

    def asGeoJson(self):
        """Return the main polygon as a geoJson dictionary."""
        polygon = self._info.get("polygon", None)
        if polygon is None:
            return None

        if len(polygon) == 1:
            type = "Polygon"
        else:
            type = "MultiPolygon"

        geoJson = {
            "type": "Feature",
            "geometry": {
                "type": type,
                "coordinates": []
            }
        }

        for subPoly in polygon:
            newSubPoly = []
            for latitude, longitude in subPoly:
                newSubPoly.append((longitude, latitude))
            if newSubPoly:
                geoJson["geometry"]["coordinates"].append(newSubPoly)

        return geoJson

    ##
    #  Internal Functions
    ##

    def _parseInfo(self, info):
        """Parses info-subelement in the capxml file, most values
        defaulting to None if not in file
        """
        infoLang = "en"
        infoAreaDesc = ""
        polygonList = []
        circleList = []
        geocodes = []
        altitude = None
        ceiling = None

        for infoElem in info:
            if self._localname(infoElem) == "language":
                infoLang = infoElem.text
            elif self._localname(infoElem) == "area":
                for areaElem in infoElem:
                    if self._localname(areaElem) == "polygon":
                        tempList = []
                        for coords in areaElem.text.split(" "):
                            latitude, longitude = coords.split(",")
                            tempList.append((
                                checkFloat(latitude, 0.0), checkFloat(longitude, 0.0)
                            ))
                        polygonList.append(tempList)

                    elif self._localname(areaElem) == "circle":
                        coords, radius = areaElem.text.split(" ")
                        latitude, longitude = coords.split(",")
                        circleList.append((
                            checkFloat(latitude, 0.0), checkFloat(longitude, 0.0),
                            checkFloat(radius, 0.0)
                        ))

                    elif self._localname(areaElem) == "geocode":
                        valueName = ""
                        value = ""
                        for elem in areaElem:
                            if self._localname(elem) == "valueName":
                                valueName = elem.text
                            elif self._localname(elem) == "value":
                                value = elem.text
                        if valueName and value:
                            geocodes.append((valueName, value))

                    elif self._localname(areaElem) == "areaDesc":
                        infoAreaDesc = areaElem.text

                    elif self._localname(areaElem) == "altitude":
                        altitude = checkFloat(areaElem.text, None)

                    elif self._localname(areaElem) == "ceiling":
                        ceiling = checkFloat(areaElem.text, None)

        self._info["polygon"] = polygonList if polygonList else None
        self._info["circle"] = circleList if circleList else None
        self._info["geocode"] = geocodes if geocodes else None
        self._info["areaDesc"][infoLang] = infoAreaDesc
        self._info["altitude"] = altitude
        self._info["ceiling"] = ceiling

    def _localname(self, etreeElem):
        """Helper function to do searches in the xml file, ignoring
        versioned namespace
        """
        return etree.QName(etreeElem.tag).localname
