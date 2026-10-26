from collections.abc import Callable
from typing import Any

import pytest

from projetof1.domain.models import Driver, SessionResult
from projetof1.processing.results import (
    STATUS_DNF,
    STATUS_DNS,
    STATUS_DSQ,
    STATUS_FINISHED,
    build_classification,
    last_known,
    result_status,
)

type LoadFixture = Callable[[str], list[dict[str, Any]]]


@pytest.mark.parametrize(
    ("flags", "expected"),
    [
        pytest.param({}, STATUS_FINISHED, id="classificado"),
        pytest.param({"dnf": True}, STATUS_DNF, id="abandono"),
        pytest.param({"dns": True, "dnf": True}, STATUS_DNS, id="nao-largou"),
        pytest.param({"dsq": True, "dnf": True}, STATUS_DSQ, id="desclassificado"),
    ],
)
def test_result_status_precedence(flags: dict[str, bool], expected: str) -> None:
    assert result_status(SessionResult(driver_number=1, **flags)) == expected


def test_build_classification_orders_by_position_with_nulls_last(
    load_fixture: LoadFixture, driver_index: dict[int, Driver]
) -> None:
    results = [
        SessionResult.model_validate(i) for i in load_fixture("session_result_race")
    ]

    entries = build_classification(results, driver_index)

    assert [(e.position, e.driver.name_acronym, e.status) for e in entries] == [
        (1, "VER", STATUS_FINISHED),
        (2, "HAM", STATUS_FINISHED),
        (None, "PER", STATUS_DNF),
    ]
    assert entries[0].durations == (5628.113,)


def test_build_classification_with_empty_input() -> None:
    assert build_classification([], {}) == []


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        pytest.param([93.4, None, None], 93.4, id="eliminado-no-q1"),
        pytest.param([92.3, 91.4, 90.9], 90.9, id="chegou-ao-q3"),
        pytest.param([None], None, id="sem-tempo"),
        pytest.param([], None, id="vazio"),
        pytest.param(["+1 LAP"], "+1 LAP", id="texto"),
    ],
)
def test_last_known_returns_last_non_null(
    values: list[float | str | None], expected: float | str | None
) -> None:
    assert last_known(values) == expected
