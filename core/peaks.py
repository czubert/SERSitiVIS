"""
Peak detection in Raman / SERS spectra.
"""
import numpy as np
import pandas as pd
from scipy import signal


def find_peaks(spectrum, prominence=0.05, min_distance=10.0, max_peaks=15):
    """
    Finds peaks in one spectrum
    :param spectrum: Series, index = Raman Shift
    :param prominence: minimal prominence as a fraction of the spectrum's intensity range (0-1)
    :param min_distance: minimal distance between peaks [cm-1]
    :param max_peaks: keep at most this many most prominent peaks (None = all)
    :return: DataFrame with columns: position, intensity, prominence, fwhm (all in spectrum units / cm-1),
             sorted by position
    """
    spectrum = spectrum.dropna().sort_index()
    columns = ['position', 'intensity', 'prominence', 'fwhm']
    if len(spectrum) < 5:
        return pd.DataFrame(columns=columns)

    x = spectrum.index.to_numpy(dtype=float)
    y = spectrum.to_numpy(dtype=float)
    step = float(np.median(np.diff(x)))
    span = y.max() - y.min()
    if span <= 0:
        return pd.DataFrame(columns=columns)

    indices, properties = signal.find_peaks(y, prominence=prominence * span,
                                            distance=max(1, int(round(min_distance / step))))
    if not len(indices):
        return pd.DataFrame(columns=columns)

    widths = signal.peak_widths(y, indices, rel_height=0.5)[0] * step
    peaks = pd.DataFrame({'position': x[indices], 'intensity': y[indices],
                          'prominence': properties['prominences'], 'fwhm': widths})
    if max_peaks:
        peaks = peaks.nlargest(max_peaks, 'prominence')
    return peaks.sort_values('position').reset_index(drop=True)


def find_peaks_all(df, **kwargs):
    """
    Peaks of every spectrum
    :param df: DataFrame, one column per spectrum
    :return: DataFrame with an additional 'spectrum' column
    """
    tables = [find_peaks(df[col], **kwargs).assign(spectrum=col) for col in df.columns]
    tables = [table for table in tables if not table.empty]
    if not tables:
        return pd.DataFrame(columns=['spectrum', 'position', 'intensity', 'prominence', 'fwhm'])
    return pd.concat(tables, ignore_index=True)[['spectrum', 'position', 'intensity', 'prominence', 'fwhm']]


def label_once(peaks_table, tolerance=5.0):
    """
    Marks which peaks get a text label: when several spectra have a peak at (nearly) the same position,
    only the highest one is labelled - otherwise labels overlap.
    :return: boolean Series aligned with peaks_table
    """
    labelled = []
    keep = pd.Series(False, index=peaks_table.index)
    for i, row in peaks_table.sort_values('intensity', ascending=False).iterrows():
        if all(abs(row['position'] - position) > tolerance for position in labelled):
            labelled.append(row['position'])
            keep[i] = True
    return keep
