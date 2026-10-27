"""Blocos visuais do dashboard.

As funções `*_rows` e `podium_card_html` são puras (testáveis); as `render_*`
desenham no Streamlit. Textos vindos da API são escapados antes de entrar no HTML.
"""

from collections.abc import Sequence
from datetime import datetime
from html import escape
from typing import Any

import streamlit as st

from projetof1.domain.models import (
    BestSectors,
    ClassificationEntry,
    FastestLapEntry,
    Meeting,
    PitEntry,
    Session,
    WeatherSummary,
)
from projetof1.processing.formatting import (
    MISSING,
    format_gap,
    format_lap_time,
    format_seconds,
    team_color,
)
from projetof1.processing.results import STATUS_FINISHED, last_known

PODIUM_SIZE = 3
PODIUM_LABELS = {1: "1º", 2: "2º", 3: "3º"}
FASTEST_SECTOR_MARK = "🟣"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Titillium+Web:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Titillium Web', 'Segoe UI', sans-serif; }
.f1-header { border-left: 6px solid #E10600; padding: 0.2rem 0 0.2rem 1rem; margin-bottom: 1rem; }
.f1-header h1 { margin: 0; font-size: 2.1rem; font-weight: 700; letter-spacing: 0.02em; }
.f1-header p { margin: 0; color: #B8B8C2; font-size: 1rem; }
.f1-card { background: #1F1F2B; border-radius: 14px; padding: 1rem; text-align: center;
           border-top: 5px solid var(--team); box-shadow: 0 6px 18px rgba(0,0,0,0.35);
           margin-bottom: 1.5rem; }
.f1-card img { width: 96px; height: 96px; object-fit: cover; border-radius: 50%;
               background: #2A2A38; border: 3px solid var(--team); }
.f1-card .pos { font-size: 1.6rem; font-weight: 700; color: #E10600; }
.f1-card .name { font-size: 1.15rem; font-weight: 700; margin-top: 0.4rem; }
.f1-card .team { color: var(--team); font-weight: 600; font-size: 0.9rem; }
.f1-card .time { font-family: monospace; font-size: 1.05rem; margin-top: 0.3rem; }
.f1-footer { color: #8A8A93; font-size: 0.8rem; margin-top: 2rem; }
</style>
"""


def default_meeting_index(meetings: Sequence[Meeting], now: datetime) -> int:
    """Índice do GP mais recente que já começou (ou o primeiro, se nenhum começou)."""
    started = [i for i, meeting in enumerate(meetings) if meeting.date_start <= now]
    return started[-1] if started else 0


def default_session_index(sessions: Sequence[Session], now: datetime) -> int:
    """Índice da corrida mais recente já iniciada; senão, da última sessão iniciada."""
    started = [i for i, session in enumerate(sessions) if session.date_start <= now]
    races = [i for i in started if sessions[i].is_race]
    if races:
        return races[-1]
    return started[-1] if started else 0


def inject_css() -> None:
    """Aplica o estilo visual do dashboard."""
    st.markdown(CSS, unsafe_allow_html=True)


def render_header(meeting: Meeting, session: Session) -> None:
    """Cabeçalho com GP, circuito, sessão e data."""
    subtitle = (
        f"{escape(meeting.circuit_short_name)} · {escape(meeting.country_name)} · "
        f"{escape(session.session_name)} · {session.date_start:%d/%m/%Y}"
    )
    st.markdown(
        f'<div class="f1-header"><h1>{escape(meeting.meeting_name)}</h1>'
        f"<p>{subtitle}</p></div>",
        unsafe_allow_html=True,
    )


def render_weather(weather: WeatherSummary | None) -> None:
    """Métricas de clima da sessão."""
    if weather is None:
        st.caption("Sem dados de clima para esta sessão.")
        return
    air, track, humidity, rain = st.columns(4)
    air.metric(
        "Ar", _celsius(weather.air_last), help=_range(weather.air_min, weather.air_max)
    )
    track.metric(
        "Pista",
        _celsius(weather.track_last),
        help=_range(weather.track_min, weather.track_max),
    )
    humidity.metric(
        "Umidade",
        MISSING if weather.humidity_last is None else f"{weather.humidity_last:.0f}%",
    )
    rain.metric("Chuva", "Sim" if weather.rained else "Não")


def _celsius(value: float | None) -> str:
    return MISSING if value is None else f"{value:.1f} °C"


def _range(low: float | None, high: float | None) -> str:
    return f"Mín. {_celsius(low)} · Máx. {_celsius(high)}"


def result_time_label(entry: ClassificationEntry) -> str:
    """Tempo do líder ou gap dos demais; status quando não terminou."""
    if entry.status != STATUS_FINISHED:
        return entry.status
    if entry.position == 1:
        return format_lap_time(last_known(entry.durations))
    return format_gap(last_known(entry.gaps))


def podium_card_html(entry: ClassificationEntry) -> str:
    """HTML do card de um piloto do pódio."""
    driver = entry.driver
    color = team_color(driver.team_colour)
    image = (
        f'<img src="{escape(driver.headshot_url)}" alt="{escape(driver.name_acronym)}">'
        if driver.headshot_url
        else ""
    )
    label = PODIUM_LABELS.get(entry.position or 0, MISSING)
    return (
        f'<div class="f1-card" style="--team: {color}">'
        f'<div class="pos">{label}</div>{image}'
        f'<div class="name">{escape(driver.full_name)}</div>'
        f'<div class="team">{escape(driver.team_name or MISSING)}</div>'
        f'<div class="time">{escape(result_time_label(entry))}</div></div>'
    )


def render_podium(classification: Sequence[ClassificationEntry]) -> None:
    """Três cards do pódio, na ordem 2º · 1º · 3º."""
    podium = [entry for entry in classification if entry.position in PODIUM_LABELS]
    if len(podium) < PODIUM_SIZE:
        return
    by_position = {entry.position: entry for entry in podium}
    columns = st.columns(PODIUM_SIZE)
    for column, position in zip(columns, (2, 1, 3), strict=True):
        column.markdown(podium_card_html(by_position[position]), unsafe_allow_html=True)


def classification_rows(entries: Sequence[ClassificationEntry]) -> list[dict[str, Any]]:
    """Linhas da tabela de classificação.

    Colunas numéricas usam `None` (célula vazia) quando ausentes, para manter um
    único tipo por coluna.
    """
    return [
        {
            "Pos.": entry.position,
            "Piloto": entry.driver.full_name,
            "Equipe": entry.driver.team_name or MISSING,
            "Voltas": entry.number_of_laps,
            "Tempo / Gap": result_time_label(entry),
            "Status": entry.status,
        }
        for entry in entries
    ]


def fastest_lap_rows(
    entries: Sequence[FastestLapEntry], sectors: Sequence[BestSectors]
) -> list[dict[str, Any]]:
    """Linhas da tabela de voltas mais rápidas, com a volta ideal do piloto.

    O setor mais rápido entre as voltas exibidas recebe o marcador roxo, como
    na transmissão oficial.
    """
    ideal = {item.driver_number: item.ideal_lap for item in sectors}
    best = best_sector_values(entries)
    rows: list[dict[str, Any]] = []
    for entry in entries:
        row: dict[str, Any] = {
            "Pos.": entry.position,
            "Piloto": entry.driver.full_name,
            "Equipe": entry.driver.team_name or MISSING,
            "Volta": entry.lap_number,
            "Tempo": format_lap_time(entry.lap_duration),
            "Gap": f"+{entry.gap_to_fastest:.3f}",
        }
        for column, value in (
            ("S1", entry.sector_1),
            ("S2", entry.sector_2),
            ("S3", entry.sector_3),
        ):
            text = format_lap_time(value)
            row[column] = (
                f"{FASTEST_SECTOR_MARK} {text}" if best.get(column) == text else text
            )
        row["Volta ideal"] = format_lap_time(ideal.get(entry.driver.driver_number))
        rows.append(row)
    return rows


def best_sector_values(entries: Sequence[FastestLapEntry]) -> dict[str, str]:
    """Melhor S1, S2 e S3 entre as voltas exibidas, já formatados (para destaque)."""
    best: dict[str, str] = {}
    for column, values in (
        ("S1", [entry.sector_1 for entry in entries]),
        ("S2", [entry.sector_2 for entry in entries]),
        ("S3", [entry.sector_3 for entry in entries]),
    ):
        known = [value for value in values if value is not None]
        if known:
            best[column] = format_lap_time(min(known))
    return best


def pit_rows(entries: Sequence[PitEntry]) -> list[dict[str, Any]]:
    """Linhas da tabela de pit stops."""
    return [
        {
            "Volta": entry.lap_number,
            "Piloto": entry.driver.full_name,
            "Equipe": entry.driver.team_name or MISSING,
            "Pit lane": format_seconds(entry.lane_duration),
            "Parado": format_seconds(entry.stop_duration),
        }
        for entry in entries
    ]


def render_footer() -> None:
    """Créditos da fonte de dados."""
    st.markdown(
        '<div class="f1-footer">Dados: <a href="https://openf1.org" target="_blank">OpenF1 API</a>'
        " · Projeto não oficial, sem vínculo com a Formula 1.</div>",
        unsafe_allow_html=True,
    )
