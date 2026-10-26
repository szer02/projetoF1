from collections.abc import Callable

import pytest

from projetof1.domain.models import Driver, Lap
from projetof1.processing.laps import (
    best_sectors,
    compute_top_n_laps,
    compute_top_n_laps_overall,
    filter_valid_laps,
    lap_time_series,
)

type MakeLap = Callable[..., Lap]


def test_filter_valid_laps_drops_untimed_zero_and_pit_out(make_lap: MakeLap) -> None:
    valid = make_lap(1, 2, 95.0)
    laps = [
        make_lap(1, 1, None),
        make_lap(1, 3, 0.0),
        make_lap(1, 4, 94.0, pit_out=True),
        valid,
    ]

    assert filter_valid_laps(laps) == [valid]


def test_filter_valid_laps_treats_unknown_pit_flag_as_valid() -> None:
    lap = Lap(driver_number=1, lap_number=2, lap_duration=95.0, is_pit_out_lap=None)

    assert filter_valid_laps([lap]) == [lap]


def test_top_n_ranks_best_lap_per_driver(
    make_lap: MakeLap, driver_index: dict[int, Driver]
) -> None:
    laps = [
        make_lap(1, 2, 95.5),
        make_lap(1, 3, 95.0, sectors=(30.0, 35.0, 30.0)),
        make_lap(11, 2, 96.0),
        make_lap(44, 2, 94.0, pit_out=True),  # descartada
        make_lap(44, 3, 95.2),
    ]

    ranking = compute_top_n_laps(laps, driver_index, n=10)

    assert [(e.position, e.driver.name_acronym, e.lap_duration) for e in ranking] == [
        (1, "VER", 95.0),
        (2, "HAM", 95.2),
        (3, "PER", 96.0),
    ]
    assert ranking[0].sector_1 == 30.0
    assert [e.gap_to_fastest for e in ranking] == [0.0, 0.2, 1.0]


def test_top_n_breaks_ties_by_earlier_lap_then_driver_number(
    make_lap: MakeLap, driver_index: dict[int, Driver]
) -> None:
    laps = [make_lap(44, 5, 95.0), make_lap(11, 3, 95.0), make_lap(1, 3, 95.0)]

    ranking = compute_top_n_laps(laps, driver_index, n=3)

    assert [e.driver.driver_number for e in ranking] == [1, 11, 44]


def test_top_n_limits_number_of_entries(
    make_lap: MakeLap, driver_index: dict[int, Driver]
) -> None:
    laps = [make_lap(number, 2, 90.0 + number) for number in (1, 11, 44)]

    assert len(compute_top_n_laps(laps, driver_index, n=2)) == 2


def test_top_n_with_no_valid_laps_returns_empty(
    make_lap: MakeLap, driver_index: dict[int, Driver]
) -> None:
    assert compute_top_n_laps([make_lap(1, 1, None)], driver_index, n=10) == []


def test_top_n_with_invalid_n_raises(driver_index: dict[int, Driver]) -> None:
    with pytest.raises(ValueError, match="n deve ser"):
        compute_top_n_laps([], driver_index, n=0)


def test_top_n_overall_allows_same_driver_more_than_once(
    make_lap: MakeLap, driver_index: dict[int, Driver]
) -> None:
    # Bahrein 2024: o critério "geral" repete VER, como no ranking da aula.
    laps = [
        make_lap(1, 39, 92.608),
        make_lap(16, 36, 94.090),
        make_lap(1, 43, 94.151),
        make_lap(1, 46, 94.193),
        make_lap(44, 48, 94.199),
        make_lap(16, 1, 90.0, pit_out=True),  # descartada
    ]

    ranking = compute_top_n_laps_overall(laps, driver_index, n=5)

    assert [(e.driver.driver_number, e.lap_number) for e in ranking] == [
        (1, 39),
        (16, 36),
        (1, 43),
        (1, 46),
        (44, 48),
    ]
    assert [e.position for e in ranking] == [1, 2, 3, 4, 5]
    assert ranking[2].gap_to_fastest == 1.543


def test_top_n_overall_and_per_driver_differ_on_same_laps(
    make_lap: MakeLap, driver_index: dict[int, Driver]
) -> None:
    laps = [make_lap(1, 2, 95.0), make_lap(1, 3, 95.1), make_lap(44, 2, 95.2)]

    per_driver = compute_top_n_laps(laps, driver_index, n=3)
    overall = compute_top_n_laps_overall(laps, driver_index, n=3)

    assert [e.driver.driver_number for e in per_driver] == [1, 44]
    assert [e.driver.driver_number for e in overall] == [1, 1, 44]


def test_top_n_overall_breaks_ties_deterministically(
    make_lap: MakeLap, driver_index: dict[int, Driver]
) -> None:
    laps = [make_lap(44, 5, 95.0), make_lap(1, 7, 95.0), make_lap(1, 5, 95.0)]

    ranking = compute_top_n_laps_overall(laps, driver_index, n=3)

    assert [(e.lap_number, e.driver.driver_number) for e in ranking] == [
        (5, 1),
        (5, 44),
        (7, 1),
    ]


def test_top_n_overall_with_empty_input_and_invalid_n(
    driver_index: dict[int, Driver],
) -> None:
    assert compute_top_n_laps_overall([], driver_index, n=5) == []
    with pytest.raises(ValueError, match="n deve ser"):
        compute_top_n_laps_overall([], driver_index, n=0)


def test_lap_time_series_removes_outliers_and_sorts_by_lap(
    make_lap: MakeLap, driver_index: dict[int, Driver]
) -> None:
    laps = [
        make_lap(1, 3, 95.0),
        make_lap(1, 1, 96.0),
        make_lap(1, 2, 130.0),  # safety car: acima de 107% da mediana
        make_lap(1, 4, 95.5),
    ]

    (series,) = lap_time_series(laps, driver_index)

    assert series.driver.name_acronym == "VER"
    assert series.lap_numbers == (1, 3, 4)
    assert series.lap_durations == (96.0, 95.0, 95.5)


def test_lap_time_series_follows_requested_order_and_skips_missing(
    make_lap: MakeLap, driver_index: dict[int, Driver]
) -> None:
    laps = [make_lap(1, 2, 95.0), make_lap(44, 2, 95.5)]

    series = lap_time_series(laps, driver_index, driver_numbers=[44, 11, 1])

    assert [item.driver.driver_number for item in series] == [44, 1]


def test_lap_time_series_with_empty_input_returns_empty(
    driver_index: dict[int, Driver],
) -> None:
    assert lap_time_series([], driver_index) == []


def test_best_sectors_takes_minimum_per_sector_ignoring_missing(
    make_lap: MakeLap,
) -> None:
    laps = [
        make_lap(1, 2, 95.5, sectors=(30.1, 35.2, None)),
        make_lap(1, 3, 95.0, sectors=(30.3, 35.0, 30.0)),
        make_lap(44, 3, 95.2, sectors=(None, None, None)),
    ]

    result = {item.driver_number: item for item in best_sectors(laps)}

    assert (result[1].sector_1, result[1].sector_2, result[1].sector_3) == (
        30.1,
        35.0,
        30.0,
    )
    assert result[1].ideal_lap == 95.1
    assert result[44].sector_1 is None
