# MetAlert Search Tools

[![flake8](https://github.com/metno/MetAlert-Search/actions/workflows/syntax.yml/badge.svg?branch=main)](https://github.com/metno/MetAlert-Search/actions/workflows/syntax.yml)
[![pytest](https://github.com/metno/MetAlert-Search/actions/workflows/pytest.yml/badge.svg?branch=main)](https://github.com/metno/MetAlert-Search/actions/workflows/pytest.yml)
[![codecov](https://codecov.io/gh/metno/MetAlert-Search/branch/main/graph/badge.svg?token=6XmejKi9gh)](https://codecov.io/gh/metno/MetAlert-Search)

This repo is a part of the [Annotated Atlas](https://github.com/metno/AnnotatedAtlas) project.

## Running Tests

```bash
pytest -v --cov=ma_search --cov-report=term
```

## Config File

A config file must be provided in yaml format. It should either be named `config.yaml` and saved
in the root folder of the source, or, alternatively, a full path to a valid yaml config file
specified with the environment variable `MA_SEARCH_CONFIG`.

## Search API

The main search API entry point is `/v1/search/<target>` where `<target>` is either `alert` for
searching the alert (CAP) file archive, or `map` for searching the map archive.

The search parameters must be submitted as JSON with the `POST` method.

The following keys can be set in the root JSON object:

* `"polygon"` (Required) A GeoJson entry with either a Polygon or a MultiPolygon object.
* `"vertical"` (Optional) An array of two floats or integers containing a minimum and maximum value
  to be matched against the altitude and ceiling parameters in the CAP files.
* `"cutoff"` (Optional) A float number greater than `0.0` and less or equal to `1.0`. Relative area
  overlaps smaller than this cutoff will not be returned in the result. Defaults to `0.01`.
* `"maxres"` (Optional) An integer lager than `0` with the maximum number of results to return from
  the search. Computing overlap between large polygons can be quite slow, so if you use very
  complex polygons, you may want to limit this number. Defaults to `1000`.

**Example:**

```python
{
    "polygon": {
        "type": "Polygon",
        "coordinates": [
            [[0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5], [0.5, 0.5]]
        ]
    },
    "vertical": [0, 1000],
    "cutoff": 0.25,
    "maxres": 100
}
```

## Maintenance Script

Only searches can be performed via the API. Ingestion of data must be done via a maintenance script
from command line. The root script is `maintenance.py` which has its own commands and switches.

Please run `./maintenance.py --help` for more information.

## Logging

The default logging level is `INFO`. This can be changed by setting the environment variable
`MA_SEARCH_LOGLEVEL`. The value must be set to one of `CRITICAL`, `ERROR`, `WARNING`, `INFO`, or
`DEBUG`.

To add logging to file, specify the file by setting the environment variable `MA_SEARCH_LOGFILE`.

## Scripts

An overview of handy scripts e.g. for importing boundaries of administrative regions to the
database can be found in the scripts folder. Note that they may not be maintained, and are not
subject to the CI routines.
