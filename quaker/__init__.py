from pkg_resources import get_distribution

# from .dashboard import dashboard
from .download import download
from .log import setup_logging
from .core.query import Query

setup_logging()

__all__ = [
    "__version__",
    "download",
    "dashboard",
    "Query",
]
__version__ = get_distribution("quaker").version
