"""
Utilities for accessing waveform data from various sources.

:copyright:
    Conor A. Bacon
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

import pathlib

import numpy as np
import obspy


def read_data(
    archive_root: pathlib.Path, read_date: obspy.UTCDateTime, all_stations: list
) -> dict:
    """
    Read in a day of data and prepare it for FMF input.

    Parameters
    ----------
    archive_root: Base path of the raw waveform archive.
    read_date: Date for which to read and prepare data.
    all_stations: List of stations for which to look for data.

    Returns
    -------
    data: Dictionary containing the keys relevant for FMF searches.

    """

    st = obspy.Stream()
    for station in all_stations:
        network, station = station.split(".")

        for delta in [-1, 0, 1]:
            tmp_read_date = read_date + delta * 86400
            try:
                st += obspy.read(
                    archive_root
                    / f"{tmp_read_date.year}/{network}/{station}/BH*/*.{tmp_read_date.julday:03d}"
                )
            except:
                continue

    st.trim(
        starttime=obspy.UTCDateTime(f"{read_date.year}-{read_date.julday:03d}") - 600,
        endtime=obspy.UTCDateTime(f"{read_date.year}-{read_date.julday:03d}")
        + 87000
        - st[0].stats.delta,
    )

    st.merge(method=0, fill_value="interpolate")

    st.detrend("linear")
    st.detrend("constant")
    st.filter("bandpass", freqmin=2.0, freqmax=16.0, corners=4, zerophase=True)
    start_trim = obspy.UTCDateTime(f"{read_date.year}-{read_date.julday:03d}")
    end_trim = start_trim + 86400 - st[0].stats.delta
    st.trim(starttime=start_trim, endtime=end_trim)

    stations = list(set([f"{tr.stats.network}.{tr.stats.station}" for tr in st]))

    data_waveforms = np.zeros(
        [len(stations), 3, int(st[0].stats.sampling_rate * 86400)], dtype=np.float32
    )

    k, available_stations = 0, []
    for _, station in enumerate(all_stations):
        if station not in stations:
            continue
        station = station.split(".")[1]
        for j, component in enumerate("NEZ"):
            st_station_comp = st.select(station=station, component=component)
            data = np.zeros(int(st_station_comp[0].stats.sampling_rate * 86400))
            position = int(
                (st_station_comp[0].stats.starttime - start_trim)
                // st_station_comp[0].stats.delta
            )
            data[position:position + len(st_station_comp[0].data)] = st_station_comp[0].data
            data_waveforms[k, j, :] = data
        k += 1
        available_stations.append(station)

    data = {}
    metadata = {}
    metadata["stations"] = available_stations
    metadata["components"] = ["BHN", "BHE", "BHZ"]
    metadata["date"] = st[0].stats.starttime
    metadata["sampling_rate"] = st[0].stats.sampling_rate
    data["metadata"] = metadata
    data["waveforms"] = data_waveforms

    return data
