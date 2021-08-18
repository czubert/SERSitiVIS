import streamlit

from processing import bwtek, renishaw, witec, wasatch, teledyne, spc


def read_files(spectrometer, files, delim):
    if spectrometer == "EMPTY":
        streamlit.warning('Choose spectra type first')
        streamlit.stop()
    
    elif spectrometer == "spc":
        df = spc.local_read_spc(files)
    
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
