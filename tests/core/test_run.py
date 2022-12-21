
import pytest
from requests import Session

from quaker.core import run_query, Query

# TODO Ensure single page query works
# TODO Ensure multi page query works
# TODO Rename run_query to execute
class TestRunQuery:
    # TODO mock file write
    # TODO mock session.get to return a Request with STATUS_OKAY code
    # TODO mocked request should have content resembling lines of bites that are comma sepreated
    # TODO assert session.get called once
    def test_single_page_query(self):
        output_file = ... # tmpfile
        query = Query(format='csv')
        with Session() as session:
            run_query(query, session, output_file)


    ...
