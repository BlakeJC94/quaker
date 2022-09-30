from pkg_resources import get_distribution

from .download import download
from .log import setup_logging
from .src.query import Query

setup_logging()

__all__ = [
    "__version__",
    "download",
    "Query",
]
__version__ = get_distribution("quaker").version
