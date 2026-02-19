"""
Basic utilities for Pick information encapsulation.

:copyright:
    Conor A. Bacon
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

from dataclasses import dataclass

import obspy
import polars as pl


@dataclass
class Pick:
    
    phase: str
    pick_time: obspy.UTCDateTime
    station: str
    uncertainty: float | None = None
    pick_snr: float
    pick_type: str

# Station,Phase,ModelledTime,PickTime,PickError,SNR,Residual


def qmdf2picks(df: pl.DataFrame) -> list[Pick]:
    """
    Utility to convert a dataframe of QuakeMigrate picks to a list of Pick objects.

    Parameters
    ----------
    df:
        A DataFrame of picks in the QuakeMigrate output format.

    Return
    ------
     :
        A list of Pick objects.

    """

    picks = []
    for pick_info in df.iter_rows(named=True):
        if pick_info[""]
        pick = Pick(
            phase=pick_info["Phase"],
            pick_time=pick_info["PickTime"],

        )
        picks.append(pick)

    return picks
