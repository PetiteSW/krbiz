import pathlib

DEFAULT_DIR = pathlib.Path.home() / pathlib.Path(".smallbiz-kr")
if not DEFAULT_DIR.exists():
    DEFAULT_DIR.mkdir()
