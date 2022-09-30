from pkg_resources import get_distribution

from .download import download
from .src.query import Query

__all__ = [
    "__version__",
    "download",
    "Query",
]
__version__ = get_distribution("quaker").version
