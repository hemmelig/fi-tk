"""
Basic utilities for Pick information encapsulation.

:copyright:
    2026, Conor A. Bacon
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

from dataclasses import dataclass
from typing import Iterable

import obspy


@dataclass
class Pick:
    station: str
    phase: str
    time: obspy.UTCDateTime
    type: str = "unknown"
    snr: float | None = None
    uncertainty: float | None = None


def filter_picks(
    picks: Iterable[Pick],
    *,
    station: str | list[str] | None = None,
    phase: str | None = "P",
    type_: str | None = None,
    min_snr: float | None = None,
    max_uncertainty: float | None = None,
) -> list[Pick]:
    """
    Filter a list of Pick objects using common selection criteria.

    Parameters
    ----------
    picks:
        Iterable of Pick objects.
    station:
        Station code or list of station codes to keep.
    phase:
        Phase to keep (e.g., "P", "S"). If None, do not filter on phase.
    type_:
        Pick type to keep (e.g., "auto", "modelled"). If None, do not filter.
    min_snr:
        Require pick.snr >= min_snr. Picks with snr=None are excluded.
    max_uncertainty:
        Require pick.uncertainty <= max_uncertainty.
        Picks with uncertainty=None are excluded.

    Returns
    -------
    out:
        Filtered picks.

    """

    out: list[Pick] = list(picks)

    if station is not None:
        if isinstance(station, str):
            stations = {station}
        else:
            stations = set(station)

        out = [p for p in out if p.station in stations]

    if phase is not None:
        phase_upper = phase.upper()
        out = [p for p in out if p.phase.upper() == phase_upper]

    if type_ is not None:
        type_lower = type_.lower()
        out = [p for p in out if p.type.lower() == type_lower]

    if min_snr is not None:
        out = [p for p in out if p.snr is not None and p.snr >= min_snr]

    if max_uncertainty is not None:
        out = [
            p
            for p in out
            if p.uncertainty is not None and p.uncertainty <= max_uncertainty
        ]

    return out
