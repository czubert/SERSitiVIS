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


def ef_from_parameters(p):
    """
    EF from all inputs (works with numbers and numpy arrays - used for Monte Carlo)
    :param p: Dict with keys: concentration [mol/dm3], volume [ml], wavelength [nm], aperture, size_x, size_y [mm],
              development, coverage, depth [m], density [g/cm3], molecular_weight [g/mol], i_sers, i_raman
    """
    n = num_of_molecules(p['concentration'], p['volume'])
    s0 = laser_spot_area(laser_spot_diameter(p['wavelength'], p['aperture']))
    platform = p['size_x'] * p['size_y'] * 10 ** (-6) * p['development']
    return enhancement_factor(p['i_sers'], n_sers(n, s0, p['coverage'], platform),
                              p['i_raman'], n_raman(s0, p['depth'], p['density'], p['molecular_weight']))


def ef_uncertainty(parameters, ranges, relative_sd, draws=20000, seed=0):
    """
    Monte Carlo uncertainty of EF
    :param parameters: Dict of nominal values (see ef_from_parameters)
    :param ranges: Dict {parameter: (low, high)} - uniform distribution within the range
    :param relative_sd: Dict {parameter: relative SD} - normal distribution (e.g. intensities)
    :return: Dict: median, low (5th percentile), high (95th percentile),
             sensitivity {parameter: (EF at low end, EF at high end)}
    """
    rng = np.random.default_rng(seed)
    sample = {key: np.full(draws, float(value)) for key, value in parameters.items()}
    for key, (low, high) in ranges.items():
        sample[key] = rng.uniform(low, high, draws)
    for key, sd in relative_sd.items():
        sample[key] = parameters[key] * np.clip(rng.normal(1, sd, draws), 0.05, None)
    values = ef_from_parameters(sample)

    sensitivity = {}
    for key, (low, high) in ranges.items():
        sensitivity[key] = (ef_from_parameters({**parameters, key: low}), ef_from_parameters({**parameters, key: high}))
    for key, sd in relative_sd.items():
        sensitivity[key] = (ef_from_parameters({**parameters, key: parameters[key] * (1 - sd)}),
                            ef_from_parameters({**parameters, key: parameters[key] * (1 + sd)}))

    low, median, high = np.percentile(values, [5, 50, 95])
    return {'median': median, 'low': low, 'high': high, 'sensitivity': sensitivity}


def analytical_ef(i_sers, c_sers, i_raman, c_raman):
    """
    Analytical enhancement factor: AEF = (I_SERS / c_SERS) / (I_Raman / c_Raman)
    c_SERS, c_Raman - analyte concentrations in the SERS and in the normal Raman measurement (same units)
    """
    return (i_sers / c_sers) / (i_raman / c_raman)
