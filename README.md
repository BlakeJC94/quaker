# Quaker
Lightweight python API to USGS earthquake dataset.
[API Docs are located here](https://earthquake.usgs.gov/fdsnws/event/1/)

## Installation
Clone the repo to your system and install

```bash
$ git clone https://github.com/BlakeJC94/quaker.git
$ cd quaker
$ pip install .
```

## Quickstart
This package comes equipped with a batteries-included CLI interface for downloading the latest
earthquake event data in CSV, GeoJSON, and plain text format from the USGS database.
```
usage: quaker [-h] [--format VAL] [--endtime TIME] [--starttime TIME] [--updatedafter TIME] [--minlatitude LAT]
              [--minlongitude LNG] [--maxlatitude LAT] [--maxlongitude LNG] [--latitude LAT] [--longitude LNG]
              [--maxradius VAL] [--maxradiuskm DIST] [--catalog VAL] [--contributor VAL] [--eventid VAL]
              [--includeallmagnitudes BOOL] [--includeallorigins BOOL] [--includedeleted VAL]
              [--includesuperceded BOOL] [--limit VAL] [--maxdepth VAL] [--maxmagnitude VAL] [--mindepth VAL]
              [--minmagnitude VAL] [--offset VAL] [--orderby VAL] [--alertlevel VAL] [--callback VAL]
              [--eventtype VAL] [--jsonerror BOOL] [--kmlanimated BOOL] [--kmlcolorby VAL] [--maxcdi VAL]
              [--maxgap VAL] [--maxmmi VAL] [--maxsig VAL] [--mincdi VAL] [--minfelt VAL] [--mingap VAL]
              [--minsig VAL] [--producttype VAL] [--productcode VAL] [--reviewstatus VAL]
              [mode]

Access USGS Earthquake dataset API Docs: https://earthquake.usgs.gov/fdsnws/event/1/ NOTE: All times use
ISO8601 Date/Time format (yyyy-mm-ddThh:mm:ss). UTC is assumed. NOTE: Minimum/maximum longitude values may
cross the date line at 180 or -180

positional arguments:
  mode                  action to perform (default: download)

optional arguments:
  -h, --help            show this help message and exit

Format:
  --format VAL          specify the output format (one of "csv", "geojson", "kml", "quakeml", "text", or
                        "xml").

Time:
  --endtime TIME        limit to events on or before the specified end time.
  --starttime TIME      limit to events on or after the specified start time.
  --updatedafter TIME   limit to events updated after the specified time.

Location - rectangle:
  --minlatitude LAT     limit to events with a latitude larger than the specified minimum [-90, 90].
  --minlongitude LNG    limit to events with a longitude larger than the specified minimum [-360, 360].
  --maxlatitude LAT     limit to events with a latitude smaller than the specified maximum [-90, 90].
  --maxlongitude LNG    limit to events with a longitude smaller than the specified maximum [-360, 360].

Location - circle:
  --latitude LAT        specify the latitude to be used for a radius search [-90, 90].
  --longitude LNG       specify the longitude to be used for a radius search [-180, 180].
  --maxradius VAL       limit to events within the specified maximum number of degrees from the geographic
                        point defined by the latitude and longitude parameters [0, 180].
  --maxradiuskm DIST    limit to events within the specified maximum number of kilometers from the geographic
                        point defined by the latitude and longitude parameters [0, 20001.6].

Other:
  --catalog VAL         limit to events from a specified catalog.
  --contributor VAL     limit to events contributed by a specified contributor.
  --eventid VAL         select a specific event by id; event identifiers are data center specific.
  --includeallmagnitudes BOOL
                        specify if all magnitudes for the event should be included.
  --includeallorigins BOOL
                        specify if all origins for the event should be included.
  --includedeleted VAL  specify if deleted products and events should be included. the value "only" returns
                        only deleted events. values "true" or "false" are typecast to bool.
  --includesuperceded BOOL
                        specify if superseded products should be included. this also includes all deleted
                        products, and is mutually exclusive to the includedeleted parameter.
  --limit VAL           limit the results to the specified number of events.
  --maxdepth VAL        limit to events with depth less than the specified maximum.
  --maxmagnitude VAL    limit to events with a magnitude smaller than the specified maximum.
  --mindepth VAL        limit to events with depth more than the specified minimum.
  --minmagnitude VAL    limit to events with a magnitude larger than the specified minimum.
  --offset VAL          return results starting at the event count specified, starting at 1.
  --orderby VAL         order the results (one of "time", "time-asc", "magnitude", or "magnitude-asc").

Extensions:
  --alertlevel VAL      limit to events with a specific pager alert level (one of "green", "yellow", "orange",
                        or "red").
  --callback VAL        convert geojson output to a jsonp response using this callback.
  --eventtype VAL       limit to events of a specific type
  --jsonerror BOOL      request json(p) formatted output even on api error results. (only for geojson format)
  --kmlanimated BOOL    whether to include timestamp in generated kml, for google earth animation support.
  --kmlcolorby VAL      how earthquakes are colored (one of "age", "depth").
  --maxcdi VAL          maximum value for maximum community determined intensity reported by dyfi [0, 12].
  --maxgap VAL          limit to events with no more than this azimuthal gap [0, 360].
  --maxmmi VAL          maximum value for maximum modified mercalli intensity reported by shakemap [0, 12].
  --maxsig VAL          limit to events with no more than this significance.
  --mincdi VAL          minimum value for maximum community determined intensity reported by dyfi [0, 12].
  --minfelt VAL         limit to events with this many dyfi responses.
  --mingap VAL          limit to events with no less than this azimuthal gap [0, 360].
  --minsig VAL          limit to events with no less than this significance.
  --producttype VAL     limit to events that have this type of product associated.
  --productcode VAL     return the event that is associated with the productcode.
  --reviewstatus VAL    limit to events with a specific review status (one of "all", "automatic", or
                        "reviewed").
```

Run `quaker download` and specify the parameters as keyword arguments and pipe the output to any
location:
```bash
$ quaker download --format csv --starttime 2022-08-01 --endtime 2022-09-01 > earthquake_data.csv
```

For more details on the available query parameters, use `quaker --help` or view the
[USGS documentation](https://earthquake.usgs.gov/fdsnws/event/1/).

Using the python API is also fairly straight-forward:
```python
>>> from quaker import Query, Client
>>> client = Client()
# An empty query defaults to all events in the last 30 days
>>> events_from_last_30_days = Query()
>>> client.execute(events_from_last_30_days, output_file="./path/to/example/output_1.csv")
# Large multi-page queries can also be handled
>>> events_from_last_5_months = Query(
...     format="csv",
...     starttime="2022-05-01",
...     endtime="2022-10-01",
... )
>>> client.execute(events_from_last_5_months, output_file="./path/to/example/output_2.csv")
# Calling `client.execute` without an output file return results as a pandas DataFrame
>>> results = client.execute(events_from_last_5_months)
# You can filter results by location using the API
>>> fields = {
...     "format": "csv",
...     "starttime": "2022-08-01",
...     "endtime": "2022-09-01",
...     "latitude": 35.652832,
...     "longitude": 139.839478,
...     "maxradiuskm": 120.0,
...     "minmagnitude": 3.0,
... }
>>> events_in_august_in_120km_within_tokyo_above_mag_3 = Query(**fields)
>>> client.execute(
...     events_in_august_in_120km_within_tokyo_above_mag_3,
...     output_file="./path/to/example/output_3.csv"
... )
# See `help(Query)` and https://earthquake.usgs.gov/fdsnws/event/1/ for more details
```

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

Virtual environment handling by `poetry` is preferred:
```bash
# in the project directory
$ poetry install
$ poetry shell
```
