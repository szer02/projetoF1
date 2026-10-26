"""Figuras Plotly do dashboard: funções puras, testáveis sem o Streamlit."""

from collections.abc import Sequence

import plotly.graph_objects as go

from projetof1.domain.models import FastestLapEntry, PaceSeries, StintBar
from projetof1.processing.formatting import (
    compound_color,
    format_lap_time,
    team_color,
)

FONT_FAMILY = "Titillium Web, Segoe UI, sans-serif"
GRID_COLOR = "rgba(255, 255, 255, 0.08)"
TRANSPARENT = "rgba(0, 0, 0, 0)"
EMPTY_MESSAGE = "Sem dados para esta sessão"
AXIS_PADDING_SECONDS = 0.4
BAR_HEIGHT_PX = 34
MIN_CHART_HEIGHT_PX = 320


def _apply_layout(
    fig: go.Figure, title: str, height: int = MIN_CHART_HEIGHT_PX
) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        title={"text": title, "x": 0, "font": {"size": 18}},
        font={"family": FONT_FAMILY},
        paper_bgcolor=TRANSPARENT,
        plot_bgcolor=TRANSPARENT,
        height=height,
        margin={"l": 10, "r": 10, "t": 60, "b": 10},
        hoverlabel={"font": {"family": FONT_FAMILY}},
        legend={"orientation": "h", "y": -0.15},
    )
    fig.update_xaxes(gridcolor=GRID_COLOR, zeroline=False)
    fig.update_yaxes(gridcolor=GRID_COLOR, zeroline=False)
    return fig


def _empty(title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=EMPTY_MESSAGE,
        showarrow=False,
        font={"size": 16},
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return _apply_layout(fig, title)


def _bar_label(entry: FastestLapEntry, show_lap: bool) -> str:
    label = f"P{entry.position}  {entry.driver.name_acronym}"
    return f"{label} · V{entry.lap_number}" if show_lap else label


def fastest_laps_bar(
    entries: Sequence[FastestLapEntry],
    title: str = "Voltas mais rápidas",
    show_lap_in_label: bool = False,
) -> go.Figure:
    """Barras horizontais com voltas rápidas, na cor da equipe.

    Args:
        entries: Ranking já ordenado (mais rápida primeiro).
        title: Título do gráfico.
        show_lap_in_label: Inclui o número da volta no rótulo, útil quando o
            mesmo piloto aparece mais de uma vez.
    """
    if not entries:
        return _empty(title)

    ordered = list(reversed(entries))  # a mais rápida fica no topo
    durations = [entry.lap_duration for entry in ordered]
    fig = go.Figure(
        go.Bar(
            x=durations,
            y=[_bar_label(entry, show_lap_in_label) for entry in ordered],
            orientation="h",
            marker={
                "color": [team_color(entry.driver.team_colour) for entry in ordered]
            },
            text=[format_lap_time(entry.lap_duration) for entry in ordered],
            textposition="outside",
            customdata=[
                [
                    entry.driver.full_name,
                    entry.driver.team_name or "—",
                    entry.lap_number,
                    f"+{entry.gap_to_fastest:.3f}",
                ]
                for entry in ordered
            ],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>%{customdata[1]}<br>"
                "Volta %{customdata[2]}: %{text}<br>Gap: %{customdata[3]}<extra></extra>"
            ),
        )
    )
    fig.update_xaxes(
        range=[
            min(durations) - AXIS_PADDING_SECONDS,
            max(durations) + AXIS_PADDING_SECONDS * 2,
        ],
        title="Tempo de volta (s)",
    )
    height = max(MIN_CHART_HEIGHT_PX, BAR_HEIGHT_PX * len(entries) + 100)
    return _apply_layout(fig, title, height)


def pace_lines(series: Sequence[PaceSeries]) -> go.Figure:
    """Linhas de tempo por volta; companheiros de equipe usam traço pontilhado."""
    title = "Ritmo volta a volta"
    if not series:
        return _empty(title)

    fig = go.Figure()
    used_colors: set[str] = set()
    for item in series:
        color = team_color(item.driver.team_colour)
        dash = "dot" if color in used_colors else "solid"
        used_colors.add(color)
        fig.add_trace(
            go.Scatter(
                x=list(item.lap_numbers),
                y=list(item.lap_durations),
                mode="lines+markers",
                name=item.driver.name_acronym,
                line={"color": color, "dash": dash, "width": 2},
                marker={"size": 5},
                text=[format_lap_time(duration) for duration in item.lap_durations],
                hovertemplate=(
                    f"<b>{item.driver.name_acronym}</b><br>"
                    "Volta %{x}: %{text}<extra></extra>"
                ),
            )
        )
    fig.update_xaxes(title="Volta")
    fig.update_yaxes(title="Tempo de volta (s)")
    return _apply_layout(fig, title, height=460)


def stint_timeline(bars: Sequence[StintBar]) -> go.Figure:
    """Linha do tempo de pneus: uma faixa por piloto, colorida por composto."""
    title = "Estratégia de pneus"
    if not bars:
        return _empty(title)

    drivers: list[str] = []
    for bar in bars:
        if bar.driver.name_acronym not in drivers:
            drivers.append(bar.driver.name_acronym)

    fig = go.Figure()
    compounds: list[str] = []
    for bar in bars:
        if bar.compound not in compounds:
            compounds.append(bar.compound)

    for compound in compounds:
        selected = [bar for bar in bars if bar.compound == compound]
        fig.add_trace(
            go.Bar(
                x=[bar.lap_end - bar.lap_start + 1 for bar in selected],
                base=[bar.lap_start - 1 for bar in selected],
                y=[bar.driver.name_acronym for bar in selected],
                orientation="h",
                name=compound.title(),
                marker={
                    "color": compound_color(compound),
                    "line": {"color": "#15151E", "width": 2},
                },
                customdata=[
                    [
                        bar.lap_start,
                        bar.lap_end,
                        bar.tyre_age_at_start
                        if bar.tyre_age_at_start is not None
                        else "—",
                    ]
                    for bar in selected
                ],
                hovertemplate=(
                    f"<b>%{{y}}</b> · {compound.title()}<br>"
                    "Voltas %{customdata[0]} a %{customdata[1]}<br>"
                    "Idade inicial: %{customdata[2]}<extra></extra>"
                ),
            )
        )
    fig.update_layout(barmode="overlay")
    fig.update_xaxes(title="Volta")
    fig.update_yaxes(categoryorder="array", categoryarray=list(reversed(drivers)))
    height = max(MIN_CHART_HEIGHT_PX, 28 * len(drivers) + 120)
    return _apply_layout(fig, title, height)
