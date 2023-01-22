"""Function to open a session and stream data."""
from quaker.core import run_query, Query, Client


def download(
    query: Query,
    output_file: str,
    **kwargs,
) -> None:
    """Main function to download data to a file.

    Also supports querying data via kwargs. See `help(quaker.Query)` for a list of the parameters
    that can be configured.

    Args:
        output_file: Path to file to dump output to.
        query: Configured query dataclass. Defaults to query for all events in last 30 days.
    """
    if not isinstance(query, Query):
        raise ValueError()

    client = Client(output_file=output_file)
    client.execute(query)
