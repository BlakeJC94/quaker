from functools import partial

from fire import Fire

from . import (
    __version__,
    download,
)

download_cli = partial(download, query=None)
download_cli.__doc__ = download.__doc__
# TODO improve CLI docs
# TODO add CLI to quickstart
# TODO make output_file a kwarg and download to a default location (filename with time of req)


def main():
    Fire(
        dict(
            version=str(__version__),
            download=partial(download, query=None),
        )
    )


if __name__ == "__main__":
    main()
