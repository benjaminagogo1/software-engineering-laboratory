"""
Renders the monthly spending chart as one self-contained HTML file.

Deliberately dependency-free: the chart is hand-authored SVG in a string, so
showing a graph costs the project nothing — no matplotlib in requirements.txt,
no CDN, no JavaScript. The file opens in any browser and works offline.

Design decisions worth knowing before editing the markup:

* One series (amount spent per day), so there is no legend — the title says
  what is plotted. Colour comes from a single validated hue.
* Bars are capped at 24px with a rounded top and a square base, and always
  keep at least a 2px gap of surface between them.
* Only the busiest day is labelled directly. Every other value is reachable
  from the axis and the table view below the chart.
* Values live in three places — hover text, the table, and the peak label — so
  nothing is gated behind a tooltip.
"""

import calendar
import html
import math
from pathlib import Path

from app.ui.formatting import CURRENCY_SYMBOL, format_money, format_money_tick


VIEW_WIDTH = 960
MARGIN_LEFT = 76
MARGIN_RIGHT = 20
# Enough headroom for the peak label to sit above the tallest bar.
MARGIN_TOP = 26
PLOT_HEIGHT = 260
AXIS_BAND = 32
VIEW_HEIGHT = MARGIN_TOP + PLOT_HEIGHT + AXIS_BAND

BAR_MAX_WIDTH = 24
BAR_GAP = 2
BAR_CORNER_RADIUS = 4
# A one-naira day should still be visible rather than a zero-height sliver.
MIN_BAR_HEIGHT = 2

TARGET_TICKS = 4


# Plain string rather than an f-string: the CSS braces stay readable, and the
# light/dark values sit side by side where they can be compared.
STYLESHEET = """
  :root { color-scheme: light dark; }

  .spending-chart {
    color-scheme: light;
    --surface-1: #fcfcfb;
    --page: #f9f9f7;
    --text-primary: #0b0b0b;
    --text-secondary: #52514e;
    --text-muted: #898781;
    --gridline: #e1e0d9;
    --baseline: #c3c2b7;
    --series-1: #2a78d6;
    --border: rgba(11, 11, 11, 0.10);

    background: var(--page);
    color: var(--text-primary);
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    margin: 0;
    padding: 32px 24px;
  }

  @media (prefers-color-scheme: dark) {
    :root:where(:not([data-theme="light"])) .spending-chart {
      color-scheme: dark;
      --surface-1: #1a1a19;
      --page: #0d0d0d;
      --text-primary: #ffffff;
      --text-secondary: #c3c2b7;
      --text-muted: #898781;
      --gridline: #2c2c2a;
      --baseline: #383835;
      --series-1: #3987e5;
      --border: rgba(255, 255, 255, 0.10);
    }
  }

  :root[data-theme="dark"] .spending-chart {
    color-scheme: dark;
    --surface-1: #1a1a19;
    --page: #0d0d0d;
    --text-primary: #ffffff;
    --text-secondary: #c3c2b7;
    --text-muted: #898781;
    --gridline: #2c2c2a;
    --baseline: #383835;
    --series-1: #3987e5;
    --border: rgba(255, 255, 255, 0.10);
  }

  .spending-chart h1 {
    font-size: 20px;
    font-weight: 600;
    margin: 0 0 4px;
  }

  .spending-chart .subtitle {
    color: var(--text-secondary);
    font-size: 13px;
    margin: 0 0 20px;
  }

  .tiles {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 20px;
  }

  .tile {
    background: var(--surface-1);
    border: 1px solid var(--border);
    border-radius: 10px;
    flex: 1 1 180px;
    padding: 14px 16px;
  }

  .tile .label {
    color: var(--text-secondary);
    font-size: 12px;
    margin-bottom: 6px;
  }

  .tile .value {
    font-size: 22px;
    font-weight: 600;
  }

  .tile .value .unit {
    color: var(--text-secondary);
    font-size: 14px;
    font-weight: 400;
  }

  .card {
    background: var(--surface-1);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 8px 4px 4px;
  }

  .card svg { display: block; height: auto; width: 100%; }

  /* Axis text sits on text tokens, never on the series colour. */
  .axis-label {
    fill: var(--text-muted);
    font-size: 11px;
    font-variant-numeric: tabular-nums;
  }

  .peak-label {
    fill: var(--text-primary);
    font-size: 11px;
    font-weight: 600;
  }

  .gridline { stroke: var(--gridline); stroke-width: 1; }
  .baseline { stroke: var(--baseline); stroke-width: 1; }
  .bar { fill: var(--series-1); }

  .empty {
    color: var(--text-secondary);
    padding: 40px 16px;
    text-align: center;
  }

  table {
    border-collapse: collapse;
    font-size: 13px;
    margin-top: 16px;
    width: 100%;
  }

  caption {
    color: var(--text-secondary);
    font-size: 12px;
    padding-bottom: 8px;
    text-align: left;
  }

  th, td {
    border-bottom: 1px solid var(--border);
    padding: 6px 8px;
    text-align: left;
  }

  th { color: var(--text-secondary); font-weight: 500; }

  td.amount, th.amount {
    font-variant-numeric: tabular-nums;
    text-align: right;
  }

  details { margin-top: 16px; }

  summary {
    color: var(--text-secondary);
    cursor: pointer;
    font-size: 13px;
    padding: 4px 0;
  }
"""


def _nice_step(raw):
    """
    Rounds an interval up to the next 1, 2, 2.5 or 5 times a power of ten, so
    axis ticks land on numbers a reader recognises.
    """
    if raw <= 0:
        return 1.0

    magnitude = 10 ** math.floor(math.log10(raw))

    for multiple in (1, 2, 2.5, 5, 10):
        step = multiple * magnitude

        if step >= raw:
            return float(step)

    return float(10 * magnitude)


def _axis_scale(max_total):
    """
    Returns (axis_max, step) for the y axis: the top gridline and the gap
    between them. axis_max is always at or above the largest bar.
    """
    step = _nice_step(max_total / TARGET_TICKS)

    return float(math.ceil(max_total / step) * step), step


def _bar_path(x, y, width, height, radius):
    """
    A bar with a rounded data-end and square corners where it meets the
    baseline: up the left side, across the top with two curves, down the right.
    """
    radius = max(0.0, min(radius, width / 2, height))

    return (
        f"M {x:.2f} {y + height:.2f} "
        f"L {x:.2f} {y + radius:.2f} "
        f"Q {x:.2f} {y:.2f} {x + radius:.2f} {y:.2f} "
        f"L {x + width - radius:.2f} {y:.2f} "
        f"Q {x + width:.2f} {y:.2f} {x + width:.2f} {y + radius:.2f} "
        f"L {x + width:.2f} {y + height:.2f} Z"
    )


def _day_label_days(days_in_month):
    """
    Which day numbers get an x-axis label. Every day would crowd the axis, so
    it is the first, the last, and the round numbers between.
    """
    return {
        day for day in range(1, days_in_month + 1)
        if day == 1 or day == days_in_month or day % 5 == 0
    }


def _render_chart(series, month_label, days_in_month):
    """
    Draws the plot: gridlines, bars, axis labels and the peak label.
    `series` is [(day, amount)] with every day of the month present.
    """
    max_total = max(amount for _, amount in series)
    axis_max, step = _axis_scale(max_total)

    plot_width = VIEW_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
    band = plot_width / days_in_month
    bar_width = min(BAR_MAX_WIDTH, band - BAR_GAP)
    baseline = MARGIN_TOP + PLOT_HEIGHT

    def y_for(amount):
        return MARGIN_TOP + PLOT_HEIGHT - (amount / axis_max) * PLOT_HEIGHT

    parts = []

    # Gridlines first, so the bars sit on top of them.
    tick_count = int(round(axis_max / step))

    for index in range(tick_count + 1):
        value = round(index * step, 2)
        y = y_for(value)
        line_class = "baseline" if index == 0 else "gridline"

        parts.append(
            f'<line class="{line_class}" x1="{MARGIN_LEFT}" y1="{y:.2f}" '
            f'x2="{VIEW_WIDTH - MARGIN_RIGHT}" y2="{y:.2f}" />'
        )
        parts.append(
            f'<text class="axis-label" x="{MARGIN_LEFT - 10}" y="{y + 4:.2f}" '
            f'text-anchor="end">{html.escape(format_money_tick(value))}</text>'
        )

    peak_day, peak_amount = max(series, key=lambda entry: (entry[1], -entry[0]))
    labelled_days = _day_label_days(days_in_month)

    for day, amount in series:
        centre = MARGIN_LEFT + (day - 1) * band + band / 2

        if day in labelled_days:
            parts.append(
                f'<text class="axis-label" x="{centre:.2f}" y="{baseline + 20}" '
                f'text-anchor="middle">{day}</text>'
            )

        if amount <= 0:
            # A day with no spending is a gap, not a zero-height bar.
            continue

        height = max(MIN_BAR_HEIGHT, (amount / axis_max) * PLOT_HEIGHT)
        x = centre - bar_width / 2
        y = baseline - height

        parts.append(
            f'<path class="bar" d="{_bar_path(x, y, bar_width, height, BAR_CORNER_RADIUS)}">'
            f"<title>{html.escape(month_label)} {day}: {html.escape(format_money(amount))}</title>"
            f"</path>"
        )

        if day == peak_day:
            # The one direct label on the chart: the extreme.
            parts.append(
                f'<text class="peak-label" x="{centre:.2f}" y="{y - 8:.2f}" '
                f'text-anchor="middle">{html.escape(format_money(amount))}</text>'
            )

    return (
        f'<svg viewBox="0 0 {VIEW_WIDTH} {VIEW_HEIGHT}" role="img" '
        f'aria-label="{html.escape(month_label)} daily spending, bar chart">'
        f"<title>{html.escape(month_label)} spending by day</title>"
        f"<desc>Total amount spent on each day of {html.escape(month_label)}. "
        f"The busiest day was day {peak_day} at {html.escape(format_money(peak_amount))}.</desc>"
        + "".join(parts)
        + "</svg>"
    )


def _render_table(series, month_label):
    """The table twin: every value in the chart, without needing colour."""
    rows = "".join(
        f"<tr><td>{html.escape(month_label)} {day}</td>"
        f'<td class="amount">{html.escape(format_money(amount))}</td></tr>'
        for day, amount in series
        if amount > 0
    )

    total = sum(amount for _, amount in series)

    return (
        "<details>"
        "<summary>Table view — every day with spending</summary>"
        "<table>"
        f"<caption>Days without spending are omitted; on the chart they are gaps.</caption>"
        "<thead><tr><th>Day</th><th class=\"amount\">Amount</th></tr></thead>"
        f"<tbody>{rows}</tbody>"
        "<tfoot><tr><th>Total</th>"
        f'<th class="amount">{html.escape(format_money(total))}</th></tr></tfoot>'
        "</table>"
        "</details>"
    )


def _render_tiles(series, month_label, days_in_month):
    """The headline numbers, including the one the chart leads with."""
    total = sum(amount for _, amount in series)
    spending_days = [day for day, amount in series if amount > 0]
    peak_day, peak_amount = max(series, key=lambda entry: (entry[1], -entry[0]))

    busiest = (
        f"{html.escape(month_label)} {peak_day}"
        f' <span class="unit">{html.escape(format_money(peak_amount))}</span>'
        if spending_days
        else "—"
    )

    return (
        '<div class="tiles">'
        f'<div class="tile"><div class="label">Total spent</div>'
        f'<div class="value">{html.escape(format_money(total))}</div></div>'
        f'<div class="tile"><div class="label">Days with spending</div>'
        f'<div class="value">{len(spending_days)} '
        f'<span class="unit">of {days_in_month}</span></div></div>'
        f'<div class="tile"><div class="label">Busiest day</div>'
        f'<div class="value">{busiest}</div></div>'
        "</div>"
    )


def build_daily_series(month, daily_totals):
    """
    Turns the sparse ("YYYY-MM-DD", total) rows the repository returns into one
    entry per day of the month, filling the days with no spending with zero.

    Returns (series, days_in_month) where series is [(day_number, amount)].
    """
    year, month_number = (int(part) for part in month.split("-"))
    days_in_month = calendar.monthrange(year, month_number)[1]

    totals_by_day = {
        int(row_date[8:10]): total
        for row_date, total in daily_totals
    }

    series = [
        (day, totals_by_day.get(day, 0))
        for day in range(1, days_in_month + 1)
    ]

    return series, days_in_month


def _month_labels(month):
    """("Sep 2026", "September 2026") for a "YYYY-MM" month."""
    year, month_number = (int(part) for part in month.split("-"))

    return (
        f"{calendar.month_abbr[month_number]} {year}",
        f"{calendar.month_name[month_number]} {year}",
    )


def render_monthly_spending_fragment(month, daily_totals):
    """
    One month of spending as (css, html) rather than as a whole document.

    The browser client injects these into a page it already owns, which is why
    the split exists: the stylesheet is scoped under `.spending-chart` and the
    markup is a body fragment, so both drop into a React tree unchanged.

    Rendering it here rather than reimplementing it in JavaScript is the point
    — a second renderer would drift from this one, and the twenty-odd checks in
    tests/test_reports.py would then be covering a chart nobody looks at.

    Injecting the result is safe for a specific, checkable reason: every
    user-supplied string in this module goes through html.escape, which is the
    same guarantee the standalone report has always relied on.
    """
    month_label, long_month_label = _month_labels(month)

    series, days_in_month = build_daily_series(month, daily_totals)
    total = sum(amount for _, amount in series)

    if total > 0:
        body = (
            f'<div class="card">{_render_chart(series, month_label, days_in_month)}</div>'
            f"{_render_table(series, month_label)}"
        )
    else:
        body = (
            f'<div class="card"><p class="empty">'
            f"No expenses recorded in {html.escape(long_month_label)}."
            f"</p></div>"
        )

    fragment = (
        f"<h1>{html.escape(long_month_label)} spending</h1>"
        f'<p class="subtitle">Total spent on each day of the month. '
        f"Amounts in {html.escape(CURRENCY_SYMBOL)}.</p>"
        f"{_render_tiles(series, month_label, days_in_month)}"
        f"{body}"
    )

    return STYLESHEET, fragment


def render_monthly_spending(month, daily_totals):
    """
    Renders one month of spending as a complete HTML document.

    `month` is "YYYY-MM" and `daily_totals` the ("YYYY-MM-DD", total) rows for
    it; days missing from that list are drawn as days with no spending.
    """
    _, long_month_label = _month_labels(month)
    css, body = render_monthly_spending_fragment(month, daily_totals)

    return (
        "<!DOCTYPE html>"
        '<html lang="en">'
        "<head>"
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{html.escape(long_month_label)} spending</title>"
        f"<style>{css}</style>"
        "</head>"
        '<body class="spending-chart">'
        f"{body}"
        "</body>"
        "</html>"
    )


def report_filename(month):
    """One file per month, so charting a second month never overwrites the first."""
    return f"spending-{month}.html"


def write_monthly_spending(month, daily_totals, directory):
    """
    Renders the chart to a file in `directory` and returns its path, creating
    the directory if this is the first report.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)

    path = directory / report_filename(month)

    path.write_text(
        render_monthly_spending(month, daily_totals),
        encoding="utf-8",
    )

    return path
