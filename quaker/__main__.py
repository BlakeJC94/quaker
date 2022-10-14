import argparse
import logging
from typing import Tuple, Dict

from . import (
    __version__,
    download,
    Query,
)

logger = logging.getLogger(__name__)


def get_query_docs() -> Tuple[str, Dict[str, Tuple[str, str, callable]]]:
    doc = Query.__doc__
    annotations = Query.__annotations__

    _head_doc, _arg_doc = doc.split("Args:")
    _arg_doc = _arg_doc.replace("\n" + 12 * " ", " ")
    query_info = "\n".join(_head_doc.splitlines()[1:])

    args_info = {}
    for entry in _arg_doc.split("\n" + 4 * " "):
        if ":" not in entry:
            continue
        name, desc = entry.split(":", 1)
        name = name.strip()
        desc = desc.strip().lower()

        type_str = str(annotations[name])
        type_str = type_str.removeprefix("Optional[").removesuffix("]")
        type_str = type_str.split(",")[0].strip().removesuffix(",")
        type_str = type_str if type_str in ["float", "int"] else "str"
        type_clb = eval(type_str)  # pylint: disable=eval-used

        metavar = "VAL"
        name_no_3_char_prefix = name[3:]
        if "latitude" in [name, name_no_3_char_prefix]:
            metavar = "LAT"
        elif "longitude" in [name, name_no_3_char_prefix]:
            metavar = "LNG"
        elif name in ["starttime", "endtime", "updatedafter"]:
            metavar = "TIME"
        elif "radiuskm" in [name, name_no_3_char_prefix]:
            metavar = "DIST"

        args_info[name] = (desc, metavar, type_clb)

    return query_info, args_info


def main():
    """Entrypoint for CLI script"""

    query_info, args_info = get_query_docs()
    parser = argparse.ArgumentParser(
        description="Access USGS Earthquake dataset" + query_info,
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

    for name, (desc, metavar, type_clb) in args_info.items():
        parser.add_argument(
            "--" + name,
            help=desc,
            metavar=metavar,
            type=type_clb,
            required=False,
            default=None,
        )

    input_args = parser.parse_args()

    fields = {k: v for k, v in vars(input_args).items() if k in args_info}
    query = Query(**fields)
    if input_args.mode == "download":
        download(output_file="/dev/stdout", query=query)
    else:
        logger.error("Only 'download' mode is supported for now")
        # logger.error("Invalid mode selected")
        return 1

    return 0


if __name__ == "__main__":
    main()
