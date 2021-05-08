import plotly.express as px

from constants import LABELS
from processing import save_read
from processing import utils
from . import draw


def show_grouped_plot(df, plots_color, template, spectra_conversion_type, shift, vals=None):
    file_name = 'grouped'
    df = df.copy()

    if spectra_conversion_type == LABELS["RAW"]:
        file_name += '_raw'

        for col_ind, col in enumerate(df.columns):
            df[col] = df[col] + shift * col_ind

    elif spectra_conversion_type in {LABELS["OPT"], LABELS["NORM"]}:
        if spectra_conversion_type == LABELS["NORM"]:
            file_name += '_normalized'
            df = (df - df.min()) / (df.max() - df.min())
        else:
            file_name += '_optimized'

        for col_ind, col in enumerate(df.columns):
            if vals is not None:
                df[col] = df[col].rolling(window=vals[col][1], min_periods=1, center=True).mean()
                df[col] = utils.subtract_baseline_series(df[col].dropna(), vals[col][0])

            df[col] += shift * col_ind  # separation

    fig = px.line(df, x=df.index, y=df.columns, color_discrete_sequence=plots_color)
    draw.fig_layout(template, fig, plots_colorscale=plots_color, descr=LABELS["OPT_S"])
    fig.update_traces(line=dict(width=3.5))
    save_read.save_adj_spectra_to_file(df, file_name)

    return fig


