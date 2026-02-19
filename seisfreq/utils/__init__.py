"""
Module containing a collection of utilities for SeisFreq.

:copyright:
    Conor A. Bacon
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

from .config import read_config
from .event import Event


__all__ = [Event, read_config]
