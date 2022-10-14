"""Global values used throughout quaker."""
BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

ISO8601_DT_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

RESPONSE_BAD_REQUEST = 400
RESPONSE_NO_CONTENT = 204
RESPONSE_NOT_FOUND = 404
RESPONSE_OK = 200

MAX_ATTEMPTS = 3
MAX_DEPTH = 10
UPPER_LIMIT = 20000
DEFAULT_QUERY_PARAMS = {"format": "csv", "orderby": "time"}
