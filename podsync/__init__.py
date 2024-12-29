from importlib.metadata import version as _version

from .download import download

__version__ = _version("podsync")
__all__ = ["download"]
