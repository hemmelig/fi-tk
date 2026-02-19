"""
Basic utilities for Event information encapsulation.

:copyright:
    Conor A. Bacon
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

from dataclasses import dataclass

import obspy

from .archive import Archive
from .picks import Picks


@dataclass
class Event:
    
    id: str
    origin_time: obspy.UTCDateTime
    picks: Picks
    waveforms: obspy.Stream | None = None

    def read_waveforms(self, archive: Archive, padding: float = 10.0) -> None:
        """Load waveforms from a specified archive"""

        max_pick = self.picks["PreferredPicks"].max()

        self.waveforms = archive.read_waveforms(
            self.origin_time - padding, max_pick + padding
        )
