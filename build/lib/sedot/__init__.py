"""
sedot - CLI video scraper for Instagram posts/reels and Threads.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("sedot")
except PackageNotFoundError:  # pragma: no cover - fallback for local execution
    __version__ = "0.0.0"

__all__ = ["__version__"]
