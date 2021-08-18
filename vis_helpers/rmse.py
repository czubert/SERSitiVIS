import streamlit as st
import pandas as pd
import numpy as np

P2P = 'Calculate RSD between spectra from "Peak to Peak ratio"'
OneP = 'Calculate RSD between spectra based on "One Peak"'


def rsd(peak1, peak2, bg):
    st.header('Relative Standard Deviation (RSD):')
    
    display_options_radio = st.radio("What would you like to do?", (OneP, P2P))
    
    if display_options_radio == OneP:
        rsd_one_peak(peak1)
    
    elif display_options_radio == P2P:
        rsd_peak_to_peak_ratio(peak1, peak2, bg)


def rsd_one_peak(peak):
    # WHAT which version is better?
    
    # II
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
    
    # I
    st.subheader('RSD after subtraction of background')
    # mean value of absolute numbers
    mean_value = (peak.max() - peak.min()).mean()
    st.write(f' Mean value: {round(mean_value)}')
    
    # Standard deviation of absolute numbers
    std_value = (peak.max() - peak.min()).std()
    st.write(f' Standard deviation value: {round(std_value)}')
    
    # Calculating RSD
    rsd = std_value / mean_value
    st.write(f' RSD value: {round(rsd * 100)} %')


def rsd_peak_to_peak_ratio(peak1, peak2, bg):
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
    
    # # Show DataFrame with data
    # dff = pd.DataFrame(np.array([bg.max(), peak1.max(), peak2.max(), peak1.max() - bg.max(), peak2.max() - bg.max()]),
    #                    index=['Bg max', 'p1 max', 'p2 max', 'p1 obj', 'p2 obj'])
    # dfff = dff.T
    #
    # st.write(dfff)
    
    mean_value = ((peak1.max() - bg.max()) / (peak2.max() - bg.max())).mean()
    st.write(f' Mean value: {round(mean_value, round_num)}')
    
    # Standard deviation of absolute numbers
    std_value = ((peak1.max() - bg.max()) / (peak2.max() - bg.max())).std()
    st.write(f' Standard deviation value: {round(std_value, round_num)}')
    
    # Calculating RSD
    rsd = std_value / mean_value
    st.write(f' RSD value: {round(rsd * 100)} %')

# # Calling the function with parameters
# peak1 = df.loc[680:725, :]
# peak2 = df.loc[990:1010, :]
# bg = df.loc[938:941, :]
#
# rsd(peak1, peak2, bg)
