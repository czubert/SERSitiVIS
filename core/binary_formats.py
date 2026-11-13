"""
Readers for instrument formats that are not plain text tables:
- Renishaw WiRE *.wdf (single spectra, series, line scans and maps - map points keep their coordinates)
- Thermo Galactic *.spc (single and multi-file)
- JCAMP-DX *.jdx / *.dx (XY data)
Every reader returns a DataFrame: index = x axis (Raman Shift), one column per spectrum.
"""
import contextlib
import io
import os
import tempfile

import numpy as np
import pandas as pd

from core import maps

SPC_VERSIONS = (0x4B, 0x4C, 0x4D)  # second byte of a Galactic SPC file


class BinaryParseError(Exception):
    pass


@contextlib.contextmanager
def quiet():
    """The libraries print diagnostic messages - keep the server log clean"""
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        yield


def detect(name, raw):
    """:return: 'WDF', 'SPC', 'JCAMP' or None"""
    if isinstance(raw, bytes) and raw[:4] == b'WDF1':
        return 'WDF'
    extension = os.path.splitext(name)[1].lower()
    if isinstance(raw, bytes) and extension == '.spc' and len(raw) > 512 and raw[1] in SPC_VERSIONS:
        return 'SPC'
    head = raw[:2000].decode('latin-1') if isinstance(raw, bytes) else raw[:2000]
    if '##TITLE' in head.upper() or '##JCAMP' in head.upper():
        return 'JCAMP'
    return None


def _stem(name):
    return os.path.splitext(os.path.basename(name))[0]


def read_wdf(name, raw):
    from renishawWiRE import WDFReader

    # the library reads only from a file on disk
    handle, path = tempfile.mkstemp(suffix='.wdf')
    try:
        with os.fdopen(handle, 'wb') as f:
            f.write(raw)
        with quiet():
            reader = WDFReader(path)
        try:
            x = np.asarray(reader.xdata, dtype=float)
            spectra = np.asarray(reader.spectra, dtype=float).reshape(-1, len(x))
            unit = str(reader.xlist_unit)
            if 'nm' in unit and reader.laser_length:  # wavelength -> Raman Shift
                x = 1e7 / reader.laser_length - 1e7 / x
            measurement = str(reader.measurement_type)
            if measurement == 'Mapping' and getattr(reader, 'xpos', None) is not None and len(reader.xpos) == len(spectra):
                xpos = np.asarray(reader.xpos, dtype=float)
                ypos = np.asarray(reader.ypos, dtype=float)
                xpos, ypos = xpos - xpos.min(), ypos - ypos.min()  # start the map at 0, 0
                names = [maps.NAME.format(x=round(px, 3), y=round(py, 3)) for px, py in zip(xpos, ypos)]
            elif len(spectra) == 1:
                names = [_stem(name)]
            else:
                names = [f'{_stem(name)} ({i})' for i in range(1, len(spectra) + 1)]
        finally:
            reader.close() if hasattr(reader, 'close') else reader.file_obj.close()
    finally:
        os.remove(path)

    df = pd.DataFrame(spectra.T, index=x, columns=names)
    return df.loc[:, ~df.columns.duplicated()]


def read_spc(name, raw):
    import spc_io

    with quiet():
        spc = spc_io.SPC.from_bytes_io(io.BytesIO(raw))
    names = [_stem(name)] if len(spc) == 1 else [f'{_stem(name)} ({i})' for i in range(1, len(spc) + 1)]
    try:  # common x axis for all sub-spectra
        with quiet():
            table = spc.to_dataframe_table()
        return pd.DataFrame(table.to_numpy(dtype=float).T, index=np.asarray(table.columns, dtype=float),
                            columns=names)
    except ValueError:  # every sub-spectrum has its own x axis
        frames = [pd.DataFrame({n: np.asarray(sub.yarray, dtype=float)}, index=np.asarray(sub.xarray, dtype=float))
                  for n, sub in zip(names, spc)]
        if max(len(f) for f in frames) < 5:
            raise BinaryParseError('No spectrum found in the file')
        from core.processing import align_spectra
        return align_spectra(frames)


def read_jcamp(name, raw):
    import jcamp

    text = raw.decode('latin-1') if isinstance(raw, bytes) else raw
    with quiet():  # the library prints checksum messages
        data = jcamp.read(io.StringIO(text))
    if 'x' not in data or 'y' not in data or len(data['x']) < 3:
        raise BinaryParseError('No XY spectrum found in the JCAMP file (peak tables and multi-block files are '
                               'not supported)')
    return pd.DataFrame({_stem(name): np.asarray(data['y'], dtype=float)}, index=np.asarray(data['x'], dtype=float))
