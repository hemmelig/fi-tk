"""
Input/output module for working with miniSEED data stored in either:

    - a local filesystem archive with a regular directory path pattern
    - a remote server operating an FDSN webservice for data access

:copyright:
    2026, Conor A. Bacon
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from datetime import datetime as dt, timedelta as td
from enum import Enum
from typing import Any, ClassVar, Mapping, Protocol

import obspy
import polars as pl
from obspy.clients.fdsn import Client as FDSNClient

try:
    from seismonpy.norsardb import Client as SeisMonClient
except ModuleNotFoundError as e:
    _SEISMON_IMPORT_ERROR = e
else:
    _SEISMON_IMPORT_ERROR = None

from fitk.utils.picks import Pick


class WaveformAccess(str, Enum):
    CONTINUOUS = "continuous"
    EVENT = "event"


class ContinuousWaveformClient(Protocol):
    def get_waveforms(
        self,
        network: str,
        station: str,
        location: str,
        channels: str,
        starttime: dt,
        endtime: dt,
        pre_pad: float = 0.0,
        post_pad: float = 0.0,
    ) -> obspy.Stream: ...


class EventWaveformClient(Protocol):
    def get_event_waveforms(
        self,
        event_id: str,
        network: str | None = None,
        station: str | None = None,
        location: str | None = None,
        channels: str | None = None,
        starttime: dt | None = None,
        endtime: dt | None = None,
        pre_pad: float = 0.0,
        post_pad: float = 0.0,
    ) -> obspy.Stream: ...


WaveformClient = ContinuousWaveformClient | EventWaveformClient


@dataclass(slots=True)
class QMEventClient:
    root: pathlib.Path
    waveforms_pattern: str
    picks_pattern: str

    access: ClassVar[WaveformAccess] = WaveformAccess.EVENT

    def get_event_waveforms(
        self,
        event_id: str,
        network: str | None = None,
        station: str | None = None,
        location: str | None = None,
        channels: str | None = None,
        starttime: dt | None = None,
        endtime: dt | None = None,
        pre_pad: float = 0.0,
        post_pad: float = 0.0,
    ) -> obspy.Stream:
        """
        Read pre-cut event waveforms from the outputs of a QuakeMigrate locate run.

        Parameters
        ----------
        event_id:
            Unique identifier for the event, determined by QuakeMigrate.
        network:
            The network code of data to be loaded from the archive.
        station:
            The station code of data to be loaded from the archive.
        location:
            The location code of data to be loaded from the archive.
        channels:
            The FDSN channel codes of data to be loaded from the archive.
        starttime:
            First timestamp of data to be loaded from the archive.
        endtime:
            Final timestamp of data to be loaded from the archive.
        pre_pad:
            Optional time-padding to account for potential tapering.
        post_pad:
            Optional time-padding to account for potential tapering.

        Returns
        -------
        st:
            Stream containing the data that has been loaded from the archive.

        """

        event_file = self.root / self.waveforms_pattern.format(event_id=event_id)
        if not event_file.exists():
            raise FileNotFoundError(f"No precut waveform file: {event_file}")

        st = obspy.read(event_file)
        st = st.select(
            network=network, station=station, location=location, channel=channels
        )
        if starttime is not None and endtime is not None:
            st.trim(
                starttime=obspy.UTCDateTime(starttime) - pre_pad,
                endtime=obspy.UTCDateTime(endtime) + post_pad - st[0].stats.delta,
            )

        return st

    def get_event_picks(self, event_id: str, prefer_auto: bool = True) -> list[Pick]:
        """
        Read phase arrival picks from the outputs of a QuakeMigrate locate run.

        Parameters
        ----------
        event_id:
            Unique identifier for the event, determined by QuakeMigrate.
        prefer_auto:
            Toggle to use automatic phase arrival picks vs modelled phase arrival times.

        Returns
        -------
        picks:
            List of phase arrival picks.

        """

        picks_file = self.root / self.picks_pattern.format(event_id=event_id)
        if not picks_file.exists():
            raise FileNotFoundError(f"No picks file: {picks_file}")

        picks_df = pl.read_csv(picks_file)

        picks: list[Pick] = []
        for row in picks_df.iter_rows(named=True):
            phase = str(row["Phase"])
            station = str(row["Station"])

            pick_time_raw = row["PickTime"]
            model_time_raw = row["ModelledTime"]

            has_auto = pick_time_raw not in (None, "-1", -1, "")
            if prefer_auto and has_auto:
                pick_time = obspy.UTCDateTime(pick_time_raw)
                pick_type = "auto"
            else:
                pick_time = obspy.UTCDateTime(model_time_raw)
                pick_type = "modelled"

            snr = None
            if "SNR" in row and row["SNR"] not in (None, "", "-1", -1):
                try:
                    snr = float(row["SNR"])
                except Exception:
                    snr = None

            uncertainty = None
            if "PickError" in row and row["PickError"] not in (None, "", "-1", -1):
                try:
                    uncertainty = float(row["PickError"])
                except Exception:
                    uncertainty = None

            picks.append(
                Pick(
                    station=station,
                    phase=phase,
                    time=pick_time,
                    type=pick_type,
                    snr=snr,
                    uncertainty=uncertainty,
                )
            )

        return picks


@dataclass(slots=True)
class LocalArchiveClient:
    root: pathlib.Path
    format: str

    access: ClassVar[WaveformAccess] = WaveformAccess.CONTINUOUS

    def get_waveforms(
        self,
        network: str,
        station: str,
        location: str,
        channels: str,
        starttime: dt,
        endtime: dt,
        pre_pad: float = 0.0,
        post_pad: float = 0.0,
    ) -> obspy.Stream:
        """
        Read data from a local waveform archive.

        Parameters
        ----------
        network:
            The network code of data to be loaded from the archive.
        station:
            The station code of data to be loaded from the archive.
        location:
            The location code of data to be loaded from the archive.
        channels:
            The FDSN channel codes of data to be loaded from the archive.
        starttime:
            First timestamp of data to be loaded from the archive.
        endtime:
            Final timestamp of data to be loaded from the archive.
        pre_pad:
            Optional time-padding to account for potential tapering.
        post_pad:
            Optional time-padding to account for potential tapering.

        Returns
        -------
        st:
            Stream containing the data that has been loaded from the archive.

        """

        st = obspy.Stream()
        read_from = starttime - td(seconds=pre_pad)
        while read_from.date() <= (endtime + td(seconds=post_pad)).date():
            glob_path = self.format.format(
                network=network,
                station=station,
                location=location,
                channels=channels,
                datetime=read_from,
                year=read_from.year,
                jday=read_from.timetuple().tm_yday,
            )
            data_files = self.root.glob(glob_path)
            for data_file in data_files:
                st += obspy.read(data_file)

            read_from += td(days=1)

        st.merge(method=-1)
        st.trim(
            starttime=obspy.UTCDateTime(starttime) - pre_pad,
            endtime=obspy.UTCDateTime(endtime) + post_pad - st[0].stats.delta,
        )

        return st


@dataclass(slots=True)
class FDSNWaveformClientWrapper:
    base_url: str
    timeout: int = 60
    _client: FDSNClient = field(init=False)

    access: ClassVar[WaveformAccess] = WaveformAccess.CONTINUOUS

    def __post_init__(self) -> None:
        self._client = FDSNClient(self.base_url, timeout=self.timeout)

    def get_waveforms(
        self,
        network: str,
        station: str,
        location: str,
        channels: str,
        starttime: dt,
        endtime: dt,
        pre_pad: float = 0.0,
        post_pad: float = 0.0,
    ) -> obspy.Stream:
        """
        Passthrough for the ObsPy FDSN Client `get_waveforms` method.

        Parameters
        ----------
        network:
            The network code of data to be loaded from the remote FDSN server.
        station:
            The station code of data to be loaded from the remote FDSN server.
        location:
            The location code of data to be loaded from the remote FDSN server.
        channels:
            The FDSN channel codes of data to be loaded from the remote FDSN server.
        starttime:
            First timestamp of data to be loaded from the remote FDSN server.
        endtime:
            Final timestamp of data to be loaded from the remote FDSN server.
        pre_pad:
            Optional time-padding to account for potential tapering.
        post_pad:
            Optional time-padding to account for potential tapering.

        Returns
        -------
        st:
            Stream containing the data that has been loaded from the remote FDSN server.

        """

        starttime = obspy.UTCDateTime(starttime) - pre_pad
        endtime = obspy.UTCDateTime(endtime) + post_pad

        return self._client.get_waveforms(
            network, station, location, channels, starttime, endtime
        )


@dataclass(slots=True)
class SeisMonWaveformClientWrapper:
    db_path: str | None = None
    db_archive_path: str | None = None
    inventories_path: str | None = None
    cache_waveforms: bool | None = None
    load_response: bool | None = None
    inventory_index_path: str | None = None
    noresponse_inventory_path: str | None = None
    response_inventory_path: str | None = None
    static_xml_inventory_path: str | None = None
    index_path: str | None = None

    _client: SeisMonClient = field(init=False)

    access: ClassVar[WaveformAccess] = WaveformAccess.CONTINUOUS

    def __post_init__(self) -> None:
        kwargs: dict[str, Any] = {
            "db_path": self.db_path,
            "db_archive_path": self.db_archive_path,
            "inventories_path": self.inventories_path,
            "cache_waveforms": self.cache_waveforms,
            "load_response": self.load_response,
            "inventory_index_path": self.inventory_index_path,
            "noresponse_inventory_path": self.noresponse_inventory_path,
            "response_inventory_path": self.response_inventory_path,
            "static_xml_inventory_path": self.static_xml_inventory_path,
            "index_path": self.index_path,
        }
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        self._client = SeisMonClient(**kwargs)

    def get_waveforms(
        self,
        network: str,
        station: str,
        location: str,
        channels: str,
        starttime: dt,
        endtime: dt,
        pre_pad: float = 0.0,
        post_pad: float = 0.0,
    ) -> obspy.Stream:
        """
        Passthrough for the SeisMonPy Client `get_waveforms` method.

        Parameters
        ----------
        network:
            The network code of data to be loaded from the SeisMon Client.
        station:
            The station code of data to be loaded from the SeisMon Client.
        location:
            The location code of data to be loaded from the SeisMon Client.
        channels:
            The FDSN channel codes of data to be loaded from the SeisMon Client.
        starttime:
            First timestamp of data to be loaded from the SeisMon Client.
        endtime:
            Final timestamp of data to be loaded from the SeisMon Client.
        pre_pad:
            Optional time-padding to account for potential tapering.
        post_pad:
            Optional time-padding to account for potential tapering.

        Returns
        -------
        st:
            Stream containing the data that has been loaded from the SeisMon Client.

        """

        starttime = obspy.UTCDateTime(starttime) - pre_pad
        endtime = obspy.UTCDateTime(endtime) + post_pad

        return self._client.get_waveforms(station, channels, starttime, endtime)


def make_waveform_client(config: Mapping[str, Any]) -> WaveformClient:
    """
    Factory function for creating a WaveformClient from a config file.

    Parameters
    ----------
    config:
        The config specifying the waveform data access client.

    Returns
    -------
    client:
        A local, FDSN, or SeisMon waveform client.

    """

    match mode := config["client"]:
        case "local":
            local = config["local"]
            return LocalArchiveClient(
                root=pathlib.Path(local["root"]),
                format=local["format"],
            )
        case "fdsn":
            remote = config["fdsn"]
            return FDSNWaveformClientWrapper(
                base_url=remote["base_url"],
                timeout=int(remote.get("timeout", 60)),
            )
        case "seismon":
            if _SEISMON_IMPORT_ERROR is not None:
                raise RuntimeError(
                    "data.client='seismon' but seismonpy is not installed"
                ) from _SEISMON_IMPORT_ERROR
            remote = config.get("seismon", {})
            return SeisMonWaveformClientWrapper(**remote)
        case "pre_cut_qm":
            local = config["pre_cut_qm"]
            return QMEventClient(
                root=pathlib.Path(local["root"]),
                waveforms_pattern=local["waveforms_pattern"],
                picks_pattern=local["picks_pattern"],
            )
        case _:
            raise ValueError(f"Unknown data.client={mode!r}")
