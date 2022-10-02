import argparse
import logging

from . import (
    __version__,
    download,
    Query,
)

logger = logging.getLogger(__name__)

def main():

    docs = Query.__doc__
    head, arg_doc = docs.split("Args:")
    extra_info = "\n".join(head.splitlines()[1:])

    arg_doc_dict = {}
    for entry in arg_doc.split('.\n'):  # relies on full stops after args!
        name, desc = entry.split(":", 1)
        name = name.strip()
        desc = desc.replace("\n" + " " * 8, " ").strip()
        arg_doc_dict[name] = desc

    main_doc = "Access USGS Earthquake dataset" + extra_info
    parser = argparse.ArgumentParser(
        description=main_doc,
        add_help=True,
    )

    # Allow one optional positional arg to select mode
    parser.add_argument('mode', nargs='?', default="download")

    # TODO get callable type from __annotations__
    # this may require an eval, use a hidden helper for safety
    for k in Query.__annotations__:
        parser.add_argument(
            "--" + k,
            help=arg_doc_dict[k],
            # type=...
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
