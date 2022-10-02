# Quaker
Lightweight python API to USGS earthquake dataset

[API Docs are located here](https://earthquake.usgs.gov/fdsnws/event/1/)

## Installation
Clone the repo to your system and install

```bash
$ git clone https://github.com/BlakeJC94/quaker.git
$ cd quaker
$ pip install .
```

## Quickstart
This package comes equiped with a batteries-included CLI interface for downloading the latest
earthquake event data in CSV format from the USGS database. Run `quaker download` and specify the
parameters as keyword arguments and pipe the output to any location:
```bash
$ quaker download --starttime 2022-09-01 > earthquake_data.csv
```

For more details on the available query parameters, use `quaker --help` or view the
[USGS documentation](https://earthquake.usgs.gov/fdsnws/event/1/).

Using the python API is also fairly straight-forward:
```python
>>> from quaker import Query, download
# An empty query defaults to all events in the last 30 days
>>> events_from_last_30_days = Query()
>>> download(events_from_last_30_days, "./path/to/example/output_1.csv")
# Large queries can also be handled
>>> events_from_last_5_months = Query(
...     starttime="2022-05-01",
...     endtime="2022-10-01",
... )
>>> download(events_from_last_5_months, "./path/to/example/output_2.csv")
# You can filter results by location using the API
>>> fields = {
...     "starttime": "2022-08-01",
...     "endtime": "2022-09-01",
...     "latitude": 35.652832,
...     "longitude": 139.839478,
...     "maxradiuskm": 120.0,
...     "minmagnitude": 3.0,
... }
>>> events_in_august_in_120km_within_tokyo_above_mag_3 = Query(**fields)
>>> download(events_in_august_in_120km_within_tokyo_above_mag_3, "./path/to/example/output_3.csv")
# See `help(Query)` and https://earthquake.usgs.gov/fdsnws/event/1/ for more details
```

## Future developments

- [ ] Match split query by last `id` instead of last `time`
- [ ] Fix issue where `__post_init__` method doesn't fire
    - [ ] put datetime handling back into `Query`
    - [ ] Handle timezones as well
- [ ] Dash app to visualise clustered query results
- [ ] Expose parameters for formats other than CSV
- [ ] Testing suite
- [ ] Publish to pypi?

## Contributing
This is a small personal project, but pull requests are most welcome!

* Code is styled using `[black](https://github.com/psf/black)` (`pip install black`)
* Code is linted with `pylint` (`pip install pylint`)
* Requirements are managed using `pip-tools` (run `pip install pip-tools` if needed)
    * Add dependencies by adding packages to `setup.py` and running `pip-compile`
* [Semantic versioning](https://semver.org) is used in this repo
    * Major version: rare, substantial changes that break backward compatibility
    * Minor version: most changes - new features, models or improvements
    * Patch version: small bug fixes and documentation-only changes

Virtual environment handling by `pyenv` is preferred:
```bash
# in the project directory
$ pyenv virtualenv 3.9.7 quaker
$ pyenv local quaker
$ pip install -e .
```
