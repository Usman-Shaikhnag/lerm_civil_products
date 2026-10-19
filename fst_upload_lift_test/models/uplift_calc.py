"""Uplift load test calculations.

Mirrors the "Welspun Uplift Load Test" sheet:

    Load (MT)                  = pressure gauge (kg/cm2) x jack area (cm2) / 1000
    Cumulative dial reading    = dial A + dial B
    Average uplift of a stage  = (last cumulative - first cumulative) / 2
    Cumulative uplift          = running total of the stage averages; the
                                 unloading stages continue from the loading total
    Total uplift               = cumulative uplift at the end of loading
    Net uplift                 = cumulative uplift after the last unloading stage
    Rebound                    = total uplift - net uplift

Values are computed with the same floating point steps as the sheet and shown
to 2 decimals the way Excel displays them (see ``excel_round``), e.g. a stage
average of -0.04499999999999993 shows as -0.04, not -0.05.

A stage starts at a reading with a zero reading interval, or at a reading whose
pressure differs from the current stage's pressure. Its first reading carries
the previous stage's last dial values (as in the sheet); readings without any
dial value are treated as not recorded and skipped.

Kept free of Odoo imports so it can be checked outside the server.
"""
from decimal import Decimal, ROUND_HALF_UP

NO_OF_DIAL_GAUGES = 2


def excel_round(value, ndigits=2):
    """Round like an Excel cell formatted with ``ndigits`` decimals.

    Excel first reduces the binary value to 15 significant digits, then
    rounds half away from zero.
    """
    exact = Decimal(format(float(value or 0.0), '.15g'))
    return float(exact.quantize(Decimal(1).scaleb(-ndigits), rounding=ROUND_HALF_UP))


def load_from_pressure(pressure, jack_area):
    return round((pressure or 0.0) * (jack_area or 0.0) / 1000.0, 4)


def cumulative_dial(dial_a, dial_b):
    return round((dial_a or 0.0) + (dial_b or 0.0), 2)


def _dial_sum(reading):
    # Unrounded, as the sheet's "F + G" column feeds the averages.
    return (reading['dial_a'] or 0.0) + (reading['dial_b'] or 0.0)


def is_recorded(reading):
    return bool(reading['dial_a'] or reading['dial_b'])


def group_stages(readings):
    stages = []
    for reading in readings:
        if (not stages
                or reading['interval'] == 0
                or (reading['pressure']
                    and reading['pressure'] != stages[-1][0]['pressure'])):
            stages.append([reading])
        else:
            stages[-1].append(reading)
    return stages


def stage_summary(loading, unloading):
    """Return one row per load stage, loading first then unloading.

    ``loading`` / ``unloading`` are lists of dicts with the keys ``interval``,
    ``pressure``, ``load``, ``dial_a`` and ``dial_b``, in test order.
    ``avg`` / ``cumulative`` are the 2 decimal values the sheet shows;
    ``cumulative_raw`` is the unrounded running total.
    """
    rows = []
    cumulative = 0.0
    prev_last = None
    for load_type, readings in (('loading', loading), ('unloading', unloading)):
        for stage in group_stages(readings):
            head = stage[0]
            if is_recorded(head) or prev_last is None:
                first = _dial_sum(head)
            else:
                first = prev_last
            recorded = [r for r in stage[1:] if is_recorded(r)]
            if recorded:
                last = _dial_sum(recorded[-1])
            else:
                last = first

            avg = (last - first) / NO_OF_DIAL_GAUGES
            cumulative += avg
            prev_last = last
            rows.append({
                'load_type': load_type,
                'load': head['load'],
                'avg': excel_round(avg),
                'cumulative': excel_round(cumulative),
                'cumulative_raw': cumulative,
            })
    return rows


def uplift_totals(rows):
    """Return (total uplift, net uplift, rebound) for ``stage_summary`` rows,
    rounded to 2 decimals as Excel shows them."""
    if not rows:
        return 0.0, 0.0, 0.0
    loading = [r['cumulative_raw'] for r in rows if r['load_type'] == 'loading']
    unloading = [r['cumulative_raw'] for r in rows if r['load_type'] == 'unloading']
    total = loading[-1] if loading else max(r['cumulative_raw'] for r in rows)
    net = unloading[-1] if unloading else total
    return excel_round(total), excel_round(net), excel_round(total - net)
