import streamlit as st


def trim_spectra(df):
    # trim raman shift range
    min_, max_ = float(df.index.min()), float(df.index.max())
    min_rs, max_rs = st.slider('custom range',
                               min_value=min_, max_value=max_, value=[min_, max_])
    mask = (min_rs <= df.index) & (df.index <= max_rs)
    return df[mask]
