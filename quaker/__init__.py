from pkg_resources import get_distribution

from .log import setup_logging
from .core.query import Query
from .core.client import Client

setup_logging()

__all__ = [
    "__version__",
    "download",
    "Query",
    "Client",
]
__version__ = get_distribution("quaker").version
