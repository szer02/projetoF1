from projetof1.domain.models import Driver, PitStop, Stint
from projetof1.processing.stints import (
    UNKNOWN_COMPOUND,
    build_stint_timeline,
    pit_summary,
)


def test_stint_timeline_orders_by_driver_order_then_stint(
    driver_index: dict[int, Driver],
) -> None:
    stints = [
        Stint(
            driver_number=1, stint_number=2, compound="hard", lap_start=21, lap_end=57
        ),
        Stint(
            driver_number=1, stint_number=1, compound="SOFT", lap_start=1, lap_end=20
        ),
        Stint(
            driver_number=44, stint_number=1, compound="MEDIUM", lap_start=1, lap_end=57
        ),
    ]

    bars = build_stint_timeline(stints, driver_index, driver_order=[44, 1])

    assert [(b.driver.name_acronym, b.stint_number, b.compound) for b in bars] == [
        ("HAM", 1, "MEDIUM"),
        ("VER", 1, "SOFT"),
        ("VER", 2, "HARD"),
    ]


def test_stint_timeline_handles_missing_fields(driver_index: dict[int, Driver]) -> None:
    stints = [
        Stint(
            driver_number=1, stint_number=1, compound=None, lap_start=1, lap_end=None
        ),
        Stint(
            driver_number=11,
            stint_number=1,
            compound="SOFT",
            lap_start=None,
            lap_end=10,
        ),
    ]

    (bar,) = build_stint_timeline(stints, driver_index)

    assert bar.compound == UNKNOWN_COMPOUND
    assert (bar.lap_start, bar.lap_end) == (1, 1)


def test_stint_timeline_puts_unlisted_drivers_last(
    driver_index: dict[int, Driver],
) -> None:
    stints = [
        Stint(driver_number=44, stint_number=1, lap_start=1, lap_end=5),
        Stint(driver_number=1, stint_number=1, lap_start=1, lap_end=5),
    ]

    bars = build_stint_timeline(stints, driver_index, driver_order=[1])

    assert [bar.driver.driver_number for bar in bars] == [1, 44]


def test_pit_summary_skips_entries_without_lane_time_and_sorts_by_lap(
    driver_index: dict[int, Driver],
) -> None:
    pits = [
        PitStop(driver_number=44, lap_number=30, lane_duration=22.4, stop_duration=2.4),
        PitStop(driver_number=1, lap_number=20, lane_duration=21.9),
        PitStop(driver_number=11, lap_number=1),
    ]

    entries = pit_summary(pits, driver_index)

    assert [(e.lap_number, e.driver.name_acronym) for e in entries] == [
        (20, "VER"),
        (30, "HAM"),
    ]
    assert entries[1].stop_duration == 2.4


def test_pit_summary_with_empty_input() -> None:
    assert pit_summary([], {}) == []
