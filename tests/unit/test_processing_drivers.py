from collections.abc import Callable

from projetof1.domain.models import Driver
from projetof1.processing.drivers import build_driver_index, resolve_driver


def test_build_driver_index_keeps_first_occurrence(
    make_driver: Callable[..., Driver],
) -> None:
    first = make_driver(1, "VER")
    duplicate = make_driver(1, "XXX")

    index = build_driver_index([first, duplicate, make_driver(44, "HAM")])

    assert index == {1: first, 44: index[44]}
    assert index[1].name_acronym == "VER"


def test_build_driver_index_with_empty_input() -> None:
    assert build_driver_index([]) == {}


def test_resolve_driver_returns_known_driver(driver_index: dict[int, Driver]) -> None:
    assert resolve_driver(driver_index, 44).name_acronym == "HAM"


def test_resolve_driver_creates_placeholder_for_unknown_number() -> None:
    driver = resolve_driver({}, 99)

    assert driver.driver_number == 99
    assert driver.name_acronym == "99"
    assert driver.team_colour is None
