"""Load vs uplift graphs, drawn like the two charts of the uplift test sheet.

Uses the object-oriented ``Figure`` API instead of pyplot so drawing does not
touch matplotlib's global state from Odoo's worker threads.
"""
import io
import math

import numpy as np
from matplotlib.figure import Figure
from matplotlib.ticker import (
    FuncFormatter,
    LogLocator,
    MultipleLocator,
    NullFormatter,
)
from scipy.interpolate import PchipInterpolator

BLUE = '#4F81BD'  # Excel's default series colour, as in the report chart


def parse_loads(value):
    loads = []
    for token in (value or '').replace('\n', ',').split(','):
        token = token.strip()
        if not token:
            continue
        try:
            loads.append(float(token))
        except ValueError:
            continue
    return loads


def _nice_step(span, target):
    raw = span / float(target)
    magnitude = 10 ** math.floor(math.log10(raw))
    for mult in (1, 2, 2.5, 5, 10):
        if mult * magnitude >= raw:
            return mult * magnitude
    return 10 * magnitude


def _split_at_breaks(x, y, breaks):
    """Split a branch after every point whose load matches a break load."""
    if not breaks or len(x) < 2:
        return [(list(x), list(y))]
    segments = []
    start = 0
    for i in range(len(x) - 1):
        if any(abs(x[i] - b) <= 1.0 for b in breaks):
            segments.append((list(x[start:i + 1]), list(y[start:i + 1])))
            start = i + 1
    segments.append((list(x[start:]), list(y[start:])))
    return segments


def _monotonic_runs(points):
    """Split points into runs whose load moves strictly one way.

    A held load (two consecutive points with the same load, e.g. the 24 hour
    hold at test load) becomes its own straight vertical run.
    """
    runs = []
    run = [points[0]]
    for point in points[1:]:
        prev = run[-1]
        if point[0] == prev[0]:
            if len(run) > 1:
                runs.append(run)
            runs.append([prev, point])
            run = [point]
        elif len(run) > 1 and (point[0] - prev[0]) * (prev[0] - run[-2][0]) < 0:
            runs.append(run)
            run = [prev, point]
        else:
            run.append(point)
    if len(run) > 1:
        runs.append(run)
    return runs


def _smooth_paths(x, y):
    """Shape-preserving curve through every measured point, in test order."""
    points = list(zip(x, y))
    if len(points) < 2:
        return [(list(x), list(y))]
    paths = []
    for run in _monotonic_runs(points):
        rx = np.asarray([p[0] for p in run], dtype=float)
        ry = np.asarray([p[1] for p in run], dtype=float)
        if len(run) < 3:
            paths.append((rx, ry))
            continue
        sign = 1.0 if rx[-1] > rx[0] else -1.0
        t = sign * rx
        try:
            interp = PchipInterpolator(t, ry)
        except ValueError:
            paths.append((rx, ry))
            continue
        t_dense = np.linspace(t[0], t[-1], 200)
        paths.append((sign * t_dense, interp(t_dense)))
    return paths


def _png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, facecolor='white')
    return buf.getvalue()


def render_load_uplift_graph(loading, unloading, load_breaks=None, unload_breaks=None):
    """"LOAD Vs SETTLEMENT CURVE" of the report: load on the top axis, uplift
    (settlement) on the reversed left axis, smoothed, with diamond markers.

    ``loading`` / ``unloading`` are lists of (load MT, cumulative uplift mm).
    """
    load_x = [0.0] + [p[0] for p in loading]
    load_y = [0.0] + [p[1] for p in loading]
    if unloading:
        unload_x = [load_x[-1]] + [p[0] for p in unloading]
        unload_y = [load_y[-1]] + [p[1] for p in unloading]
    else:
        unload_x, unload_y = [], []

    fig = Figure(figsize=(7.5, 5.5))
    fig.patch.set_facecolor('white')
    ax = fig.subplots()
    ax.set_facecolor('white')

    for bx, by, breaks in ((load_x, load_y, load_breaks),
                           (unload_x, unload_y, unload_breaks)):
        if not bx:
            continue
        for seg_x, seg_y in _split_at_breaks(bx, by, breaks):
            for px, py in _smooth_paths(seg_x, seg_y):
                ax.plot(px, py, color=BLUE, linewidth=2.2, zorder=2)
        ax.scatter(bx, by, color=BLUE, s=36, marker='D', zorder=5)

    # Ticks and labels along the top, axis title at the bottom, as in Excel.
    ax.xaxis.tick_top()
    ax.tick_params(axis='x', which='both', bottom=False, top=True,
                   direction='in', length=4)
    ax.tick_params(axis='x', which='major', length=6)
    ax.tick_params(axis='y', which='both', direction='out', length=4)
    serif = 'serif'
    ax.set_xlabel('Load in  MT', fontsize=11, fontfamily=serif, labelpad=8)
    ax.set_ylabel('Settlement, mm', fontsize=11, fontfamily=serif, labelpad=8)
    ax.set_title('LOAD  Vs SETTLEMENT  CURVE', fontsize=13, fontweight='bold',
                 fontfamily=serif, pad=12)

    for spine in ax.spines.values():
        spine.set_linewidth(0.8)
        spine.set_color('#000000')

    # Axis runs to the next 10 MT above the peak (150 for 140.13) with labels
    # every 20 MT, like the report's chart.
    x_peak = max(load_x + unload_x) or 10.0
    x_top = math.ceil(x_peak * 1.05 / 10.0) * 10.0
    x_step = _nice_step(x_top, 8)
    ax.set_xlim(0, x_top)
    ax.xaxis.set_major_locator(MultipleLocator(x_step))
    ax.xaxis.set_minor_locator(MultipleLocator(x_step / 4))

    y_peak = max(load_y + unload_y) or 1.0
    y_step = _nice_step(y_peak * 1.1, 10)
    y_top = math.ceil(y_peak * 1.1 / y_step) * y_step
    ax.set_ylim(0, y_top)
    ax.invert_yaxis()
    ax.yaxis.set_major_locator(MultipleLocator(y_step))

    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _pos: f'{v:.1f}'))
    ax.grid(False)
    fig.tight_layout()
    return _png(fig)


def render_log_graph(points, load_breaks=None, unload_breaks=None):
    """Log-log uplift (x) vs load (y), straight lines in test order.

    ``points`` is a list of (cumulative uplift mm, load MT, stage). A log axis
    cannot show zero or negative values, so those points are skipped.
    Returns None when nothing can be drawn.
    """
    points = [p for p in points if p[0] > 0 and p[1] > 0]
    if not points:
        return None

    segments = []
    start = 0
    for i in range(len(points) - 1):
        _, load_val, stage = points[i]
        breaks = load_breaks if stage == 'loading' else unload_breaks
        if breaks and any(abs(load_val - b) <= 1.0 for b in breaks):
            segments.append(points[start:i + 1])
            start = i + 1
    segments.append(points[start:])

    x_vals = [p[0] for p in points]
    y_vals = [p[1] for p in points]

    fig = Figure(figsize=(7.5, 5.5))
    fig.patch.set_facecolor('white')
    ax = fig.subplots()
    ax.set_facecolor('white')

    for seg in segments:
        ax.plot([p[0] for p in seg], [p[1] for p in seg], color='#1f4e9c',
                linewidth=1.8, marker='D', markersize=6,
                markerfacecolor='#1f4e9c', markeredgecolor='#1f4e9c', zorder=3)

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.xaxis.set_major_locator(LogLocator(base=10.0, numticks=15))
    ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs=tuple(range(2, 10)), numticks=15))
    ax.yaxis.set_major_locator(LogLocator(base=10.0, numticks=15))
    ax.yaxis.set_minor_locator(LogLocator(base=10.0, subs=tuple(range(2, 10)), numticks=15))

    def _plain_log_label(value, _pos):
        return '' if value <= 0 else f'{value:g}'

    ax.xaxis.set_major_formatter(FuncFormatter(_plain_log_label))
    ax.yaxis.set_major_formatter(FuncFormatter(_plain_log_label))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.yaxis.set_minor_formatter(NullFormatter())

    def _log_floor(value):
        return 10.0 ** math.floor(math.log10(value))

    def _log_ceil(value):
        return 10.0 ** math.ceil(math.log10(value))

    ax.set_xlim(min(0.1, _log_floor(min(x_vals))), max(10.0, _log_ceil(max(x_vals))))
    ax.set_ylim(min(1.0, _log_floor(min(y_vals))), max(1000.0, _log_ceil(max(y_vals))))

    serif = 'serif'
    ax.set_title('LOAD UPLIFT CURVE', fontsize=13, fontweight='bold',
                 fontfamily=serif, pad=14)
    ax.set_xlabel('Uplift in mm', fontsize=11, fontfamily=serif, labelpad=8)
    ax.set_ylabel('Load in MT', fontsize=11, fontfamily=serif, labelpad=8)
    ax.tick_params(axis='both', which='major', length=6, width=0.9,
                   color='black', labelcolor='black')
    ax.tick_params(axis='both', which='minor', length=3, width=0.7, color='black')
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontfamily(serif)
        label.set_fontsize(9)
    for spine in ax.spines.values():
        spine.set_color('black')
        spine.set_linewidth(1.0)
    ax.grid(False)

    fig.tight_layout()
    return _png(fig)
