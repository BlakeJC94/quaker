import argparse
import logging

from . import (
    __version__,
    download,
    Query,
)

logger = logging.getLogger(__name__)


def main():

    # TODO move this into a Query method
    docs = Query.__doc__
    head, arg_doc = docs.split("Args:")
    arg_doc = arg_doc.replace("\n" + 12 * " ", " ")
    extra_info = "\n".join(head.splitlines()[1:])

    arg_doc_dict = {}
    for entry in arg_doc.split("\n" + 4 * " "):
        if ":" not in entry:
            continue
        name, desc = entry.split(":", 1)
        arg_doc_dict[name.strip()] = desc.strip().lower()

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
        type=str,
        default=default_mode,
        help=f"action to perform (default: {default_mode})",
    )

    query_annotations = Query.__annotations__
    for k, v in query_annotations.items():

        # Get the first type in square brackets, requires Optional[..]!
        type_str = str(v).replace(",", "[").split("[")[1][:-1].strip()
        type_clb = str
        if type_clb in ["str", "float", "int"]:
            type_clb = eval(type_str)  # pylint: disable=eval-used

        metavar = "VAL"
        k_no_3_char_prefix, k_no_5_char_prefix = k[3:], k[5:]
        if "latitude" in [k, k_no_3_char_prefix]:
            metavar = "LAT"
        if "longitude" in [k, k_no_3_char_prefix]:
            metavar = "LNG"
        if "time" in [k, k_no_3_char_prefix, k_no_5_char_prefix]:
            metavar = "TIME"
        if "radiuskm" in [k, k_no_3_char_prefix]:
            metavar = "DIST"

        parser.add_argument(
            "--" + k,
            help=arg_doc_dict[k],
            metavar=metavar,
            type=type_clb,
            required=False,
            default=None,
        )

    args = parser.parse_args()

    fields = {k: v for k, v in vars(args).items() if k in query_annotations}
    query = Query(**fields)
    if args.mode == "download":
        download(output_file="/dev/stdout", query=query)
    else:
        logger.error("Only 'download' mode is supported for now")
        # logger.error("Invalid mode selected")
        return 1

    return 0


if __name__ == "__main__":
    main()
