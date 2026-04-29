"""LinkVault package."""

__all__ = ["__version__", "__build_commit__", "__build_date__", "__display_version__"]

__version__ = "0.1.0"

try:
    from ._build import __build_commit__, __build_date__
except (ImportError, AttributeError):
    __build_commit__ = "dev"
    __build_date__ = "dev"

if __build_commit__ == "dev":
    __display_version__ = f"{__version__} (dev)"
else:
    __display_version__ = f"{__version__} ({__build_commit__}, {__build_date__})"
