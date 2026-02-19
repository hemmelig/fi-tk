"""
Command-line utility entry point for the SeisFreq tools.

:copyright:
    Conor A. Bacon
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

import argparse
import pathlib

import matplotlib.pyplot as plt
import numpy as np
import obspy
import polars as pl

from seisfreq.frequency_index import compute_fi, METHODS
from seisfreq.visualise import plot_station_fi
from seisfreq.utils import read_config, Event


def analyse_station_fi(event: Event, station: str, config: dict) -> None:
    """
    Compute and visualise the frequency index for a single event.

    Parameters
    ----------
    event:
        The event for which to compute the frequency index.
    station:
        Unique identifier for the station at which to calculate the frequency index.
    config:
        Various configuration information for frequency index computation.

    """

    st = event.waveforms.select(
        station=station,
        component=config["measure_on"],
    )

    window_starttime = event.picks[station] - config["pre_cut"]
    window_endtime = event.picks[station]  + config["post_cut"] - st[0].stats.delta

    windowed_trace = st.slice(starttime=window_starttime, endtime=window_endtime)[0]
    frequencies, spectra = METHODS[config["method"]](windowed_trace)

    frequency_index, spec_info = compute_fi(frequencies, spectra, config["bands"])

    fig = plot_station_fi(
        event,
        station,
        frequency_index,
        spec_info,
        config,
    )

    fname = (
        config["outpath"]
        / f"plots/{event.id}/fi-{station}-{config['method']}.png"
    )
    fname.parent.mkdir(exist_ok=True, parents=True)

    plt.savefig(fname, dpi=400)
    plt.close()


def analyse_stacked_fi(
    event, config
    # event_id, picks, waveforms, config, outdir
) -> list[np.ndarray, np.ndarray]:
    """
    
    """

    pre_stack_frequencies, pre_stack_spectra, i = [], [], 0
    for pick in picks.iter_rows(named=True):
        if i == config["n_stack"]:
            break
        if pick["Phase"] != "P":
            continue
        if pick["PickTime"] == "-1":  # Use modelled traveltime as pick
            pick_time = obspy.UTCDateTime(pick["ModelledTime"])
            if args.only_picked:  # i.e., only compute FI for auto-picks
                continue
        else:  # Use automatic pick made by QuakeMigrate
            pick_time = obspy.UTCDateTime(pick["PickTime"])

        st_tmp = waveforms.select(
            station=pick["Station"],
            component=config["measure_on"],
        )

        window_starttime = pick_time - config["pre_cut"]
        window_endtime = pick_time + config["post_cut"] - st_tmp[0].stats.delta

        windowed_trace = st_tmp.slice(
            starttime=window_starttime, endtime=window_endtime
        )[0]
        frequencies, spectra = METHODS[config["method"]](windowed_trace)
        pre_stack_frequencies.append(frequencies)
        pre_stack_spectra.append(spectra)
        i += 1
    frequencies = sum(pre_stack_frequencies) / config["n_stack"]
    spectra = sum(pre_stack_spectra) / config["n_stack"]

    frequency_index, spec_info = compute_fi(
        frequencies, spectra, config["bands"]
    )

    print(f"Event {event_id} has a stacked FI of: " f"{frequency_index:3.5f}")
    fig = plot_spectrum_with_fi(
        frequency_index,
        spec_info,
        config["bands"],
        event_id,
        pick["Station"],
    )
    fname = outdir / f"plots/{event_id}/fi-stacked-{config['method']}.png"
    fname.parent.mkdir(exist_ok=True, parents=True)
    plt.savefig(fname, dpi=400)
    plt.close()

    fname = outdir / f"measurements/{event_id}-stacked-fi.txt"
    fname.parent.mkdir(exist_ok=True, parents=True)
    with fname.open("w") as f:
        print(f"{event_id},{frequency_index}", file=f)


def compute_all_station_fis(
    event_id, picks, waveforms, config
) -> list[np.ndarray, np.ndarray]:
    for pick in picks.iter_rows(named=True):
        if pick["Phase"] != "P":
            continue
        if pick["PickTime"] == "-1":  # Use modelled traveltime as pick
            pick_time = obspy.UTCDateTime(pick["ModelledTime"])
            if args.only_picked:  # i.e., only compute FI for auto-picks
                continue
        else:  # Use automatic pick made by QuakeMigrate
            pick_time = obspy.UTCDateTime(pick["PickTime"])

        st_tmp = waveforms.select(
            station=pick["Station"],
            component=config["measure_on"],
        )

        window_starttime = pick_time - config["pre_cut"]
        window_endtime = pick_time + config["post_cut"] - st_tmp[0].stats.delta

        windowed_trace = st_tmp.slice(
            starttime=window_starttime, endtime=window_endtime
        )[0]
        frequencies, spectra = METHODS[config["method"]](windowed_trace)

        frequency_index, spec_info = compute_fi(
            frequencies, spectra, config["bands"]
        )

        print(
            f"Event {event_id} at {pick['Station']} has an FI of: "
            f"{frequency_index:3.5f}"
        )
        fig = plot_spectrum_with_fi(
            frequency_index,
            spec_info,
            config["bands"],
            event_id,
            pick["Station"],
        )
        fname = (
            args.outpath
            / f"plots/{event_id}/fi-{pick['Station']}-{config['method']}.png"
        )
        fname.parent.mkdir(exist_ok=True, parents=True)
        plt.savefig(fname, dpi=400)
        plt.close()


def cli(args: dict | None = None) -> None:
    """Command-line interface entry point for SeisFreq."""

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-c",
        "--config",
        help="Specify the path to a config file for this FI run.",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--outpath",
        help="Specify the path to output the prepared data files.",
        default=pathlib.Path.cwd() / "data",
    )
    parser.add_argument(
        "--only-picked",
        dest="only_picked",
        action=argparse.BooleanOptionalAction,
        help="Toggle to compute FI using only auto-picks.",
    )
    args = parser.parse_args()

    config = read_config(pathlib.Path(args.config))

    if not isinstance(config["events"], list):
        events = pl.read_csv(config["events"])
        events = events["EventID"]
    else:
        events = config["events"]

    for event_id in events:
        for pick_dir in config["pick_dirs"]:
            pick_file = pathlib.Path(pick_dir) / f"{event_id}.picks"
            if pick_file.is_file():
                picks = pl.read_csv(pick_file)
                break

        # Read data from waveform archive


        cut_waveforms = obspy.read(
            pick_file.parents[1] / f"raw_cut_waveforms/{event_id}.m"
        )
        cut_waveforms.detrend("linear")
        cut_waveforms.detrend("constant")
        cut_waveforms.detrend("demean")
        cut_waveforms.filter(**config["filter"])

        if config["stack"]:
            compute_stacked_fi(event_id, picks, cut_waveforms, config)
        else:
            for station in picks:
                compute_station_fi(event_id, picks, cut_waveforms, config)
            # compute_all_station_fis(event_id, picks, cut_waveforms, fi_config)
