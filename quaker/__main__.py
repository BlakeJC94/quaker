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
    for entry in arg_doc.split(".\n"):  # relies on full stops after args!
        if ":" not in entry:
            continue
        name, desc = entry.split(":", 1)
        arg_doc_dict[name.strip()] = desc.replace("\n" + " " * 8, " ").strip().lower()

    main_doc = "Access USGS Earthquake dataset" + extra_info
    parser = argparse.ArgumentParser(
        description=main_doc,
        add_help=True,
    )

    # Allow one optional positional arg to select mode
    default_mode = "download"
    parser.add_argument(
        "mode",
        nargs="?",
        tyep=str,
        default=default_mode,
        help=f"action to perform (default: {default_mode})",
    )

    for k, v in Query.__annotations__.items():
        # Get the first type in square brackets, requires Optional[..]!
        type_str = str(v).replace(",", "[").split("[")[1][:-1].strip()
        type_clb = str
        if type_clb in ["str", "float", "int"]:
            type_clb = eval(type_str)  # pylint: disable=eval-used
        parser.add_argument(
            "--" + k,
            help=arg_doc_dict[k],
            metavar="VAL",
            type=type_clb,
            required=False,
            default=None,
        )

    args = parser.parse_args()

    # TODO move query handling here
    # query = Query(**dict(args))
    if args.mode == "download":
        download(output_file="/dev/stdout", query=None, **vars(args))
    else:
        logger.error("Only 'download' mode is supported for now")
        # logger.error("Invalid mode selected")
        return 1

    return 0


if __name__ == "__main__":
    main()
