"""
Raman / SERS maps: reading map files and substrate uniformity statistics.

A map file (e.g. Renishaw WiRE export) has 4 columns: X, Y, Raman Shift, Intensity - one row per point and
wavenumber. Each map point becomes a spectrum named 'x=..; y=..', so maps go through the same pipeline as
other spectra and the coordinates can be read back from the names.
"""
import re

import numpy as np
import pandas as pd

from core.processing import trim

NAME = 'x={x:g}; y={y:g}'
NAME_PATTERN = re.compile(r'x=(-?[\d.e+-]+); y=(-?[\d.e+-]+)$')


def is_map_table(table):
    """
    4 numeric columns: X and Y with few distinct values, Raman Shift repeated for every point
    :param table: DataFrame of numbers (as read from the file)
    """
    if table.shape[1] != 4 or len(table) < 20:
        return False
    points = table.iloc[:, [0, 1]].drop_duplicates()
    if len(points) < 2:
        return False
    per_point = len(table) / len(points)
    return per_point >= 10 and per_point == int(per_point) and table.iloc[:, 2].nunique() <= per_point * 1.01


def map_to_spectra(table):
    """
    :param table: DataFrame with columns X, Y, Raman Shift, Intensity (any names)
    :return: DataFrame, index = Raman Shift, one column per map point named 'x=..; y=..'
    """
    data = table.iloc[:, :4].copy()
    data.columns = ['x', 'y', 'shift', 'intensity']
    data['name'] = [NAME.format(x=x, y=y) for x, y in zip(data['x'], data['y'])]
    order = data[['x', 'y', 'name']].drop_duplicates()
    wide = data.pivot_table(index='shift', columns='name', values='intensity', aggfunc='mean')
    # points ordered by y, then x (rows of the map)
    wide = wide[order.sort_values(['y', 'x'])['name']]
    wide.columns.name = None
    return wide.sort_index()


def coordinates_from_names(names):
    """
    :return: DataFrame (index = names, columns x, y) or None if names are not map points
    """
    coords = {}
    for name in names:
        match = NAME_PATTERN.search(str(name))
        if not match:
            return None
        coords[name] = (float(match.group(1)), float(match.group(2)))
    return pd.DataFrame.from_dict(coords, orient='index', columns=['x', 'y'])


def grid_coordinates(names, columns, step_x=1.0, step_y=1.0, snake=False):
    """
    Coordinates for spectra measured on a regular grid, row by row
    :param names: spectra names in measurement order
    :param columns: number of points in a row
    :param snake: Bool, every second row measured in the opposite direction
    :return: DataFrame (index = names, columns x, y)
    """
    coords = {}
    for i, name in enumerate(names):
        row, col = divmod(i, columns)
        if snake and row % 2:
            col = columns - 1 - col
        coords[name] = (col * step_x, row * step_y)
    return pd.DataFrame.from_dict(coords, orient='index', columns=['x', 'y'])


def uniformity(values):
    """
    Statistics of a map
    :param values: Series, one value per map point
    :return: Dict
    """
    values = values.dropna()
    mean, sd = values.mean(), values.std()
    return {'n': int(len(values)), 'mean': mean, 'sd': sd, 'rsd': 100 * sd / mean if mean else np.nan,
            'min': values.min(), 'max': values.max(),
            'within_20': 100 * float((abs(values - mean) <= 0.2 * abs(mean)).mean())}


def grid(values, coords):
    """
    Values arranged as an image for a heatmap
    :return: DataFrame (index = y, columns = x)
    """
    data = coords.assign(value=values.reindex(coords.index))
    return data.pivot_table(index='y', columns='x', values='value', aggfunc='mean').sort_index()
