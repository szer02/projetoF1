from collections.abc import Callable

from projetof1.dashboard.charts import (
    EMPTY_MESSAGE,
    fastest_laps_bar,
    pace_lines,
    stint_timeline,
)
from projetof1.domain.models import Driver, FastestLapEntry, PaceSeries, StintBar
from projetof1.processing.formatting import COMPOUND_COLORS

type MakeDriver = Callable[..., Driver]


def lap_entry(position: int, driver: Driver, duration: float) -> FastestLapEntry:
    return FastestLapEntry(
        position=position,
        driver=driver,
        lap_number=10,
        lap_duration=duration,
        sector_1=None,
        sector_2=None,
        sector_3=None,
        gap_to_fastest=round(duration - 95.0, 3),
    )


def test_fastest_laps_bar_puts_fastest_on_top_with_team_colors(
    make_driver: MakeDriver,
) -> None:
    ver = make_driver(1, "VER", team_colour="3671C6")
    ham = make_driver(44, "HAM", team_colour="27F4D2")

    fig = fastest_laps_bar([lap_entry(1, ver, 95.0), lap_entry(2, ham, 95.5)])

    (bar,) = fig.data
    assert list(bar.y) == ["P2  HAM", "P1  VER"]
    assert list(bar.marker.color) == ["#27F4D2", "#3671C6"]
    assert list(bar.text) == ["1:35.500", "1:35.000"]
    assert fig.layout.xaxis.range[0] < 95.0
    assert fig.layout.title.text == "Voltas mais rápidas"


def test_fastest_laps_bar_with_lap_in_label_and_custom_title(
    make_driver: MakeDriver,
) -> None:
    ver = make_driver(1, "VER")
    entries = [
        FastestLapEntry(1, ver, 39, 92.608, None, None, None, 0.0),
        FastestLapEntry(2, ver, 43, 94.151, None, None, None, 1.543),
    ]

    fig = fastest_laps_bar(entries, title="Top 2 · geral", show_lap_in_label=True)

    assert list(fig.data[0].y) == ["P2  VER · V43", "P1  VER · V39"]
    assert fig.layout.title.text == "Top 2 · geral"


def test_empty_charts_show_message() -> None:
    for fig in (fastest_laps_bar([]), pace_lines([]), stint_timeline([])):
        assert len(fig.data) == 0
        assert fig.layout.annotations[0].text == EMPTY_MESSAGE


def test_pace_lines_dash_teammates_sharing_color(make_driver: MakeDriver) -> None:
    series = [
        PaceSeries(make_driver(1, "VER"), (1, 2), (95.0, 95.2)),
        PaceSeries(make_driver(11, "PER"), (1, 2), (95.5, 95.6)),
        PaceSeries(make_driver(44, "HAM", team_colour="27F4D2"), (1,), (95.1,)),
    ]

    fig = pace_lines(series)

    assert [trace.name for trace in fig.data] == ["VER", "PER", "HAM"]
    assert [trace.line.dash for trace in fig.data] == ["solid", "dot", "solid"]
    assert list(fig.data[0].x) == [1, 2]


def test_stint_timeline_has_one_trace_per_compound(make_driver: MakeDriver) -> None:
    ver = make_driver(1, "VER")
    ham = make_driver(44, "HAM")
    bars = [
        StintBar(ver, 1, "SOFT", 1, 20, 0),
        StintBar(ver, 2, "HARD", 21, 57, None),
        StintBar(ham, 1, "SOFT", 1, 25, 2),
    ]

    fig = stint_timeline(bars)

    by_name = {trace.name: trace for trace in fig.data}
    assert set(by_name) == {"Soft", "Hard"}
    assert list(by_name["Soft"].base) == [0, 0]
    assert list(by_name["Soft"].x) == [20, 25]
    assert by_name["Hard"].marker.color == COMPOUND_COLORS["HARD"]
    assert list(fig.layout.yaxis.categoryarray) == ["HAM", "VER"]
