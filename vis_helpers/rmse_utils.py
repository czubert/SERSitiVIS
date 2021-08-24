import pandas as pd
import streamlit as st
from processing.utils import subtract_baseline


def rsd(peak1, peak2, bg, selection, OneP, P2P):
    if selection == OneP:
        results = rsd_one_peak(peak1)
    
    elif selection == P2P:
        results = rsd_peak_to_peak_ratio(peak1, peak2, bg)
    
    return results

def rsd_one_peak(peak):
    """
    This function takes one particular peak from each spectrum,
    and calculates RMSE basing on values that corresponds to this peak
    :param peak: DataFrame
    :return: Float, RMSE score
    """
    
    st.subheader('RSD directly from data')
    # mean value of absolute numbers
    mean_value = (peak.max()).mean()
    st.write(f' Mean value: {round(mean_value)}')

    # Standard deviation of absolute numbers
    std_value = (peak.max()).std()
    st.write(f' Standard deviation value: {round(std_value)}')

    # Calculating RSD
    rsd = std_value / mean_value
    st.write(f' RSD value: {round(rsd * 100)} %')

    st.subheader('RSD after subtraction of background')

    peak = subtract_baseline(peak, 1)
    # mean value
    mean_value = peak.max().mean()
    st.write(f' Mean value: {round(mean_value)}')

    # Standard deviation of absolute numbers
    std_value = peak.max().std()
    st.write(f' Standard deviation value: {round(std_value)}')

    # Calculating RSD
    rsd = std_value / mean_value
    st.write(f' RSD value: {round(rsd * 100)} %')


def rsd_peak_to_peak_ratio(peak1, peak2, bg):
    """
    This function takes proportions between two peaks from each spectrum,
    and calculates RMSE
    :param peak: DataFrame
    :return: Float, RMSE score
    """
    round_num = 3
    
    # Calculating mean, std and RSD
    mean_value, std_value, rsd = calculate_p2p_rsd(peak1, peak2)
    
    # Baseline correction
    peak1 = subtract_baseline(peak1, 1)
    peak2 = subtract_baseline(peak2, 1)
    
    # Calculating mean, std and RSD after baseline correction
    mean_value_basecorr, std_value_basecorr, rsd_basecorr = calculate_p2p_rsd(peak1, peak2)
    
    results = create_results_df(mean_value, std_value, rsd, round_num, 'RAW data')
    
    results_base_corr = create_results_df(mean_value_basecorr,
                                          std_value_basecorr,
                                          rsd_basecorr,
                                          round_num,
                                          'Baseline corrected',
                                          )
    
    return pd.concat((results, results_base_corr), axis=1)


def calculate_p2p_rsd(peak1, peak2):
    mean_value = (peak1.max() / peak2.max()).mean()
    
    # Standard deviation of absolute numbers
    std_value = (peak1.max() / peak2.max()).std()
    
    # Calculating RSD
    rsd = std_value / mean_value
    
    return mean_value, std_value, rsd


def create_results_df(mean_value, std_value, rsd, round_num, col_name):
    results = {'Mean': round(mean_value, round_num),
               'Standard deviation': round(std_value, round_num),
               'RSD': str(round(rsd * 100)) + ' %'
               }
    
    return pd.DataFrame.from_dict(results, orient='index', columns=[f'{col_name}'])
