"""Testes contra a OpenF1 real (requer internet). Rodar com `--no-cov`.

Usam sessões históricas fixas (GP de Singapura 2023), cujo resultado não muda.
"""

from collections.abc import Iterator

import pytest

from projetof1.domain.services import F1DashboardService
from projetof1.ingestion.http_client import HttpClient
from projetof1.ingestion.openf1_repositories import build_repositories
from projetof1.utils.config import DEFAULT_BASE_URL

SINGAPORE_2023_MEETING = 1219
SINGAPORE_2023_QUALIFYING = 9161
SINGAPORE_2023_RACE = 9165
LIVE_TIMEOUT_SECONDS = 30.0

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def service() -> Iterator[F1DashboardService]:
    with HttpClient(
        DEFAULT_BASE_URL, timeout=LIVE_TIMEOUT_SECONDS, backoff_seconds=2.0
    ) as client:
        yield F1DashboardService(build_repositories(client))


def test_list_meetings_2023_includes_singapore(service: F1DashboardService) -> None:
    meetings = service.list_meetings(2023)

    assert SINGAPORE_2023_MEETING in {m.meeting_key for m in meetings}
    assert meetings == sorted(meetings, key=lambda m: m.date_start)


def test_singapore_2023_has_qualifying_and_race(service: F1DashboardService) -> None:
    sessions = {s.session_key: s for s in service.list_sessions(SINGAPORE_2023_MEETING)}

    assert sessions[SINGAPORE_2023_QUALIFYING].session_type == "Qualifying"
    assert sessions[SINGAPORE_2023_RACE].is_race


def test_qualifying_overview_has_q1_q2_q3_and_pole(service: F1DashboardService) -> None:
    session = next(
        s
        for s in service.list_sessions(SINGAPORE_2023_MEETING)
        if s.session_key == SINGAPORE_2023_QUALIFYING
    )

    overview = service.get_session_overview(session)

    pole = overview.classification[0]
    assert pole.position == 1
    assert pole.driver.name_acronym == "SAI"
    assert len(pole.durations) == 3
    assert len(overview.fastest_laps) == 20  # um por piloto (teto padrão = 20)
    assert len(overview.fastest_laps_overall) == 20
    overall_drivers = {e.driver.driver_number for e in overview.fastest_laps_overall}
    assert len(overall_drivers) < 20  # na visão geral, pilotos se repetem
    assert overview.weather is not None


def test_race_overview_has_strategy_and_winner(service: F1DashboardService) -> None:
    session = next(
        s
        for s in service.list_sessions(SINGAPORE_2023_MEETING)
        if s.session_key == SINGAPORE_2023_RACE
    )

    overview = service.get_session_overview(session)

    assert overview.classification[0].driver.name_acronym == "SAI"
    assert any(entry.status == "DNF" for entry in overview.classification)
    assert overview.stints
    assert overview.pit_stops
