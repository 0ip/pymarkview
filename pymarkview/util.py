import sys
from pathlib import Path


def resource_path(relative_path):
    """ Get absolute path to PyInstaller resource """
    try:
        return str(Path(sys._MEIPASS).joinpath(Path(relative_path).name))
    except Exception:
        return relative_path
