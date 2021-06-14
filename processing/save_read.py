# TODO does this function has any occurance in the code beside this one?
from constants import LABELS
from processing import bwtek, renishaw, witec, wasatch


def read_files(spectrometer, files):
    # BWTek raw spectra
    if spectrometer == LABELS['BWTEK']:
        df, bwtek_metadata = bwtek.read_bwtek(files)

    # Renishaw raw spectra
    elif spectrometer == LABELS['RENI']:
        # TODO I don't get why the same data works differently depending on if it is on the server or uploaded
        try:
            df = renishaw.read_renishaw(files, " ")
        except ValueError:
            df = renishaw.read_renishaw(files, "\t")

    # WITec raw spectra
    elif spectrometer == LABELS['WITEC']:
        df = witec.read_witec(files, ',')

    # WASATCH raw spectra
    elif spectrometer == LABELS['WASATCH']:
        df = wasatch.read_wasatch(files, ',')

    # Teledyne raw spectra
    elif spectrometer == LABELS['TELEDYNE']:
        df = renishaw.read_renishaw(files, ',')

    else:
        raise ValueError('Unknown spectrometer type')

    # fix comma separated decimals (stored as strings)
    for col in df.columns:
        try:
            df.loc[:, col] = df[col].str.replace(',', '.').astype(float)
        except (AttributeError, ValueError):
            ...

    return df
