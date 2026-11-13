"""
PDF reports. Charts are drawn with matplotlib (Plotly image export would need a Chrome browser on the server).
Text uses the DejaVu Sans font shipped with matplotlib - it has Polish letters, Greek letters and superscripts.
"""
import io
import os
from datetime import datetime

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from fpdf import FPDF  # noqa: E402

PALETTE = ['#1C336D', '#6C9BC0', '#DBBD8A', '#B5651D', '#5B8C5A', '#8E6C8A', '#C0504D', '#4BACC6', '#7F7F7F',
           '#2E2E2E']
BLUE, GOLD, NAVY = '#2F6A9B', '#DBBD8A', '#1C336D'
FONT_DIR = os.path.join(matplotlib.get_data_path(), 'fonts', 'ttf')
LOGO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logos',
                    'sersitivis_no_background.png')


class Report(FPDF):
    """
    report = Report('RSD', 'Relative Standard Deviation')
    report.heading('Settings'); report.key_values({...}); report.figure(fig); report.table(df)
    pdf_bytes = report.to_bytes()
    """

    def __init__(self, title, footer_text='SERSitiVIS - sersitive.eu'):
        super().__init__(format='A4')
        self.report_title = title
        self.footer_text = footer_text
        self.add_font('DejaVu', '', os.path.join(FONT_DIR, 'DejaVuSans.ttf'))
        self.add_font('DejaVu', 'B', os.path.join(FONT_DIR, 'DejaVuSans-Bold.ttf'))
        self.set_auto_page_break(True, margin=18)
        self.set_margins(15, 15, 15)
        self.add_page()

    def header(self):
        if os.path.exists(LOGO):
            self.image(LOGO, x=15, y=10, h=12)
        self.set_font('DejaVu', '', 9)
        self.set_text_color(110)
        self.set_xy(-75, 12)
        self.cell(60, 5, datetime.now().strftime('%Y-%m-%d %H:%M'), align='R')
        self.set_xy(15, 26)
        self.set_text_color(0)
        if self.page_no() == 1:
            self.set_font('DejaVu', 'B', 17)
            self.cell(0, 10, self.report_title, new_x='LMARGIN', new_y='NEXT')
            self.set_draw_color(*_rgb(GOLD))
            self.set_line_width(0.8)
            self.line(15, self.get_y(), 195, self.get_y())
            self.ln(4)
        else:
            self.ln(2)

    def footer(self):
        self.set_y(-12)
        self.set_font('DejaVu', '', 8)
        self.set_text_color(130)
        self.cell(0, 5, f'{self.footer_text}    {self.page_no()}', align='C')

    # # content
    def heading(self, text):
        self.ln(3)
        self.set_font('DejaVu', 'B', 12)
        self.set_text_color(*_rgb(NAVY))
        self.cell(0, 8, text, new_x='LMARGIN', new_y='NEXT')
        self.set_text_color(0)

    def text(self, text, size=10):
        self.set_font('DejaVu', '', size)
        self.multi_cell(0, 5, text, new_x='LMARGIN', new_y='NEXT', align='L')
        self.ln(1)

    def key_values(self, values, label_width=70):
        """:param values: Dict or list of (label, value)"""
        items = values.items() if isinstance(values, dict) else values
        self.set_font('DejaVu', '', 10)
        value_x = self.l_margin + label_width + 3
        for label, value in items:
            if self.get_y() > self.h - 30:
                self.add_page()
            top = self.get_y()
            # label and value both wrap within their own column, the row is as high as the taller one
            self.set_text_color(90)
            self.multi_cell(label_width, 6, str(label), align='L', new_x='LMARGIN', new_y='NEXT')
            label_bottom = self.get_y()
            self.set_xy(value_x, top)
            self.set_text_color(0)
            self.multi_cell(0, 6, _format(value), align='L', new_x='LMARGIN', new_y='NEXT')
            self.set_y(max(label_bottom, self.get_y()))
        self.ln(1)

    def table(self, df, index=True, max_rows=60):
        """Simple table, numbers formatted to 4 significant digits"""
        df = df.head(max_rows)
        if index:
            df = df.rename_axis(df.index.name or '').reset_index()
        columns = [str(c) for c in df.columns]
        width = (self.w - self.l_margin - self.r_margin) / len(columns)
        if self.get_y() + 7 + 6 * min(len(df), 3) > self.h - 20:  # keep the header with the first rows
            self.add_page()
        self.set_font('DejaVu', 'B', 9)
        self.set_fill_color(*_rgb('#E4E9EF'))
        for column in columns:
            self.cell(width, 7, _shorten(column, width), border=1, fill=True)
        self.ln()
        self.set_font('DejaVu', '', 9)
        for _, row in df.iterrows():
            if self.get_y() > self.h - 25:
                self.add_page()
            for value in row:
                self.cell(width, 6, _shorten(_format(value), width), border=1)
            self.ln()
        self.ln(2)

    def figure(self, fig, width=180):
        """Adds a matplotlib figure (and closes it)"""
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=200, bbox_inches='tight')
        plt.close(fig)
        buffer.seek(0)
        height = width * fig.get_figheight() / fig.get_figwidth()
        if self.get_y() + height > self.h - 20:
            self.add_page()
        self.image(buffer, x=(self.w - width) / 2, w=width)
        self.ln(2)

    def to_bytes(self):
        return bytes(self.output())


# # charts
def _axes(figsize=(9, 4.2)):
    fig, ax = plt.subplots(figsize=figsize)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    ax.grid(axis='y', color='#e5e5e5')
    return fig, ax


def spectra_figure(df, xlabel='Raman Shift [cm⁻¹]', ylabel='Intensity [a.u.]', ranges=None, title=None,
                   legend=True):
    """
    :param df: DataFrame, index = x, one column per line
    :param ranges: list of (low, high, colour) shaded ranges
    """
    fig, ax = _axes()
    for i, col in enumerate(df.columns):
        ax.plot(df.index, df[col], color=PALETTE[i % len(PALETTE)], linewidth=1.2, label=str(col))
    for low, high, color in ranges or []:
        ax.axvspan(low, high, color=color, alpha=0.25, linewidth=0)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title, fontsize=11)
    if legend and 1 < df.shape[1] <= 12:
        ax.legend(fontsize=7, frameon=False, loc='best')
    return fig


def scatter_figure(x, y, xlabel, ylabel, groups=None, line=None, errors=None, log_x=False):
    """
    :param groups: labels for colouring points
    :param line: (x, y) of a fitted line
    :param errors: (x, y, yerr) of points with error bars
    """
    fig, ax = _axes((7, 4.5))
    if groups is None:
        ax.scatter(x, y, color=PALETTE[1], s=25, alpha=0.7)
    else:
        for i, group in enumerate(pd.unique(pd.Series(groups))):
            mask = np.asarray(groups) == group
            ax.scatter(np.asarray(x)[mask], np.asarray(y)[mask], color=PALETTE[i % len(PALETTE)], s=35,
                       label=str(group))
        ax.legend(fontsize=8, frameon=False)
    if errors is not None:
        ax.errorbar(*errors[:2], yerr=errors[2], fmt='o', color=PALETTE[0], capsize=4, markersize=6)
    if line is not None:
        ax.plot(*line, color=GOLD, linewidth=2)
    if log_x:
        ax.set_xscale('log')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    return fig


def heatmap_figure(image, label):
    """:param image: DataFrame (index = y, columns = x)"""
    fig, ax = plt.subplots(figsize=(6.5, 5))
    extent = [image.columns.min(), image.columns.max(), image.index.min(), image.index.max()]
    shown = ax.imshow(image.to_numpy(), origin='lower', cmap='viridis', aspect='equal',
                      extent=extent if image.shape[0] > 1 and image.shape[1] > 1 else None)
    fig.colorbar(shown, ax=ax, label=label)
    ax.set_xlabel('X [µm]')
    ax.set_ylabel('Y [µm]')
    return fig


def histogram_figure(values, label):
    fig, ax = _axes((6, 3))
    ax.hist(values.dropna(), bins=min(30, max(5, len(values) // 3)), color=PALETTE[1], edgecolor='white')
    ax.set_xlabel(label)
    return fig


def range_figure(ranges, nominal, xlabel):
    """Sensitivity ('tornado') chart: {name: (low, high)}, log x axis"""
    fig, ax = _axes((7, 0.6 + 0.5 * len(ranges)))
    for i, (name, (a, b)) in enumerate(ranges.items()):
        ax.plot([a, b], [i, i], color=PALETTE[1], linewidth=10, solid_capstyle='butt')
    ax.axvline(nominal, color=GOLD, linestyle='--')
    ax.set_yticks(range(len(ranges)), list(ranges))
    ax.set_xscale('log')
    ax.set_xlabel(xlabel)
    ax.grid(axis='x', color='#e5e5e5')
    return fig


# # helpers
def _rgb(color):
    color = color.lstrip('#')
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def _format(value):
    if isinstance(value, (float, np.floating)):
        if not np.isfinite(value):
            return '—'
        if value != 0 and (abs(value) >= 1e5 or abs(value) < 1e-3):
            return f'{value:.3e}'
        return f'{value:.4g}'
    return str(value)


def _shorten(text, width_mm, char_mm=1.9):
    limit = max(4, int(width_mm / char_mm))
    return text if len(text) <= limit else text[:limit - 1] + '…'
