"""
Basic utilities for Event encapsulation.

:copyright:
    Conor A. Bacon
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

import pathlib
from dataclasses import dataclass


@dataclass
class Archive:
    
    base_path: pathlib.Path
    structure: str


@dataclass
class QuakeMigrateArchive(Archive):

    output_path: pathlib.Path
    run_name: str
