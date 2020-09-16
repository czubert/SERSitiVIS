import os
import pandas as pd
from joblib import dump, load


# PATH = 'data_output'


def save_as_joblib(data_to_save, file_name, path):
    if not os.path.isdir(f'{path}'):
        os.makedirs(f'{path}')

    dump(data_to_save, f'{path}/{file_name}.joblib')


def read_joblib(file_name, dir_name):
    return load(f'{dir_name}/{file_name}.joblib')


def save_as_csv(data, file_name, dir_name):
    if not os.path.isdir(f'{dir_name}'):
        os.mkdir(f'{dir_name}')

    data.to_csv(f'{dir_name}/{file_name}.csv')


def read_csv(file_name, dir_name):
    return pd.read_csv(f'{dir_name}/{file_name}.csv')
