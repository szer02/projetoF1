import pytest

from projetof1.processing.formatting import (
    COMPOUND_COLORS,
    DEFAULT_COMPOUND_COLOR,
    DEFAULT_TEAM_COLOR,
    MISSING,
    compound_color,
    format_gap,
    format_lap_time,
    format_seconds,
    team_color,
)


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        pytest.param(83.456, "1:23.456", id="volta"),
        pytest.param(59.1, "59.100", id="menos-de-um-minuto"),
        pytest.param(60.0, "1:00.000", id="um-minuto-exato"),
        pytest.param(6397.418, "1:46:37.418", id="prova-com-horas"),
        pytest.param(0.0, "0.000", id="zero"),
        pytest.param(None, MISSING, id="ausente"),
        pytest.param(-1.0, MISSING, id="negativo"),
    ],
)
def test_format_lap_time(seconds: float | None, expected: str) -> None:
    assert format_lap_time(seconds) == expected


@pytest.mark.parametrize(
    ("gap", "expected"),
    [
        pytest.param(0.812, "+0.812", id="segundos"),
        pytest.param(0, "+0.000", id="lider"),
        pytest.param("+1 LAP", "+1 LAP", id="texto-da-api"),
        pytest.param(None, MISSING, id="ausente"),
    ],
)
def test_format_gap(gap: float | str | None, expected: str) -> None:
    assert format_gap(gap) == expected


@pytest.mark.parametrize(("seconds", "expected"), [(2.44, "2.4 s"), (None, MISSING)])
def test_format_seconds(seconds: float | None, expected: str) -> None:
    assert format_seconds(seconds) == expected


@pytest.mark.parametrize(
    ("colour", "expected"),
    [
        pytest.param("3671c6", "#3671C6", id="sem-cerquilha"),
        pytest.param("#27F4D2", "#27F4D2", id="com-cerquilha"),
        pytest.param(None, DEFAULT_TEAM_COLOR, id="ausente"),
        pytest.param("", DEFAULT_TEAM_COLOR, id="vazio"),
        pytest.param("red", DEFAULT_TEAM_COLOR, id="invalido"),
        pytest.param("3671C6'><script>", DEFAULT_TEAM_COLOR, id="injecao"),
    ],
)
def test_team_color(colour: str | None, expected: str) -> None:
    assert team_color(colour) == expected


@pytest.mark.parametrize(
    ("compound", "expected"),
    [
        ("SOFT", COMPOUND_COLORS["SOFT"]),
        ("intermediate", COMPOUND_COLORS["INTERMEDIATE"]),
        ("UNKNOWN", DEFAULT_COMPOUND_COLOR),
        (None, DEFAULT_COMPOUND_COLOR),
    ],
)
def test_compound_color(compound: str | None, expected: str) -> None:
    assert compound_color(compound) == expected
