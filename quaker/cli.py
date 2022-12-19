import argparse
import logging

from . import (
    __version__,
    download,
    Query,
)

logger = logging.getLogger(__name__)

METAVARS = {
    k: value
    for keys, value in [
        (["endtime", "starttime", "updatedafter"], "TIME"),
        (["minlatitude", "maxlatitude", "latitude"], "LAT"),
        (["minlongitude", "maxlongitude", "longitude"], "LNG"),
        (["maxradiuskm"], "DIST"),
    ]
    for k in keys
}


def run(cli_input: Optional[List[str]] = None) -> int:
    parser = get_parser()
    query_input = parser.parse_args(cli_input)
    if all(var is None for _, var in vars(query_input).items()):
        parser.parse_args(["-h"])
    # pylint: disable=unsupported-membership-test
    query = Query(**{k: v for k, v in vars(query_input).items() if k in Query.fields})
    if query_input.mode == "download":
        download(output_file="/dev/stdout", query=query)
    else:
        logger.error("Only 'download' mode is supported for now")
        # logger.error("Invalid mode selected")
        return 1
    return 0


def get_parser() -> argparse.ArgumentParser:
    cli_doc_head = "Access USGS Earthquake dataset."
    cli_doc = "\n\n".join([cli_doc_head, Query.doc_head])
    parser = argparse.ArgumentParser(
        description=cli_doc,
        add_help=True,
    )

    # Allow one optional positional arg to select mode
    parser.add_argument(
        "mode",
        nargs="?",
        type=str,
        help=f"action to perform.",
    )

    for component_class in list(Query.component_classes):
        group = parser.add_argument_group(component_class.name)

        for field_name, field_doc in component_class.field_docs.items():

            field_type = component_class.field_types[field_name]
            add_arg_kwargs = dict(
                help=field_doc,
                required=False,
                default=None,
            )
            if field_type is bool:
                add_arg_kwargs["action"] = "store_true"
            else:
                add_arg_kwargs["type"] = field_type
                add_arg_kwargs["metavar"] = METAVARS.get(
                    field_name,
                    str(field_type.__name__).upper(),
                )

            group.add_argument(
                "--" + field_name,
                **add_arg_kwargs,
            )

    return parser
