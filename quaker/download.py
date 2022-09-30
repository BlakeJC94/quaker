"""Script to open a session and stream CSV data."""
from os import path, makedirs
from typing import List

from requests import Session, Request

from quaker.src import run_query, Query

# TODO docstring
def download(query_params: Query, output_file: str) -> List[Request]:
    parent_dir, _ = path.split(output_file)
    if not path.exists(parent_dir):
        print(f"INFO: parent dir {parent_dir} doesnt exist, creating")
        makedirs(parent_dir, exist_ok=True)

    with Session() as session:
        # TODO write a try catch here, make sure the file writing is safely handled as well
        return run_query(query_params, session, output_file)
