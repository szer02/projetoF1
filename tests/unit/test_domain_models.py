from collections.abc import Callable
from typing import Any

import pytest
from pydantic import ValidationError

from projetof1.domain.models import (
    BestSectors,
    Driver,
    Lap,
    Meeting,
    PitStop,
    Session,
    SessionResult,
    Stint,
    Weather,
)

type LoadFixture = Callable[[str], list[dict[str, Any]]]


@pytest.mark.parametrize(
    ("fixture", "model"),
    [
        ("meetings", Meeting),
        ("sessions", Session),
        ("drivers", Driver),
        ("laps", Lap),
        ("stints", Stint),
        ("pit", PitStop),
        ("session_result_race", SessionResult),
        ("session_result_quali", SessionResult),
        ("weather", Weather),
    ],
)
def test_fixtures_parse_ignoring_extra_fields(
    load_fixture: LoadFixture, fixture: str, model: type[Any]
) -> None:
    items = [model.model_validate(item) for item in load_fixture(fixture)]

    assert len(items) == len(load_fixture(fixture))


def test_race_result_scalars_become_single_item_lists(
    load_fixture: LoadFixture,
) -> None:
    winner = SessionResult.model_validate(load_fixture("session_result_race")[1])

    assert winner.duration == [5628.113]
    assert winner.gap_to_leader == [0]


def test_quali_result_keeps_q1_q2_q3_lists(load_fixture: LoadFixture) -> None:
    pole = SessionResult.model_validate(load_fixture("session_result_quali")[0])

    assert pole.duration == [92.3, 91.4, 90.9]


def test_missing_result_values_become_empty_lists() -> None:
    result = SessionResult.model_validate(
        {"driver_number": 11, "duration": None, "gap_to_leader": None}
    )

    assert result.duration == []
    assert result.gap_to_leader == []


def test_gap_accepts_text_from_api() -> None:
    result = SessionResult.model_validate(
        {"driver_number": 2, "gap_to_leader": "+1 LAP"}
    )

    assert result.gap_to_leader == ["+1 LAP"]


def test_model_without_required_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Lap.model_validate({"lap_number": 1})


@pytest.mark.parametrize(
    ("session_type", "expected"), [("Race", True), ("Qualifying", False)]
)
def test_session_is_race(
    make_session: Callable[..., Session], session_type: str, expected: bool
) -> None:
    assert make_session(session_type=session_type).is_race is expected


def test_ideal_lap_sums_best_sectors() -> None:
    assert BestSectors(1, 30.0, 35.0, 30.001).ideal_lap == 95.001


def test_ideal_lap_is_none_when_a_sector_is_missing() -> None:
    assert BestSectors(1, 30.0, None, 30.0).ideal_lap is None
