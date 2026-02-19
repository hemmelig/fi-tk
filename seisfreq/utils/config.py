"""
Utilities for handling config files used by SeisFreq.

:copyright:
    Conor A. Bacon
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

import pathlib
import tomllib


def read_config(config_filepath: pathlib.Path) -> dict:
    """Utility to read in a SeisFreq config file."""

    if not config_filepath.is_file():
        raise FileNotFoundError("You must provide an FI config file that exists.")

    with config_filepath.open("rb") as f:
        config = tomllib.load(f)

    return config
