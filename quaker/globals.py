"""Global values used throughout quaker."""
BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

ISO8601_REGEX = r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\+\d{2}:d{2})?)?(\.\d{6})?$"
ISO8601_DT_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

RESPONSE_BAD_REQUEST = 400
RESPONSE_OK = 200

MAX_DEPTH = 3
UPPER_LIMIT = 20000
DEFAULT_QUERY_PARAMS = {"format": "csv", "orderby": "time"}
