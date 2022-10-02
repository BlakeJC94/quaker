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
earthquake event data in CSV format from the USGS database.
```
usage: quaker [-h] [--endtime TIME] [--starttime TIME] [--minlatitude LAT]
              [--minlongitude LNG] [--maxlatitude LAT] [--maxlongitude LNG]
              [--latitude LAT] [--longitude LNG] [--maxradiuskm DIST]
              [--minmagnitude VAL] [--maxmagnitude VAL] [--limit VAL]
              [mode]

Access USGS Earthquake dataset API Docs:
https://earthquake.usgs.gov/fdsnws/event/1/ NOTE: All times use ISO8601
Date/Time format (yyyy-mm-ddThh:mm:ss). UTC is assumed. NOTE: Minimum/maximum
longitude values may cross the date line at 180 or -180

positional arguments:
  mode                action to perform (default: download)

optional arguments:
  -h, --help          show this help message and exit
  --endtime TIME      limit to events on or before the specified end time
  --starttime TIME    limit to events on or after the specified start time
  --minlatitude LAT   limit to events with a latitude larger than the
                      specified minimum
  --minlongitude LNG  limit to events with a longitude larger than the
                      specified minimum
  --maxlatitude LAT   limit to events with a latitude smaller than the
                      specified maximum
  --maxlongitude LNG  limit to events with a longitude smaller than the
                      specified maximum
  --latitude LAT      specify the latitude to be used for a radius search
  --longitude LNG     specify the longitude to be used for a radius search
  --maxradiuskm DIST  limit to events within the specified maximum number of
                      kilometers from the geographic point defined by the
                      latitude and longitude parameters
  --minmagnitude VAL  limit to events with a magnitude larger than the
                      specified minimum
  --maxmagnitude VAL  limit to events with a magnitude smaller than the
                      specified maximum
  --limit VAL         limit the results to the specified number of events
```

Run `quaker download` and specify the parameters as keyword arguments and pipe the output to any
location:
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
