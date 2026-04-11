from importlib.metadata import PackageNotFoundError, version


try:
    __version__ = version("garth-ng")
except PackageNotFoundError:
    __version__ = "0+unknown"
