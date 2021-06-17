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

## Logging

The default logging level is `INFO`. This can be changed by setting the environment variable
`MA_SEARCH_LOGLEVEL`. The value must be set to one of `CRITICAL`, `ERROR`, `WARNING`, `INFO`, or
`DEBUG`.

To add logging to file, specify the file by setting the environment variable `MA_SEARCH_LOGFILE`.
