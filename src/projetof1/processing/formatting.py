import re

from projetof1.domain.models import GapValue

SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
MISSING = "—"

DEFAULT_TEAM_COLOR = "#9B9BA5"
DEFAULT_COMPOUND_COLOR = "#8A8A93"
COMPOUND_COLORS = {
    "SOFT": "#DA291C",
    "MEDIUM": "#FFD12E",
    "HARD": "#F0F0EC",
    "INTERMEDIATE": "#43B02A",
    "WET": "#0067AD",
}

_HEX_COLOR = re.compile(r"#?([0-9A-Fa-f]{6})")


def format_lap_time(seconds: float | None) -> str:
    """Formata segundos como tempo de volta ou de prova.

    Exemplos: `83.456 → "1:23.456"`, `59.1 → "59.100"`,
    `6397.418 → "1:46:37.418"`.
    """
    if seconds is None or seconds < 0:
        return MISSING
    hours, rest = divmod(seconds, SECONDS_PER_HOUR)
    minutes, secs = divmod(rest, SECONDS_PER_MINUTE)
    if hours >= 1:
        return f"{int(hours)}:{int(minutes):02d}:{secs:06.3f}"
    if minutes >= 1:
        return f"{int(minutes)}:{secs:06.3f}"
    return f"{secs:.3f}"


def format_gap(gap: GapValue) -> str:
    """Formata o gap para o líder; textos da API (`+1 LAP`) passam inalterados."""
    if gap is None:
        return MISSING
    if isinstance(gap, str):
        return gap
    return f"+{gap:.3f}"


def format_seconds(seconds: float | None) -> str:
    """Formata uma duração curta em segundos (ex.: pit stop `2.4 → "2.4 s"`)."""
    if seconds is None:
        return MISSING
    return f"{seconds:.1f} s"


def team_color(colour: str | None) -> str:
    """Converte a cor da equipe da API (`3671C6`) em hex CSS (`#3671C6`)."""
    if colour:
        match = _HEX_COLOR.fullmatch(colour.strip())
        if match:
            return f"#{match.group(1).upper()}"
    return DEFAULT_TEAM_COLOR


def compound_color(compound: str | None) -> str:
    """Cor oficial do composto de pneu, com cor neutra para desconhecidos."""
    return COMPOUND_COLORS.get((compound or "").upper(), DEFAULT_COMPOUND_COLOR)
