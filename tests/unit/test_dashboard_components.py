from collections.abc import Callable
from datetime import UTC, datetime

import pytest

from projetof1.dashboard.components import (
    FASTEST_SECTOR_MARK,
    best_sector_values,
    classification_rows,
    default_meeting_index,
    default_session_index,
    fastest_lap_rows,
    pit_rows,
    podium_card_html,
    result_time_label,
)
from projetof1.domain.models import (
    BestSectors,
    ClassificationEntry,
    Driver,
    FastestLapEntry,
    Meeting,
    PitEntry,
    Session,
)

type MakeDriver = Callable[..., Driver]
NOW = datetime(2026, 10, 26, 12, tzinfo=UTC)


def meeting(key: int, month: int) -> Meeting:
    return Meeting(
        meeting_key=key,
        meeting_name=f"GP {key}",
        country_name="X",
        circuit_short_name="Y",
        year=2026,
        date_start=datetime(2026, month, 1, tzinfo=UTC),
    )


def entry(
    driver: Driver,
    position: int | None,
    durations: tuple[float | None, ...] = (),
    gaps: tuple[float | str | None, ...] = (),
    status: str = "Classificado",
) -> ClassificationEntry:
    return ClassificationEntry(position, driver, durations, gaps, 57, status)


def test_default_meeting_index_picks_latest_started() -> None:
    meetings = [meeting(1, 3), meeting(2, 10), meeting(3, 12)]

    assert default_meeting_index(meetings, NOW) == 1


def test_default_meeting_index_when_none_started() -> None:
    assert default_meeting_index([meeting(1, 12)], NOW) == 0


def test_default_session_index_prefers_latest_started_race(
    make_session: Callable[..., Session],
) -> None:
    sessions = [
        make_session(1, "Practice", datetime(2026, 10, 1, tzinfo=UTC)),
        make_session(2, "Race", datetime(2026, 10, 3, tzinfo=UTC)),
        make_session(3, "Practice", datetime(2026, 10, 4, tzinfo=UTC)),
        make_session(4, "Race", datetime(2026, 11, 1, tzinfo=UTC)),  # futura
    ]

    assert default_session_index(sessions, NOW) == 1


def test_default_session_index_without_race_uses_latest_started(
    make_session: Callable[..., Session],
) -> None:
    sessions = [
        make_session(1, "Practice", datetime(2026, 10, 1, tzinfo=UTC)),
        make_session(2, "Qualifying", datetime(2026, 10, 2, tzinfo=UTC)),
    ]

    assert default_session_index(sessions, NOW) == 1
    assert default_session_index(sessions, datetime(2026, 1, 1, tzinfo=UTC)) == 0


@pytest.mark.parametrize(
    ("position", "durations", "gaps", "status", "expected"),
    [
        pytest.param(
            1, (5628.113,), (0,), "Classificado", "1:33:48.113", id="lider-corrida"
        ),
        pytest.param(
            1,
            (92.3, 91.4, 90.9),
            (0.3, 0.0, 0.0),
            "Classificado",
            "1:30.900",
            id="pole",
        ),
        pytest.param(2, (5640.1,), (11.987,), "Classificado", "+11.987", id="gap"),
        pytest.param(5, (), ("+1 LAP",), "Classificado", "+1 LAP", id="retardatario"),
        pytest.param(None, (), (), "DNF", "DNF", id="abandono"),
    ],
)
def test_result_time_label(
    make_driver: MakeDriver,
    position: int | None,
    durations: tuple[float, ...],
    gaps: tuple[float | str, ...],
    status: str,
    expected: str,
) -> None:
    assert (
        result_time_label(entry(make_driver(), position, durations, gaps, status))
        == expected
    )


def test_podium_card_escapes_api_text(make_driver: MakeDriver) -> None:
    driver = make_driver(
        1,
        "<b>X</b>",
        team_name="<script>alert(1)</script>",
        headshot_url='x" onerror="y',
    )

    html = podium_card_html(entry(driver, 1, (90.0,), (0,)))

    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "x&quot; onerror=&quot;y" in html
    assert "--team: #3671C6" in html


def test_podium_card_without_headshot_has_no_image(make_driver: MakeDriver) -> None:
    assert "<img" not in podium_card_html(entry(make_driver(), 2, (), (1.0,)))


def test_classification_rows_keep_numeric_columns_typed(
    make_driver: MakeDriver,
) -> None:
    rows = classification_rows([entry(make_driver(), None, status="DNF")])

    assert rows[0]["Pos."] is None
    assert rows[0]["Status"] == "DNF"
    assert rows[0]["Tempo / Gap"] == "DNF"


def test_fastest_lap_rows_mark_best_sector_and_ideal_lap(
    make_driver: MakeDriver,
) -> None:
    ver, ham = make_driver(1, "VER"), make_driver(44, "HAM")
    entries = [
        FastestLapEntry(1, ver, 10, 95.0, 30.0, 35.1, 29.9, 0.0),
        FastestLapEntry(2, ham, 11, 95.2, 29.8, 35.2, 30.2, 0.2),
    ]
    sectors = [BestSectors(1, 30.0, 35.0, 29.9)]

    rows = fastest_lap_rows(entries, sectors)

    assert rows[0]["S1"] == "30.000"
    assert rows[1]["S1"] == f"{FASTEST_SECTOR_MARK} 29.800"
    assert rows[0]["S2"] == f"{FASTEST_SECTOR_MARK} 35.100"
    assert rows[0]["Volta ideal"] == "1:34.900"
    assert rows[1]["Volta ideal"] == "—"


def test_best_sector_values_ignores_missing(make_driver: MakeDriver) -> None:
    lap = FastestLapEntry(1, make_driver(), 3, 95.0, None, 35.0, None, 0.0)

    assert best_sector_values([lap]) == {"S2": "35.000"}


def test_pit_rows_format_durations(make_driver: MakeDriver) -> None:
    rows = pit_rows([PitEntry(make_driver(), 20, 21.93, None)])

    assert rows == [
        {
            "Volta": 20,
            "Piloto": "Driver VER",
            "Equipe": "Red Bull Racing",
            "Pit lane": "21.9 s",
            "Parado": "—",
        }
    ]
