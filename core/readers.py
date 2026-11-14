"""
Reading spectra files exported by different Raman spectrometers.

Pure Python/pandas - no Streamlit here, so it can be tested and reused.
Every reader returns a DataFrame: index = Raman Shift [cm-1] (float, ascending), one column per spectrum.
"""
import os
import re
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from core import binary_formats, maps
from core.processing import align_spectra

RAMAN_SHIFT = 'Raman Shift'

# Formats a user can choose manually (normally detected automatically). Renishaw, WITec, Jobin Yvon,
# Teledyne and most other software export a plain text table, so they share one reader.
FORMATS = {
    'AUTO': 'Auto-detect',
    'BWTEK': 'BWTEK',
    'WASATCH': 'Wasatch (ENLIGHTEN)',
    'TABLE': 'Text table (Renishaw, WITec, Jobin Yvon, Teledyne, other)',
    'MAP': 'Map (X, Y, Raman Shift, Intensity)',
    'WDF': 'Renishaw WiRE (*.wdf)',
    'SPC': 'Galactic / Thermo (*.spc)',
    'JCAMP': 'JCAMP-DX (*.jdx, *.dx)',
}

# BWTEK: pixels below this are cut off by the instrument's edge filter (~490 cm-1 and lower)
BWTEK_FIRST_PIXEL = 311
# Saturated detector: the top of the strongest peak is cut off, so its height (and EF, calibration...) is too low.
# BWTEK files keep the raw counts of a 16-bit detector (max 65 535), e.g. 64 380 + 1 114 dark = 65 494.
# Other formats: a clipped peak - the maximum repeated on several neighbouring points.
SATURATION_COUNTS = 0.99 * 65535
FLAT_TOP_POINTS = 3

ENCODINGS = ('utf-8-sig', 'cp1250', 'latin-1')


class ParseError(Exception):
    """File could not be read as a spectrum"""


@dataclass
class LoadedFile:
    name: str
    format: str
    data: pd.DataFrame
    saturated: list = field(default_factory=list)  # spectra whose detector was saturated


def flat_top(y, points=FLAT_TOP_POINTS):
    """The maximum repeated on >= points neighbouring points - a clipped (saturated) peak"""
    y = np.asarray(y, dtype=float)
    y = y[np.isfinite(y)]
    if len(y) < points or y.max() <= 0:
        return False
    run = longest = 0
    for at_max in y == y.max():
        run = run + 1 if at_max else 0
        longest = max(longest, run)
    return longest >= points


def decode(raw):
    """
    Bytes -> str. Software running on Polish Windows often saves files in cp1250, not UTF-8.
    """
    if isinstance(raw, str):
        return raw
    for encoding in ENCODINGS:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue


def stem(file_name):
    return os.path.splitext(os.path.basename(file_name))[0]


#
# # Format detection
#
def detect_format(text):
    """
    Guesses which spectrometer produced the file
    :param text: Str, file content
    :return: Str, key of FORMATS
    """
    head = text[:5000]
    if 'BWSpec' in head or ('Raman Shift' in head and 'Dark Subtracted #1' in head):
        return 'BWTEK'
    if 'ENLIGHTEN' in head or re.search(r'^Pixel,Wavelength,Wavenumber', head, re.M):
        return 'WASATCH'
    if _is_wasatch_txt(text):
        return 'WASATCH'
    return 'TABLE'


def _is_wasatch_txt(text):
    """Wasatch *.txt export: 'pixel wavelength wavenumber processed raw' - pixel numbers 0, 1, 2..."""
    lines = [line.split() for line in text.splitlines()[:5] if line.strip()]
    if len(lines) < 3 or any(len(fields) != 5 for fields in lines):
        return False
    return [fields[0] for fields in lines] == [str(i) for i in range(len(lines))]


#
# # Reading
#
def read_file(name, raw, file_format='AUTO'):
    """
    Reads one file
    :param name: Str, file name (used as spectrum name)
    :param raw: bytes or str, file content
    :param file_format: Str, key of FORMATS
    :return: LoadedFile
    """
    if not raw:
        raise ParseError('File is empty')

    # binary / special formats first - they must not be decoded as text
    if file_format == 'AUTO':
        file_format = binary_formats.detect(name, raw) or 'AUTO'
    if file_format in ('WDF', 'SPC', 'JCAMP'):
        reader = {'WDF': binary_formats.read_wdf, 'SPC': binary_formats.read_spc,
                  'JCAMP': binary_formats.read_jcamp}[file_format]
        try:
            df = reader(name, raw if isinstance(raw, bytes) else raw.encode('latin-1'))
        except binary_formats.BinaryParseError as e:
            raise ParseError(str(e))
        if file_format == 'WDF' and maps.coordinates_from_names(df.columns) is not None:
            file_format = 'MAP'
        return _finish(name, file_format, df)

    text = decode(raw)
    if not text or not text.strip():
        raise ParseError('File is empty')

    if file_format == 'AUTO':
        file_format = detect_format(text)

    saturated = []
    if file_format == 'BWTEK':
        df, raw_max = read_bwtek(name, text)
        saturated = list(df.columns) if raw_max >= SATURATION_COUNTS else []
    elif file_format == 'WASATCH':
        df = read_wasatch(name, text)
    elif file_format in ('TABLE', 'MAP'):
        df = read_table(name, text)
        if maps.coordinates_from_names(df.columns) is not None:
            file_format = 'MAP'
    else:
        raise ValueError(f'Unknown format: {file_format}')
    return _finish(name, file_format, df, saturated)


def _finish(name, file_format, df, saturated=()):
    df = df[~df.index.duplicated()].sort_index().astype(float)
    df = df[np.isfinite(df.index)]
    df.index.name = RAMAN_SHIFT
    if df.empty:
        raise ParseError('No spectrum found in the file')
    saturated = [c for c in df.columns if c in saturated or flat_top(df[c])]
    return LoadedFile(name=name, format=file_format, data=df, saturated=saturated)


def read_files(files, file_format='AUTO'):
    """
    Reads several files and merges them into one DataFrame (common Raman Shift axis).
    :param files: Iterable of (name, raw content) tuples
    :param file_format: Str, key of FORMATS
    :return: (DataFrame or None, list of LoadedFile, dict {file name: error message})
    """
    loaded, errors = [], {}
    for name, raw in files:
        try:
            loaded.append(read_file(name, raw, file_format))
        except ParseError as e:
            errors[name] = str(e)
        except Exception as e:  # unexpected file layout
            errors[name] = 'Could not read the file'

    if not loaded:
        return None, loaded, errors

    frames = unique_column_names([f.data for f in loaded])
    return align_spectra(frames).rename_axis(RAMAN_SHIFT), loaded, errors


def unique_column_names(frames):
    """Two files with the same name (or the same column names) must not overwrite each other"""
    seen = {}
    result = []
    for frame in frames:
        columns = []
        for col in frame.columns:
            count = seen.get(col, 0)
            seen[col] = count + 1
            columns.append(col if count == 0 else f'{col} ({count + 1})')
        result.append(frame.set_axis(columns, axis=1))
    return result


def _to_float(values, decimal_comma):
    values = pd.Series(values, dtype=str).str.strip()
    if decimal_comma:
        values = values.str.replace(',', '.', regex=False)
    return pd.to_numeric(values, errors='coerce')


def read_bwtek(name, text):
    """:return: (DataFrame, highest raw detector count - to detect saturation)"""
    lines = text.splitlines()
    try:
        header_row = next(i for i, line in enumerate(lines) if 'Raman Shift' in line and 'Pixel' in line)
    except StopIteration:
        raise ParseError('BWTEK data header (Pixel; ... Raman Shift ...) not found')

    header = [h.strip() for h in lines[header_row].split(';')]
    rows = [line.split(';') for line in lines[header_row + 1:] if line.strip()]
    rows = [row + [''] * (len(header) - len(row)) for row in rows]
    table = pd.DataFrame([row[:len(header)] for row in rows], columns=header)

    y_column = 'Dark Subtracted #1' if 'Dark Subtracted #1' in header else 'Raw data #1'
    pixel = _to_float(table['Pixel'], decimal_comma=True)
    data = pd.DataFrame({RAMAN_SHIFT: _to_float(table['Raman Shift'], decimal_comma=True),
                         stem(name): _to_float(table[y_column], decimal_comma=True)})
    used = (pixel >= BWTEK_FIRST_PIXEL).to_numpy()
    raw = _to_float(table['Raw data #1'], decimal_comma=True)[used] if 'Raw data #1' in header else data[stem(name)]
    data = data[used].dropna()
    return data.set_index(RAMAN_SHIFT), float(raw.max())


def read_wasatch(name, text):
    if 'ENLIGHTEN' in text[:5000] or re.search(r'^Pixel,Wavelength,Wavenumber', text, re.M):
        lines = text.splitlines()
        header_row = next((i for i, line in enumerate(lines) if line.startswith('Pixel,')), None)
        if header_row is None:
            raise ParseError('Wasatch data header (Pixel,Wavelength,Wavenumber...) not found')
        header = lines[header_row].split(',')
        rows = [line.split(',') for line in lines[header_row + 1:] if line.strip()]
        table = pd.DataFrame([row[:len(header)] for row in rows], columns=header)
        x, y = table['Wavenumber'], table['Raw']
    else:
        table = _numeric_table(text)
        if table.shape[1] < 5:
            raise ParseError('Expected 5 columns: pixel, wavelength, wavenumber, processed, raw')
        x, y = table[2], table[4]

    # Wasatch software adds a timestamp/serial suffix, e.g. 'sample-20201009-093705-137238-WP-00702'
    spectrum_name = re.sub(r'-\d{8}-\d{6}-\d+-WP-\d+$', '', stem(name))
    data = pd.DataFrame({RAMAN_SHIFT: _to_float(x, decimal_comma=False),
                         spectrum_name: _to_float(y, decimal_comma=False)}).dropna()
    return data.set_index(RAMAN_SHIFT)


def read_table(name, text):
    """
    Plain text table: Raman Shift column followed by intensity columns, optional header row.
    Renishaw, WITec, Jobin Yvon, Teledyne and most other software can export it.
    A file may contain several Raman Shift columns (WITec exports one per spectrum) - every intensity
    column uses the nearest Raman Shift column on its left.
    """
    table, header = _numeric_table(text, return_header=True)
    if maps.is_map_table(table):
        return maps.map_to_spectra(table)
    if table.shape[1] < 2:
        raise ParseError('Expected at least two columns: Raman Shift and intensity')

    first_x = table.iloc[:, 0]
    x_column = table.columns[0]
    spectra = []  # (x column, y column)
    for col in table.columns[1:]:
        if table[col].isna().all():
            continue
        if _looks_like_raman_shift(table[col], first_x):
            x_column = col
        else:
            spectra.append((x_column, col))

    if not spectra:
        raise ParseError('No intensity column found')

    frames = []
    for i, (x_col, y_col) in enumerate(spectra, start=1):
        if len(spectra) == 1:
            col_name = stem(name)
        else:
            label = header[y_col] if header and header[y_col] else str(i)
            col_name = f'{stem(name)} ({label})'
        frame = pd.DataFrame({col_name: table[y_col].to_numpy()}, index=table[x_col].to_numpy())
        frame = frame[frame.index.notna()].dropna()
        frames.append(frame)

    return align_spectra(unique_column_names(frames))


def _looks_like_raman_shift(values, first_x):
    """Monotonic column with values close to the first (Raman Shift) column"""
    values = values.dropna()
    if not (values.is_monotonic_increasing or values.is_monotonic_decreasing):
        return False
    span = first_x.max() - first_x.min()
    difference = (values - first_x.loc[values.index]).abs().max()
    return difference <= 0.02 * span


def _numeric_table(text, return_header=False):
    """
    Finds the delimiter and the numeric part of a text table.
    Lines that do not fit (metadata, comments) are skipped. Comma is treated as a decimal separator
    unless it is the column delimiter.
    """
    lines = [line for line in text.splitlines() if line.strip()]
    sample = lines[-50:]

    best = None
    for delimiter in ('	', ';', ',', None):  # None = any whitespace
        fields = [_split(line, delimiter) for line in sample]
        ncols = pd.Series([len(f) for f in fields]).mode().iloc[0]
        if ncols < 2:
            continue
        numeric = sum(len(f) == ncols and _is_numeric_row(f, delimiter != ',') for f in fields)
        if numeric >= 0.8 * len(sample):
            best = delimiter, ncols
            break

    if best is None:
        raise ParseError('Could not find columns with numbers')

    delimiter, ncols = best
    decimal_comma = delimiter != ','
    rows, header = [], None
    for line in lines:
        fields = _split(line, delimiter)
        if len(fields) != ncols:
            continue
        if _is_numeric_row(fields, decimal_comma):
            rows.append(fields)
        elif not rows and any(f.strip() for f in fields):
            header = [f.strip() for f in fields]

    table = pd.DataFrame(rows).apply(lambda col: _to_float(col, decimal_comma))
    if return_header:
        return table, header
    return table


def _split(line, delimiter):
    line = line.strip()
    return line.split() if delimiter is None else line.split(delimiter)


def _is_float(value, decimal_comma):
    if decimal_comma:
        value = value.replace(',', '.')
    try:
        float(value)
        return True
    except ValueError:
        return False


def _is_numeric_row(fields, decimal_comma):
    """At least two values, every non-empty field is a number"""
    values = [f.strip() for f in fields if f.strip()]
    return len(values) >= 2 and all(_is_float(v, decimal_comma) for v in values)
