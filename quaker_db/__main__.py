from argparse import ArgumentParser

from quaker_db.client import Client

DOCS = {
    "Formats": {
        "format": (
            str,
            "(default: quakeml) Specify the output format, one of csv, geojson, kml, quakeml, csv, text, xml",
        ),
    },
    "Time": {
        "endtime": (
            str,
            "(default: present time) Limit to events on or before the specified end time. NOTE: All times use ISO8601 Date/Time format. Unless a timezone is specified, UTC is assumed",
        ),
        "starttime": (
            str,
            "(default: NOW - 30 days) Limit to events on or after the specified start time. NOTE: All times use ISO8601 Date/Time format. Unless a timezone is specified, UTC is assumed",
        ),
        "updatedafter": (
            str,
            "(default: null) Limit to events updated after the specified time.  NOTE: All times use ISO8601 Date/Time format. Unless a timezone is specified, UTC is assumed",
        ),
    },
    "Location (rectangle)": {
        "minlatitude": (
            float,
            "(default: -90) [-90,90] degrees, Limit to events with a latitude larger than the specified minimum. NOTE: min values must be less than max values",
        ),
        "minlongitude": (
            float,
            "(default: -180) [-360,360] degrees, Limit to events with a longitude larger than the specified minimum. NOTE: rectangles may cross the date line by using a minlongitude < -180 or maxlongitude > 180. NOTE: min values must be less than max values",
        ),
        "maxlatitude": (
            float,
            "(default: 90) [-90,90] degrees, Limit to events with a latitude smaller than the specified maximum. NOTE: min values must be less than max values",
        ),
        "maxlongitude": (
            float,
            "(default: 180) [-360,360] degrees, Limit to events with a longitude smaller than the specified maximum. NOTE: rectangles may cross the date line by using a minlongitude < -180 or maxlongitude > 180. NOTE: min values must be less than max values",
        ),
    },
    "Location (circle)": {
        "latitude": (
            float,
            "(default: null) [-90,90] degrees, Specify the latitude to be used for a radius search",
        ),
        "longitude": (
            float,
            "(default: null) [-180,180] degrees, Specify the longitude to be used for a radius search",
        ),
        "maxradius": (
            float,
            "(default: 180) [0, 180] degrees, Limit to events within the specified maximum number of degrees from the geographic point defined by the latitude and longitude parameters. NOTE: This option is mutually exclusive with maxradiuskm and specifying both will result in an error",
        ),
        "maxradiuskm": (
            float,
            "(default: 20001.6) [0, 20001.6] km, Limit to events within the specified maximum number of kilometers from the geographic point defined by the latitude and longitude parameters. NOTE: This option is mutually exclusive with maxradius and specifying both will result in an error",
        ),
    },
    "Other": {
        "catalog": (
            str,
            "(default: null) Limit to events from a specified catalog. Use the Catalogs Method to find available catalogs. NOTE: when catalog and contributor are omitted, the most preferred information from any catalog or contributor for the event is returned",
        ),
        "contributor": (
            str,
            "(default: null) Limit to events contributed by a specified contributor. Use the Contributors Method to find available contributors. NOTE: when catalog and contributor are omitted, the most preferred information from any catalog or contributor for the event is returned",
        ),
        "eventid": (
            str,
            "(default: null) Select a specific event by ID; event identifiers are data center specific. NOTE: Selecting a specific event implies includeallorigins, includeallmagnitudes, and, additionally, associated moment tensor and focal-mechanisms are included",
        ),
        "includeallmagnitudes": (
            bool,
            "(default: false) Specify if all magnitudes for the event should be included, default is data center dependent but is suggested to be the preferred magnitude only. NOTE: because magnitudes and origins are strongly associated, this parameter is interchangeable with includeallmagnitude",
        ),
        "includeallorigins": (
            bool,
            "(default: false) Specify if all origins for the event should be included, default is data center dependent but is suggested to be the preferred origin only. NOTE: because magnitudes and origins are strongly associated, this parameter is interchangable with includeallmagnitude",
        ),
        "includedeleted": (
            bool,
            "(default: false) Specify if deleted products and events should be included. The value only returns only deleted events.  Deleted events otherwise return the HTTP status 409 Conflict.  NOTE: Only supported by the csv and geojson formats, which include status",
        ),
        "includesuperseded": (
            bool,
            "(default: false) Specify if superseded products should be included. This also includes all deleted products, and is mutually exclusive to the includedeleted parameter. NOTE: Only works when specifying eventid parameter",
        ),
        "maxmagnitude": (
            float,
            "(default: null) Limit to events with a magnitude smaller than the specified maximum",
        ),
        "mindepth": (
            float,
            "(default: -100) [-100, 1000] km Limit to events with depth more than the specified minimum",
        ),
        "minmagnitude": (
            float,
            "(default: null) Limit to events with a magnitude larger than the specified minimum",
        ),
        "orderby": (
            str,
            "Order the results. The allowed values are: time, time-asc, magnitude, magnitude-asc",
        ),
    },
}


def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        "argfile", nargs="?", help="Optional comma separated file with API arguments"
    )

    for group_name, params in DOCS.items():
        group = parser.add_argument_group(group_name + " arguments")

        for field_name, (field_type, doc) in params.items():
            add_arg_kwargs = dict(
                help=doc,
                required=False,
                default=None,
            )
            if field_type is bool:
                add_arg_kwargs["action"] = "store_true"
            else:
                add_arg_kwargs["type"] = field_type

            group.add_argument(
                "--" + field_name,
                **add_arg_kwargs,
            )

    return parser.parse_args()


def main():
    args = vars(parse_args())

    if (args_file := args.pop("args_file", None)) is not None:
        args = {}
        docs_types = {k: t for n, v in DOCS.items() for k, (t, _) in v.items()}
        with open(args_file, "r") as f:
            for line in f.readlines():
                k, v = line.split(":", 1)
                k, v = k.strip(), v.strip()
                t = docs_types[k]
                v = t(v)
                args[k] = v

    client = Client()
    args.pop('argfile', None)
    result = client.execute(**args)

    print(result)


if __name__ == "__main__":
    main()
