import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from projetof1.domain.models import Driver, Lap, Session

FIXTURES_DIR = Path(__file__).parent / "fixtures"

type Payload = list[dict[str, Any]]


@pytest.fixture
def load_fixture() -> Callable[[str], Payload]:
    def _load(name: str) -> Payload:
        return json.loads((FIXTURES_DIR / f"{name}.json").read_text(encoding="utf-8"))

    return _load


@pytest.fixture
def make_driver() -> Callable[..., Driver]:
    def _make(
        number: int = 1,
        acronym: str = "VER",
        team_colour: str | None = "3671C6",
        team_name: str | None = "Red Bull Racing",
        headshot_url: str | None = None,
    ) -> Driver:
        return Driver(
            driver_number=number,
            full_name=f"Driver {acronym}",
            name_acronym=acronym,
            team_name=team_name,
            team_colour=team_colour,
            headshot_url=headshot_url,
        )

    return _make


@pytest.fixture
def make_lap() -> Callable[..., Lap]:
    def _make(
        driver_number: int,
        lap_number: int,
        duration: float | None,
        sectors: tuple[float | None, float | None, float | None] = (None, None, None),
        pit_out: bool = False,
    ) -> Lap:
        return Lap(
            driver_number=driver_number,
            lap_number=lap_number,
            lap_duration=duration,
            duration_sector_1=sectors[0],
            duration_sector_2=sectors[1],
            duration_sector_3=sectors[2],
            is_pit_out_lap=pit_out,
        )

    return _make


@pytest.fixture
def make_session() -> Callable[..., Session]:
    def _make(
        session_key: int = 100,
        session_type: str = "Race",
        start: datetime = datetime(2023, 3, 5, 15, tzinfo=UTC),
    ) -> Session:
        return Session(
            session_key=session_key,
            meeting_key=1,
            session_name=session_type,
            session_type=session_type,
            date_start=start,
            date_end=start,
            year=start.year,
        )

    return _make


@pytest.fixture
def drivers(make_driver: Callable[..., Driver]) -> list[Driver]:
    return [
        make_driver(1, "VER"),
        make_driver(11, "PER"),
        make_driver(44, "HAM", team_colour="27F4D2", team_name="Mercedes"),
    ]


@pytest.fixture
def driver_index(drivers: list[Driver]) -> dict[int, Driver]:
    return {driver.driver_number: driver for driver in drivers}
