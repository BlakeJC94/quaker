from fire import Fire
from . import (
    __version__,
    download,
)


def main():
    Fire(
        dict(
            version=str(__version__),
            download=download,
        )
    )


if __name__ == "__main__":
    main()
