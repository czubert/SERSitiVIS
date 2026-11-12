import io

import streamlit as st
from detect_delimiter import detect

from processing import bwtek, renishaw, witec, wasatch, teledyne


def read_files(spectrometer, files, delim):
    if spectrometer == "EMPTY":
        st.warning('Choose spectra type first')
        st.stop()
    
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
    for col in df.columns:
        if df[col].dtype == object:
            try:
                df[col] = df[col].str.replace(',', '.').astype(float)
            except (AttributeError, ValueError):
                ...
    
    return df


def decode_line(line):
    """
    Decodes a line read from an uploaded (binary) file. Files exported by software running on
    Polish Windows are often not UTF-8 (e.g. cp1250), so fall back to other encodings.
    """
    if isinstance(line, str):
        return line
    for encoding in ('utf-8', 'cp1250', 'latin-1'):
        try:
            return line.decode(encoding)
        except UnicodeDecodeError:
            continue


def files_to_df(files, spectrometer):
    new_files = []
    delim = None

    for file in files:
        file.seek(0)
        lines = file.readlines()

        lines = [decode_line(line) for line in lines]

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

