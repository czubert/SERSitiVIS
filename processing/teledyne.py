from . import renishaw


def read_teledyne(uploaded_files, separator):
    """
    Teledyne Princeton Instruments files have the same two-column layout as Renishaw ones
    :param uploaded_files: List of file-like objects
    :param separator: Str, column separator
    :return: DataFrame
    """
    return renishaw.read_renishaw(uploaded_files, separator)
