"""
Visualisation tools for SeisFreq.

:copyright:
    Conor A. Bacon
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt


if TYPE_CHECKING:
    from obspy import Trace, UTCDateTime

    from fitk.frequency_index import FrequencyIndexMeasurement


plt.style.use(pathlib.Path(__file__).parent / "assets/basic.mplstyle")


def plot_waveforms(ax: plt.Axes, trace: Trace) -> plt.Axes:
    """Populate waveform panel of frequency index summary."""

    ax.plot(
        trace.times(),
        trace.data / trace.max(),
        color="#000000",
    )
    ax.set_xlim([trace.times()[0], trace.times()[-1]])
    ax.set_ylim([-1.1, 1.1])
    ax.set_yticks([-1.0, -0.5, 0.0, 0.5, 1.0])
    ax.set_xlabel("Time, s")
    ax.set_ylabel("Normalised amplitude")

    return ax


def plot_spectrogram(ax: plt.Axes, trace: Trace) -> plt.Axes:
    """Populate spectrogram panel of frequency index summary."""

    trace.spectrogram(axes=ax)
    ax.set_xlim([trace.times()[0], trace.times()[-1]])
    ax.set_ylabel("Frequency, Hz")

    return ax


def plot_frequency_index(ax: plt.Axes, spectral_info: dict, bands: dict) -> plt.Axes:
    """Populate power spectrum panel of frequency index summary."""

    ax.semilogy(spectral_info["frequencies"], spectral_info["spectra"])

    ax.axvspan(
        bands["low_band"][0],
        bands["low_band"][1],
        alpha=0.2,
        color="#8856a7",
        label="Low Band",
    )
    ax.axvspan(
        bands["high_band"][0],
        bands["high_band"][1],
        alpha=0.2,
        color="#2ca25f",
        label="High Band",
    )
    ax.set_xlim([0, spectral_info["frequencies"][-1]])
    ax.set_ylabel("Amplitude, dB")
    ax.yaxis.set_label_position("right")
    ax.set_xlabel("Frequency, Hz")

    return ax


def single_station_summary(
    waveforms: Trace,
    fi_measurement: FrequencyIndexMeasurement,
    window: tuple[UTCDateTime, UTCDateTime, UTCDateTime],
) -> plt.Figure:
    """
    Multi-panel summary of a frequency index measurement made at a single station.

    Parameters
    ----------
    waveforms:
        Waveform trace used for the frequency index measurement.
    fi_measurement:

    pick_time


    """

    fig = plt.figure(figsize=(17.5 / 2.54, 6 / 2.54), constrained_layout=True)
    axes = fig.subplot_mosaic(
        """
        AAAABBBBB
        CCCCBBBBB
        """
    )

    # Plot spectrograms
    ax = axes["A"]
    ax = plot_spectrogram(ax, waveforms)
    ax.set_xticklabels([])
    ax.set_ylim([0, 60])
    ax.axvspan(
        window[0] - waveforms.stats.starttime,
        window[2] - waveforms.stats.starttime,
        color="#23a576",
        alpha=0.2,
    )
    ax.axvline(window[1] - waveforms.stats.starttime, color="#23a576", linestyle="--")

    # Plot waveforms
    ax = axes["C"]
    ax = plot_waveforms(ax, waveforms)
    ax.axvspan(
        window[0] - waveforms.stats.starttime,
        window[2] - waveforms.stats.starttime,
        color="#23a576",
        alpha=0.2,
    )
    ax.axvline(window[1] - waveforms.stats.starttime, color="#23a576", linestyle="--")

    # Plot frequency index measurement
    ax = axes["B"]
    ax = plot_frequency_index(ax, fi_measurement.spectral_information, fi_measurement.bands)
    ax.tick_params(left=False, labelleft=False, right=True, labelright=True)
    ax.set_xlim([0, 60])
    ax.text(
        0.5,
        0.1,
        f"Frequency Index = {fi_measurement.frequency_index:5.3f}",
        ha="center",
        va="center",
        transform=ax.transAxes,
    )
    ax.legend()

    return fig
