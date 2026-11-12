import pandas as pd

from constants import LABELS
from . import utils


def read_renishaw(uploaded_files, delim):
    """
    Reads two-column spectra (Raman Shift, Intensity) and merges them into one DataFrame.
    Used for Renishaw, Jobin Yvon and Teledyne files.
    :param uploaded_files: List of file-like objects
    :param delim: Str, column separator
    :return: DataFrame, Raman Shift as index, one column per file
    """
    spectra_params_uploaded = {'sep': delim, 'decimal': '.', 'skipinitialspace': True,
                               'header': None}

    frames = []
    for uploaded_file in uploaded_files:
        data = utils.read_spec(uploaded_file, spectra_params_uploaded)
        data = data.iloc[:, :2]
        data.columns = [LABELS["RS"], uploaded_file.name[:-4]]

        # comma used as decimal separator
        data = data.apply(lambda col: pd.to_numeric(col.astype(str).str.replace(',', '.'), errors='coerce'))
        data.dropna(inplace=True, how='any', axis=0)
        data.set_index(LABELS["RS"], inplace=True)

        frames.append(data)

    return utils.align_spectra(frames)
