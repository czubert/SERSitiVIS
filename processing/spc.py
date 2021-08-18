import pandas as pd

from pyspectra.readers.read_spc import read_spc
from pyspectra.readers.read_spc import read_spc_dir


def local_read_spc(files):
    if len(files) == 1:
        # read_spc returns array, therefore for our needs we need to make a df out of it
        df_spc = pd.DataFrame(read_spc('data/data_examples/a/a.spc'))
    else:
        # returns DataFrame and dict with filenames as keys and Series as values
        df_spc, dict_spc = read_spc_dir('data/data_examples/a')
        df_spc = df_spc.T
    
    return df_spc
