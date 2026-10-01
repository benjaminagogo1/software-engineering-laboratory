"""
Tests for the monthly spending chart.

These pin the parts of the design that are easy to break by accident: the bars
stay inside the plot, they never touch each other, and every value in the chart
is also reachable from a table.
"""

import re

from app.reports.monthly_chart import (
    BAR_GAP,
    BAR_MAX_WIDTH,
    MARGIN_LEFT,
    MARGIN_RIGHT,
    MARGIN_TOP,
    PLOT_HEIGHT,
    VIEW_WIDTH,
    build_daily_series,
    render_monthly_spending,
    report_filename,
    write_monthly_spending,
)


def bar_paths(page):
    return re.findall(r'<path class="bar" d="([^"]+)"', page)


def bar_box(path):
    """The (min_x, max_x, min_y, max_y) a bar path covers."""
    points = [
        (float(x), float(y))
        for x, y in re.findall(r"(-?\d+\.\d+) (-?\d+\.\d+)", path)
    ]

    xs = [x for x, _ in points]
    ys = [y for _, y in points]

    return min(xs), max(xs), min(ys), max(ys)


# --- Turning sparse rows into a month --------------------------------------


def test_days_without_spending_are_filled_with_zero():
    series, days_in_month = build_daily_series("2026-07", [("2026-07-04", 500.0)])

    assert days_in_month == 31
    assert len(series) == 31
    assert series[2] == (3, 0.0)
    assert series[3] == (4, 500.0)


def test_february_is_its_own_length():
    series, days_in_month = build_daily_series("2026-02", [])

    assert days_in_month == 28
    assert len(series) == 28


def test_a_leap_february_has_an_extra_day():
    _, days_in_month = build_daily_series("2028-02", [])

    assert days_in_month == 29


# --- The chart itself -------------------------------------------------------


def test_only_days_with_spending_get_a_bar():
    page = render_monthly_spending(
        "2026-07",
        [("2026-07-04", 500.0), ("2026-07-05", 200.0)],
    )

    assert len(bar_paths(page)) == 2


def test_bars_stay_inside_the_plot():
    page = render_monthly_spending(
        "2026-07",
        [("2026-07-04", 500.0), ("2026-07-18", 900.0)],
    )

    for path in bar_paths(page):
        _, _, min_y, max_y = bar_box(path)

        assert min_y >= MARGIN_TOP
        assert max_y <= MARGIN_TOP + PLOT_HEIGHT


def test_bars_never_exceed_the_maximum_width_or_touch_each_other():
    """A full month of bars is the tightest case: 31 of them."""
    page = render_monthly_spending(
        "2026-07",
        [(f"2026-07-{day:02d}", 100.0) for day in range(1, 32)],
    )

    band = (VIEW_WIDTH - MARGIN_LEFT - MARGIN_RIGHT) / 31

    for path in bar_paths(page):
        min_x, max_x, _, _ = bar_box(path)
        # Rounded to the precision the coordinates are written with, so the
        # comparison is about the geometry and not about float subtraction.
        width = round(max_x - min_x, 2)

        assert width <= BAR_MAX_WIDTH
        assert band - width >= BAR_GAP


def test_the_tallest_day_is_sized_against_the_axis_maximum():
    """Doubling the biggest amount must not change the tallest bar's height."""
    single = render_monthly_spending("2026-07", [("2026-07-04", 1000.0)])
    doubled = render_monthly_spending("2026-07", [("2026-07-04", 2000.0)])

    _, _, single_top, single_bottom = bar_box(bar_paths(single)[0])
    _, _, doubled_top, doubled_bottom = bar_box(bar_paths(doubled)[0])

    assert single_bottom == doubled_bottom
    assert single_bottom - single_top == doubled_bottom - doubled_top


def test_only_the_busiest_day_is_labelled_directly():
    page = render_monthly_spending(
        "2026-07",
        [("2026-07-04", 500.0), ("2026-07-18", 900.0)],
    )

    assert page.count('class="peak-label"') == 1
    assert "₦900.00" in page


def test_a_day_with_a_tiny_amount_still_gets_a_visible_bar():
    page = render_monthly_spending("2026-07", [("2026-07-04", 0.5), ("2026-07-05", 9000.0)])

    _, _, min_y, max_y = bar_box(bar_paths(page)[0])

    assert max_y - min_y >= 2


# --- Values, the table, and the axis ---------------------------------------


def test_the_table_view_carries_every_value_in_the_chart():
    page = render_monthly_spending(
        "2026-07",
        [("2026-07-04", 500.0), ("2026-07-18", 900.0)],
    )

    assert page.count("<tr><td>Jul 2026") == 2
    assert "₦500.00" in page
    assert "₦1,400.00" in page  # the total row


def test_every_bar_carries_its_value_as_hover_text():
    page = render_monthly_spending("2026-07", [("2026-07-04", 500.0)])

    assert "<title>Jul 2026 4: ₦500.00</title>" in page


def test_the_axis_avoids_awkward_numbers():
    """12500 splits into 0 / 5000 / 10000 / 15000 rather than 0 / 3125 / ..."""
    page = render_monthly_spending("2026-07", [("2026-07-04", 12500.0)])

    assert "₦5,000" in page
    assert "₦15,000" in page


def test_the_axis_survives_a_maximum_that_does_not_divide_evenly():
    page = render_monthly_spending("2026-07", [("2026-07-04", 3333.33)])

    assert "NaN" not in page
    assert "Infinity" not in page


# --- The document -----------------------------------------------------------


def test_the_document_is_self_contained():
    page = render_monthly_spending("2026-07", [("2026-07-04", 500.0)])

    assert page.startswith("<!DOCTYPE html>")
    assert page.rstrip().endswith("</html>")
    assert "<script" not in page
    assert "http://" not in page
    assert "https://" not in page


def test_the_chart_carries_a_dark_mode():
    page = render_monthly_spending("2026-07", [])

    assert "prefers-color-scheme: dark" in page
    assert '[data-theme="dark"]' in page
    # The dark step of the series hue, not an automatic flip of the light one.
    assert "#3987e5" in page
    assert "#2a78d6" in page


def test_a_month_without_expenses_says_so_instead_of_drawing():
    page = render_monthly_spending("2026-07", [])

    assert "No expenses recorded in July 2026." in page
    assert "<svg" not in page


def test_the_chart_names_itself():
    page = render_monthly_spending("2026-07", [("2026-07-04", 500.0)])

    assert "<title>July 2026 spending</title>" in page
    assert 'role="img"' in page
    assert "aria-label=" in page


# --- Writing it to disk -----------------------------------------------------


def test_one_file_per_month(tmp_path):
    reports = tmp_path / "reports"

    first = write_monthly_spending("2026-07", [], reports)
    second = write_monthly_spending("2026-08", [], reports)

    assert first.exists()
    assert second.exists()
    assert first.name == "spending-2026-07.html"
    assert second.name == "spending-2026-08.html"
    assert report_filename("2026-07") == "spending-2026-07.html"


def test_writing_creates_the_directory_on_first_use(tmp_path):
    reports = tmp_path / "does" / "not" / "exist" / "yet"

    path = write_monthly_spending("2026-07", [], reports)

    assert path.exists()
    assert path.read_text(encoding="utf-8").startswith("<!DOCTYPE html>")
