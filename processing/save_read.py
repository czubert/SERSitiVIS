import io

import streamlit
import streamlit as st
from detect_delimiter import detect

from processing import bwtek, renishaw, witec, wasatch, teledyne


def read_files(spectrometer, files, delim):
    if spectrometer == "EMPTY":
        streamlit.warning('Choose spectra type first')
        streamlit.stop()
    
    # BWTek raw spectra
    elif spectrometer == 'BWTEK':
        df, bwtek_metadata = bwtek.read_bwtek(files, delim)
    
    # Renishaw raw spectra
    elif spectrometer == 'RENI':
        df = renishaw.read_renishaw(files, delim)
    
    # WITec raw spectra
    elif spectrometer == 'WITEC':
        df = witec.read_witec(files, delim)
    
    # WASATCH raw spectra
    elif spectrometer == 'WASATCH':
        df = wasatch.read_wasatch(files, delim)

    # Teledyne raw spectra
    elif spectrometer == 'TELEDYNE':
        df = teledyne.read_teledyne(files, delim)

    # Renishaw raw spectra
    elif spectrometer == 'JOBIN':
        df = renishaw.read_renishaw(files, delim)

    else:
        raise ValueError('Unknown spectrometer type')
    
    # fix comma separated decimals (stored as strings)
    if spectrometer != "None":
        for col in df.columns:
            try:
                df.loc[:, col] = df[col].str.replace(',', '.').astype(float)
            except (AttributeError, ValueError):
                ...
    
    return df


def files_to_df(files, spectrometer):
    new_files = []
    delim = None

    for file in files:
        file.seek(0)
        lines = file.readlines()

        try:
            lines = [line.decode('utf-8') for line in lines]
        except AttributeError:
            pass

        first_lines = '\n'.join(lines[:20])
        delim = detect(first_lines)
        colnum = lines[-2].count(delim)

        lines = [i for i in lines if i.count(delim) == colnum]
        text = '\n'.join(lines)
        buffer = io.StringIO(text)
        buffer.name = file.name
        new_files.append(buffer)

    try:
        df = read_files(spectrometer, new_files, delim)
        return df

    except (TypeError, ValueError):
        st.error('Try choosing another type of spectra')
        st.stop()

