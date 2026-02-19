"""
Visualisation tools for SeisFreq.

:copyright:
    Conor A. Bacon
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

import matplotlib.pyplot as plt
import obspy


def plot_waveforms(ax: plt.Axes, trace: obspy.Trace, event) -> plt.Axes:
    """
    
    """

    ax.plot(
        trace.times(),
        # secs + pre_time,
        trace.data / trace.max(),
        color="#2ca25f",
        lw=1,
    )

    # Plot picks
    ax.axvline(2 * pre_time, ls=":", c="r")
    ax.axvline(2 * pre_time + s_p_time, ls=":", c="dodgerblue")

    return ax


def plot_spectrogram(ax: plt.Axes, trace: obspy.Trace) -> plt.Axes:
    """Utility function for plotting the spectrogram for an event on an axis."""

    trace.spectrogram(axes=ax)

    ax.axvline(2 * pre_time, ls=":", c="r")
    ax.axvline(2 * pre_time + s_p_time, ls=":", c="dodgerblue")

    return ax


def plot_frequency_index(ax: plt.Axes, spectral_info: dict, bands: dict) -> plt.Axes:
    """Utility function for plotting the frequency index measurement data on an axis."""

    ax.semilogy(spectral_info["frequencies"], spectral_info["spectra"])

    ax.axvspan(
        bands["low_band"][0],
        bands["low_band"][1],
        alpha=0.2,
        color="blue",
        label="Low Band",
    )
    ax.axvspan(
        bands["high_band"][0],
        bands["high_band"][1],
        alpha=0.2,
        color="red",
        label="High Band",
    )

    return ax


def plot_stacked_fi():
    pass


def plot_station_fi(
    frequency_index: float,
    spec_info: dict,
    bands: dict,
    event_id: str,
    station: str | None = None,
) -> plt.Figure:
    """
    Plot a
    Plot the power spectrum and mark the frequency bands used for FI calculation.

    Parameters
    ----------

    """

    fig = plt.figure(figsize=(15, 5), layout="constrained")
    axes = fig.subplot_mosaic(
        """
        AAAABBBBB
        CCCCBBBBB
        """
    )
    ax = axes["B"]

    ax.semilogy(spec_info["frequencies"], spec_info["spectra"])

    ax.axvspan(
        bands["low_band"][0],
        bands["low_band"][1],
        alpha=0.2,
        color="blue",
        label="Low Band",
    )
    ax.axvspan(
        bands["high_band"][0],
        bands["high_band"][1],
        alpha=0.2,
        color="red",
        label="High Band",
    )

    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Power Spectral Density")
    if station is None:
        ax.set_title(f"Event {event_id} - FI = {frequency_index:3.5f}")
    else:
        ax.set_title(
            f"Event {event_id} - Station {station} - FI = {frequency_index:3.5f}"
        )
    ax.legend()

    return fig
