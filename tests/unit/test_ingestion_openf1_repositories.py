import logging
from collections.abc import Callable
from typing import Any

import pytest
from pytest_mock import MockerFixture

from projetof1.domain.models import Driver, Lap
from projetof1.ingestion.http_client import HttpClient
from projetof1.ingestion.openf1_repositories import (
    OpenF1DriverRepository,
    OpenF1LapRepository,
    OpenF1MeetingRepository,
    OpenF1PitRepository,
    OpenF1SessionRepository,
    OpenF1SessionResultRepository,
    OpenF1StintRepository,
    OpenF1WeatherRepository,
    build_repositories,
    parse_items,
)

type LoadFixture = Callable[[str], list[dict[str, Any]]]


@pytest.fixture
def client(mocker: MockerFixture) -> Any:
    return mocker.create_autospec(HttpClient, instance=True)


@pytest.mark.parametrize(
    ("repository", "argument", "endpoint", "params", "fixture"),
    [
        (OpenF1MeetingRepository, 2023, "meetings", {"year": 2023}, "meetings"),
        (OpenF1SessionRepository, 1, "sessions", {"meeting_key": 1}, "sessions"),
        (OpenF1DriverRepository, 9, "drivers", {"session_key": 9}, "drivers"),
        (OpenF1LapRepository, 9, "laps", {"session_key": 9}, "laps"),
        (OpenF1StintRepository, 9, "stints", {"session_key": 9}, "stints"),
        (OpenF1PitRepository, 9, "pit", {"session_key": 9}, "pit"),
        (
            OpenF1SessionResultRepository,
            9,
            "session_result",
            {"session_key": 9},
            "session_result_race",
        ),
        (OpenF1WeatherRepository, 9, "weather", {"session_key": 9}, "weather"),
    ],
)
def test_repository_queries_endpoint_and_parses_items(
    client: Any,
    load_fixture: LoadFixture,
    repository: type[Any],
    argument: int,
    endpoint: str,
    params: dict[str, int],
    fixture: str,
) -> None:
    client.get.return_value = load_fixture(fixture)

    items = repository(client).fetch(argument)

    client.get.assert_called_once_with(endpoint, params)
    assert len(items) == len(load_fixture(fixture))


def test_lap_repository_filters_by_driver(client: Any) -> None:
    client.get.return_value = []

    OpenF1LapRepository(client).fetch(9, driver_number=44)

    client.get.assert_called_once_with("laps", {"session_key": 9, "driver_number": 44})


def test_parse_items_skips_and_logs_invalid_items(
    caplog: pytest.LogCaptureFixture,
) -> None:
    items = [
        {"driver_number": 1, "lap_number": 1, "lap_duration": 95.0},
        {"lap_number": 2},  # sem driver_number
        {"driver_number": "abc", "lap_number": 3},
    ]

    with caplog.at_level(logging.WARNING):
        laps = parse_items(items, Lap, "laps")

    assert [lap.lap_number for lap in laps] == [1]
    assert "endpoint=laps invalidos=2 validos=1" in caplog.text


def test_parse_items_with_all_valid_does_not_log(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING):
        drivers = parse_items(
            [{"driver_number": 1, "full_name": "A", "name_acronym": "AAA"}],
            Driver,
            "drivers",
        )

    assert len(drivers) == 1
    assert caplog.text == ""


def test_build_repositories_wires_every_repository(client: Any) -> None:
    repos = build_repositories(client)

    assert isinstance(repos.meetings, OpenF1MeetingRepository)
    assert isinstance(repos.weather, OpenF1WeatherRepository)
    assert isinstance(repos.results, OpenF1SessionResultRepository)
