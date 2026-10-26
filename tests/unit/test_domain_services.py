from collections.abc import Callable
from typing import Any

import pytest
from pytest_mock import MockerFixture

from projetof1.domain.models import (
    Driver,
    Lap,
    Meeting,
    PitStop,
    Session,
    SessionResult,
    Stint,
    Weather,
)
from projetof1.domain.repositories import (
    DataSourceError,
    DriverRepository,
    F1Repositories,
    LapRepository,
    MeetingRepository,
    PitRepository,
    SessionRepository,
    SessionResultRepository,
    StintRepository,
    WeatherRepository,
)
from projetof1.domain.services import F1DashboardService

type LoadFixture = Callable[[str], list[dict[str, Any]]]


@pytest.fixture
def repos(mocker: MockerFixture, load_fixture: LoadFixture) -> F1Repositories:
    def repo(contract: type[Any], model: type[Any], fixture: str) -> Any:
        mock = mocker.create_autospec(contract, instance=True)
        mock.fetch.return_value = [
            model.model_validate(i) for i in load_fixture(fixture)
        ]
        return mock

    return F1Repositories(
        meetings=repo(MeetingRepository, Meeting, "meetings"),
        sessions=repo(SessionRepository, Session, "sessions"),
        drivers=repo(DriverRepository, Driver, "drivers"),
        laps=repo(LapRepository, Lap, "laps"),
        stints=repo(StintRepository, Stint, "stints"),
        pits=repo(PitRepository, PitStop, "pit"),
        results=repo(SessionResultRepository, SessionResult, "session_result_race"),
        weather=repo(WeatherRepository, Weather, "weather"),
    )


def test_list_meetings_sorts_by_date_and_skips_cancelled(repos: F1Repositories) -> None:
    meetings = F1DashboardService(repos).list_meetings(2023)

    assert [m.meeting_key for m in meetings] == [1, 2]
    repos.meetings.fetch.assert_called_once_with(2023)


def test_list_sessions_sorts_by_date(repos: F1Repositories) -> None:
    sessions = F1DashboardService(repos).list_sessions(1)

    assert [s.session_name for s in sessions] == ["Qualifying", "Race"]


def test_session_overview_combines_all_sources(
    repos: F1Repositories, make_session: Callable[..., Session]
) -> None:
    session = make_session(session_key=102)

    overview = F1DashboardService(repos).get_session_overview(session, top_n=3)

    assert overview.session == session
    assert [e.driver.name_acronym for e in overview.classification] == [
        "VER",
        "HAM",
        "PER",
    ]
    assert [d.name_acronym for d in overview.drivers] == ["VER", "HAM", "PER"]
    assert [e.driver.name_acronym for e in overview.fastest_laps] == [
        "VER",
        "HAM",
        "PER",
    ]
    assert [
        (e.driver.name_acronym, e.lap_number) for e in overview.fastest_laps_overall
    ] == [("VER", 3), ("HAM", 3), ("VER", 2)]
    assert [s.driver.name_acronym for s in overview.pace] == ["VER", "HAM", "PER"]
    assert [b.driver.name_acronym for b in overview.stints] == ["VER", "VER", "HAM"]
    assert [p.lap_number for p in overview.pit_stops] == [20, 30]
    assert overview.weather is not None
    assert overview.weather.samples == 2
    for repo in (repos.drivers, repos.laps, repos.stints, repos.pits, repos.results):
        repo.fetch.assert_called_once_with(102)


def test_session_overview_with_empty_sources(
    repos: F1Repositories, make_session: Callable[..., Session]
) -> None:
    for repo in (
        repos.drivers,
        repos.laps,
        repos.stints,
        repos.pits,
        repos.results,
        repos.weather,
    ):
        repo.fetch.return_value = []

    overview = F1DashboardService(repos).get_session_overview(make_session())

    assert overview.classification == ()
    assert overview.fastest_laps == ()
    assert overview.fastest_laps_overall == ()
    assert overview.weather is None


def test_session_overview_rejects_invalid_top_n(
    repos: F1Repositories, make_session: Callable[..., Session]
) -> None:
    with pytest.raises(ValueError, match="top_n"):
        F1DashboardService(repos).get_session_overview(make_session(), top_n=0)
    repos.drivers.fetch.assert_not_called()


def test_data_source_errors_propagate(
    repos: F1Repositories, make_session: Callable[..., Session]
) -> None:
    repos.laps.fetch.side_effect = DataSourceError("fora do ar")

    with pytest.raises(DataSourceError):
        F1DashboardService(repos).get_session_overview(make_session())
