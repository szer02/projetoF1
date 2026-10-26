"""Testes do app Streamlit com repositórios em memória (sem rede)."""

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

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

APP_PATH = (
    Path(__file__).resolve().parents[2] / "src" / "projetof1" / "dashboard" / "app.py"
)
APP_TIMEOUT_SECONDS = 30

BAHRAIN_2023, BAHRAIN_2024, ABU_DHABI_2024 = 3, 1, 2


def _meeting(key: int, name: str, start: datetime) -> Meeting:
    return Meeting(
        meeting_key=key,
        meeting_name=name,
        country_name="X",
        circuit_short_name="Y",
        year=start.year,
        date_start=start,
    )


def _session(key: int, meeting_key: int, name: str, start: datetime) -> Session:
    return Session(
        session_key=key,
        meeting_key=meeting_key,
        session_name=name,
        session_type="Race" if name == "Race" else name,
        date_start=start,
        date_end=start,
        year=start.year,
    )


MEETINGS = {
    2023: [
        _meeting(BAHRAIN_2023, "Bahrain Grand Prix", datetime(2023, 3, 3, tzinfo=UTC))
    ],
    2024: [
        _meeting(BAHRAIN_2024, "Bahrain Grand Prix", datetime(2024, 2, 29, tzinfo=UTC)),
        _meeting(
            ABU_DHABI_2024, "Abu Dhabi Grand Prix", datetime(2024, 12, 6, tzinfo=UTC)
        ),
    ],
}
SESSIONS = {
    BAHRAIN_2023: [
        _session(32, BAHRAIN_2023, "Race", datetime(2023, 3, 5, 15, tzinfo=UTC))
    ],
    BAHRAIN_2024: [
        _session(11, BAHRAIN_2024, "Qualifying", datetime(2024, 3, 1, 16, tzinfo=UTC)),
        _session(12, BAHRAIN_2024, "Race", datetime(2024, 3, 2, 15, tzinfo=UTC)),
    ],
    ABU_DHABI_2024: [
        _session(
            21, ABU_DHABI_2024, "Qualifying", datetime(2024, 12, 7, 14, tzinfo=UTC)
        ),
        _session(22, ABU_DHABI_2024, "Race", datetime(2024, 12, 8, 13, tzinfo=UTC)),
    ],
}
DRIVERS = [
    Driver(driver_number=1, full_name="Max VERSTAPPEN", name_acronym="VER"),
    Driver(driver_number=16, full_name="Charles LECLERC", name_acronym="LEC"),
    Driver(driver_number=20, full_name="Kevin MAGNUSSEN", name_acronym="MAG"),
]


def _lap(driver: int, lap: int, duration: float) -> Lap:
    return Lap(driver_number=driver, lap_number=lap, lap_duration=duration)


LAPS = {
    32: [_lap(1, 30, 93.0)],
    12: [
        _lap(1, 39, 92.608),
        _lap(16, 36, 94.090),
        _lap(1, 43, 94.151),
        _lap(1, 46, 94.193),
    ],
    22: [_lap(20, 57, 85.637), _lap(20, 32, 87.235), _lap(1, 44, 87.5)],
}


class _Meetings(MeetingRepository):
    def fetch(self, year: int) -> list[Meeting]:
        return MEETINGS.get(year, [])


class _Sessions(SessionRepository):
    def fetch(self, meeting_key: int) -> list[Session]:
        return SESSIONS.get(meeting_key, [])


class _Drivers(DriverRepository):
    def fetch(self, session_key: int) -> list[Driver]:
        return DRIVERS


class _Laps(LapRepository):
    def fetch(self, session_key: int, driver_number: int | None = None) -> list[Lap]:
        return LAPS.get(session_key, [])


class _Stints(StintRepository):
    def fetch(self, session_key: int) -> list[Stint]:
        return []


class _Pits(PitRepository):
    def fetch(self, session_key: int) -> list[PitStop]:
        return []


class _Results(SessionResultRepository):
    def fetch(self, session_key: int) -> list[SessionResult]:
        return []


class _Weather(WeatherRepository):
    def fetch(self, session_key: int) -> list[Weather]:
        return []


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch) -> Iterator[AppTest]:
    repositories = F1Repositories(
        _Meetings(),
        _Sessions(),
        _Drivers(),
        _Laps(),
        _Stints(),
        _Pits(),
        _Results(),
        _Weather(),
    )
    monkeypatch.setattr(
        "projetof1.ingestion.openf1_repositories.build_repositories",
        lambda client: repositories,
    )
    st.cache_data.clear()
    st.cache_resource.clear()
    yield AppTest.from_file(str(APP_PATH), default_timeout=APP_TIMEOUT_SECONDS)
    st.cache_data.clear()
    st.cache_resource.clear()


def _selectbox(at: AppTest, label: str) -> Any:
    return next(box for box in at.sidebar.selectbox if box.label == label)


def _header(at: AppTest) -> str:
    return next(
        item.value for item in at.markdown if '<div class="f1-header">' in item.value
    )


def _fastest_drivers(at: AppTest) -> list[str]:
    return list(at.dataframe[0].value["Piloto"])


def _select_year(at: AppTest, year: int) -> None:
    _selectbox(at, "Temporada").set_value(year).run()


def test_default_opens_latest_race_of_the_season(app: AppTest) -> None:
    app.run()
    _select_year(app, 2024)

    assert not app.exception
    assert "Abu Dhabi Grand Prix" in _header(app)
    assert "08/12/2024" in _header(app)
    assert _fastest_drivers(app)[0] == "Kevin MAGNUSSEN"


def test_changing_grand_prix_updates_the_session(app: AppTest) -> None:
    app.run()
    _select_year(app, 2024)

    _selectbox(app, "Grande Prêmio").select_index(0).run()  # Bahrain 2024

    assert not app.exception
    header = _header(app)
    assert "Bahrain Grand Prix" in header
    assert "02/03/2024" in header  # corrida do Bahrein, não a de Abu Dhabi
    assert _fastest_drivers(app)[0] == "Max VERSTAPPEN"


def test_fastest_laps_views_per_driver_and_overall(app: AppTest) -> None:
    app.run()
    _select_year(app, 2024)
    _selectbox(app, "Grande Prêmio").select_index(0).run()  # Bahrain 2024

    assert _fastest_drivers(app) == ["Max VERSTAPPEN", "Charles LECLERC"]

    app.radio(key="fastest-view").set_value(
        "Voltas mais rápidas da sessão (geral)"
    ).run()

    assert not app.exception
    assert _fastest_drivers(app) == [
        "Max VERSTAPPEN",
        "Charles LECLERC",
        "Max VERSTAPPEN",
        "Max VERSTAPPEN",
    ]
    assert list(app.dataframe[0].value["Volta"]) == [39, 36, 43, 46]


def test_changing_season_updates_grand_prix_with_same_name(app: AppTest) -> None:
    app.run()
    _select_year(app, 2024)
    _selectbox(app, "Grande Prêmio").select_index(0).run()  # Bahrain 2024

    _select_year(app, 2023)

    assert not app.exception
    assert "05/03/2023" in _header(app)  # Bahrain 2023, não 2024
