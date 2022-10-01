# from functools import partial

# import fire
# from fire import Fire

from . import (
    __version__,
    download,
    Query,
)

# download_cli = partial(download, query=None, output_file="/dev/stdout")
# def download_cli(**kwargs):
#     download(query=None, output_file="/dev/stdout", **kwargs)
# download_cli.__doc__ = download.__doc__.split("\n")[0] + "\n".join(Query.__doc__.split("\n")[1:])
# TODO add CLI to quickstart
# TODO fire sucks, just write one from scratch based on sudokupy




def main():
    # Fire(
    #     dict(
    #         version=str(__version__),
    #         download=download_cli,
    #     )
    # )


if __name__ == "__main__":
    main()
