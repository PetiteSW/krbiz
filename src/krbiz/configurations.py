import pathlib

DEFAULT_DIR = pathlib.Path.home() / pathlib.Path(".krbiz")
if not DEFAULT_DIR.exists():
    DEFAULT_DIR.mkdir()
