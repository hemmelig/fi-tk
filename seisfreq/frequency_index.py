"""
Core computational tools for frequency index analysis.

:copyright:
    Conor A. Bacon
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

import pathlib

import numpy as np
import obspy
from multitaper import MTSpec
from obspy.signal.util import next_pow_2
from scipy import signal


def _fft_spectra(trace: obspy.Trace) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute the frequencies and corresponding powers at each frequency using
    the NumPy Fast Fourier Transform.

    Parameters
    ----------
    trace: Waveform data for an event from which to compute spectra.

    Returns
    -------
    frequencies: The range of frequencies at which spectral powers have been computed.
    spectra: Power at each frequency.

    """

    frequencies = np.arange(trace.stats.npts) / (
        trace.stats.npts / trace.stats.sampling_rate
    )  # +ve/-ve frequency range
    positive_frequencies = range(trace.stats.npts // 2)
    frequencies = frequencies[positive_frequencies]

    spectra = np.fft.fft(trace.data) / trace.stats.npts
    spectra = 2 * (
        np.pow(abs(spectra[positive_frequencies]), 2) / (0.01 / trace.stats.npts)
    )
    spectra = np.sqrt(spectra / np.amax(spectra))
    # spectra = abs(spectra[positive_frequencies])
    # spectra = spectra / np.amax(spectra)  # normalising

    return frequencies, spectra


def _mtspec_spectra(trace: obspy.Trace) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute the frequencies and corresponding powers at each frequency using
    the Multi-Taper Spectral approach.

    Parameters
    ----------
    trace: Waveform data for an event from which to compute spectra.

    Returns
    -------
    frequencies: The range of frequencies at which spectral powers have been computed.
    spectra: Power at each frequency.

    """

    mtspec = MTSpec(
        trace.data,
        nw=3,
        dt=trace.stats.delta,
        nfft=next_pow_2(len(trace.data)),
    )
    frequencies, spectra = mtspec.rspec()

    return frequencies, spectra


def _welch_spectra(trace: obspy.Trace) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute the frequencies and corresponding powers at each frequency using
    the SciPy Welch function.

    Parameters
    ----------
    trace: Waveform data for an event from which to compute spectra.

    Returns
    -------
    frequencies: The range of frequencies at which spectral powers have been computed.
    spectra: Power at each frequency.

    """

    frequencies, spectra = signal.welch(
        trace.data,
        fs=trace.stats.sampling_rate,
        nperseg=min(len(trace.data), 1024),
        scaling="density",
    )

    return frequencies, spectra


METHODS = {
    "welch": _welch_spectra,
    "fft": _fft_spectra,
    "mtspec": _mtspec_spectra,
}


def compute_fi(
    frequencies: np.ndarray, spectra: np.ndarray, bands: dict
) -> tuple[float, dict]:
    """
    Compute the frequency index given a distribution of frequencies and powers at
    each frequency.

    Parameters
    ----------
    frequencies: The range of frequencies at which spectral powers have been computed.
    spectra: Power at each frequency.
    bands: The low and high frequency bands for which to calculate the FI.

    Returns
    -------
    frequency_index: The computed FI.
    spec_info: Energies computed within the low and high bands and other spectral data.

    """

    def get_band_energy(freq_range):
        mask = (frequencies >= freq_range[0]) & (frequencies <= freq_range[1])
        return np.mean(spectra[mask])

    low_energy = get_band_energy(bands["low_band"])
    high_energy = get_band_energy(bands["high_band"])

    frequency_index = np.log10(high_energy / low_energy)

    spec_info = {
        "low_band_energy": low_energy,
        "high_band_energy": high_energy,
        "spectra": spectra,
        "frequencies": frequencies,
    }

    return frequency_index, spec_info
