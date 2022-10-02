import argparse
import logging

from . import (
    __version__,
    download,
    Query,
)

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(
        description="Access USGS Earthquake dataset",
        add_help=True,
    )

    parser.add_argument('mode', nargs='?', default="download")

    for k in Query.__annotations__:
        parser.add_argument(
            "--" + k,
            help=k,  # TODO better docs?
            required=False,
            default=None,
        )

    args = parser.parse_args()

    breakpoint()
    # TODO move query handling here
    # query = Query(**dict(args))
    if args.mode == "download":
        download(output_file="/dev/stdout", query=None, **vars(args))
    else:
        logger.error("Invalid mode selected")
        return 1

    return 0


if __name__ == "__main__":
    main()
