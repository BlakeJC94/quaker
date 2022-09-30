"""""" # TODO
import os
import re
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Optional, List

from requests import Session, Request

from quaker.globals import ISO8601_REGEX
from quaker.src import run_query, Query

# TODO docstring
def download(query_params: Query, output_file: str) -> List[Request]:
    # TODO check if output_file is given and create parent dirs if needed
    with Session() as session:
        # TODO write a try catch here, make sure the file writing is safely handled as well
        return run_query(query_params, session, output_file)
