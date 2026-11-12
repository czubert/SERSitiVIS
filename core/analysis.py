"""
Calculations: Relative Standard Deviation (RSD) and Enhancement Factor (EF).
"""
import numpy as np
import pandas as pd

from core.processing import subtract_baseline

AVOGADRO = 6.02214076e23  # [1/mol]


#
# # RSD
#
def rsd_stats(values):
    """
    :param values: Series, one value per spectrum
    :return: (mean, standard deviation, RSD as a fraction)
    """
    mean, std = values.mean(), values.std()
    return mean, std, std / mean


def rsd_table(peak1, peak2=None, degree=3):
    """
    RSD of the peak intensity (or of peak1/peak2 intensity ratio) between spectra,
    for raw and baseline-corrected data.
    :param peak1: DataFrame, Raman Shift range of the first peak, one column per spectrum
    :param peak2: DataFrame or None, second peak for the peak-to-peak ratio
    :param degree: int, polynomial degree for baseline correction
    :return: DataFrame
    """
    def values(p1, p2):
        return p1.max() if p2 is None else p1.max() / p2.max()

    results = {}
    for label, p1, p2 in [('RAW data', peak1, peak2),
                          ('Baseline corrected',
                           subtract_baseline(peak1, degree),
                           None if peak2 is None else subtract_baseline(peak2, degree))]:
        mean, std, rsd = rsd_stats(values(p1, p2))
        results[label] = {'Mean': mean, 'Standard deviation': std, 'RSD[%]': rsd * 100}

    return pd.DataFrame(results)


#
# # Enhancement Factor
# Method: 'Enhancement Factor (EF): teoria i praktyka', IChF PAN 2020
#
def num_of_molecules(conc, vol):
    """
    Number of molecules in the solution
    :param conc: Float, concentration [mol/dm^3]
    :param vol: Float, volume [ml]
    :return: Float
    """
    return AVOGADRO * conc * vol * 10 ** (-3)


def laser_spot_diameter(wave_length_nm, numerical_aperture):
    """
    :param wave_length_nm: laser wavelength [nm]
    :param numerical_aperture: lens numerical aperture
    :return: Float, diameter of the laser spot [m]
    """
    return 1.22 * wave_length_nm * 10 ** (-9) / numerical_aperture


def laser_spot_area(spot_diameter):
    """:return: Float, area of the laser spot [m^2]"""
    return np.pi * (spot_diameter / 2) ** 2


def n_sers(num_molecules, spot_area, coverage, platform_area):
    """
    Number of molecules within the laser spot on the SERS platform
    :param platform_area: [m^2], including surface development coefficient
    """
    return num_molecules * spot_area * coverage / platform_area


def n_raman(spot_area, penetration_depth, density, molecular_weight):
    """
    Number of molecules of the solid compound irradiated during Raman measurement
    :param spot_area: [m^2]
    :param penetration_depth: [m]
    :param density: [g/cm^3]
    :param molecular_weight: [g/mol]
    """
    volume = spot_area * penetration_depth  # [m^3]
    mass = volume * density * 10 ** 6  # [g]
    return mass / molecular_weight * AVOGADRO


def enhancement_factor(i_sers, n_sers_, i_raman, n_raman_):
    return (i_sers / n_sers_) * (n_raman_ / i_raman)


def peak_intensity(df, low, high):
    """
    Peak intensity read from the mean spectrum
    :param df: DataFrame, one column per spectrum
    :return: Dict: intensity, position, n spectra, SD of per-spectrum peak intensities (None for one spectrum)
    """
    mask = (df.index >= low) & (df.index <= high)
    if not mask.any():
        return None
    mean_peak = df[mask].mean(axis=1)
    per_spectrum = df[mask].max()
    return {'intensity': mean_peak.max(),
            'position': mean_peak.idxmax(),
            'n': df.shape[1],
            'sd': per_spectrum.std() if df.shape[1] > 1 else None,
            'rsd': per_spectrum.std() / per_spectrum.mean() if df.shape[1] > 1 else None}
