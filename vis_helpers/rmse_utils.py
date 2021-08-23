import streamlit as st
from processing.utils import subtract_baseline

P2P = 'Calculate RSD between spectra from "Peak to Peak ratio"'
OneP = 'Calculate RSD between spectra based on "One Peak"'


def rsd(peak1, peak2, bg):
    st.header('Relative Standard Deviation (RSD)')
    
    display_options_radio = st.radio("RSD type:", (OneP, P2P))
    
    if display_options_radio == OneP:
        rsd_one_peak(peak1)
    
    elif display_options_radio == P2P:
        rsd_peak_to_peak_ratio(peak1, peak2, bg)


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
    
    st.subheader('RSD directly from data')
    # mean value of absolute numbers
    mean_value = (peak1.max() / peak2.max()).mean()
    st.write(f' Mean value: {round(mean_value, round_num)}')

    # Standard deviation of absolute numbers
    std_value = (peak1.max() / peak2.max()).std()
    st.write(f' Standard deviation value: {round(std_value, round_num)}')

    # Calculating RSD
    rsd = std_value / mean_value
    st.write(f' RSD value: {round(rsd * 100)} %')

    st.subheader('RSD after subtraction of background')

    # Subtracting the background using peakutils
    peak1 = subtract_baseline(peak1, 1)
    peak2 = subtract_baseline(peak2, 1)

    # Mean
    mean_value = (peak1.max() / peak2.max()).mean()
    st.write(f' Mean value: {round(mean_value, round_num)}')

    # Standard deviation
    std_value = (peak1.max() / peak2.max()).std()
    st.write(f' Standard deviation value: {round(std_value, round_num)}')

    # Calculating RSD
    rsd = std_value / mean_value
    st.write(f' RSD value: {round(rsd * 100)} %')
