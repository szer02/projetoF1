"""Modelos de domínio: payloads validados da OpenF1 e projeções para o dashboard."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

type GapValue = float | str | None
"""Gap para o líder: segundos, texto da API (ex.: `+1 LAP`) ou ausente."""


class OpenF1Model(BaseModel):
    """Base dos payloads da OpenF1: imutável e tolerante a campos extras."""

    model_config = ConfigDict(extra="ignore", frozen=True)


class Meeting(OpenF1Model):
    """Fim de semana de GP ou teste."""

    meeting_key: int
    meeting_name: str
    country_name: str
    circuit_short_name: str
    year: int
    date_start: datetime
    is_cancelled: bool = False


class Session(OpenF1Model):
    """Sessão de um meeting (treino, classificação, sprint ou corrida)."""

    session_key: int
    meeting_key: int
    session_name: str
    session_type: str
    date_start: datetime
    date_end: datetime
    year: int
    is_cancelled: bool = False

    @property
    def is_race(self) -> bool:
        """Indica se a sessão é corrida ou sprint (tem pit stops estratégicos)."""
        return self.session_type == "Race"


class Driver(OpenF1Model):
    """Piloto inscrito em uma sessão."""

    driver_number: int
    full_name: str
    name_acronym: str
    team_name: str | None = None
    team_colour: str | None = None
    headshot_url: str | None = None


class Lap(OpenF1Model):
    """Volta de um piloto."""

    driver_number: int
    lap_number: int
    lap_duration: float | None = None
    duration_sector_1: float | None = None
    duration_sector_2: float | None = None
    duration_sector_3: float | None = None
    i1_speed: int | None = None
    i2_speed: int | None = None
    st_speed: int | None = None
    is_pit_out_lap: bool | None = None


class Stint(OpenF1Model):
    """Período contínuo de um piloto com o mesmo jogo de pneus."""

    driver_number: int
    stint_number: int
    compound: str | None = None
    lap_start: int | None = None
    lap_end: int | None = None
    tyre_age_at_start: int | None = None


class PitStop(OpenF1Model):
    """Passagem pelo pit lane."""

    driver_number: int
    lap_number: int
    lane_duration: float | None = None
    stop_duration: float | None = None


class SessionResult(OpenF1Model):
    """Resultado final de um piloto na sessão.

    `duration` e `gap_to_leader` são sempre listas: um elemento na corrida e nos
    treinos, três (Q1, Q2, Q3) na classificação; vazias quando ausentes.
    """

    driver_number: int
    position: int | None = None
    duration: list[float | None] = []
    gap_to_leader: list[GapValue] = []
    number_of_laps: int | None = None
    dnf: bool = False
    dns: bool = False
    dsq: bool = False

    @field_validator("duration", "gap_to_leader", mode="before")
    @classmethod
    def _as_list(cls, value: Any) -> list[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]


class Weather(OpenF1Model):
    """Amostra de clima na pista (aproximadamente uma por minuto)."""

    date: datetime
    air_temperature: float | None = None
    track_temperature: float | None = None
    humidity: float | None = None
    rainfall: float | None = None
    wind_speed: float | None = None
    wind_direction: int | None = None


# ---------------------------------------------------------------- Projeções


@dataclass(frozen=True, slots=True)
class FastestLapEntry:
    """Melhor volta válida de um piloto, posicionada no ranking da sessão."""

    position: int
    driver: Driver
    lap_number: int
    lap_duration: float
    sector_1: float | None
    sector_2: float | None
    sector_3: float | None
    gap_to_fastest: float


@dataclass(frozen=True, slots=True)
class PaceSeries:
    """Tempos de volta representativos de um piloto, em ordem de volta."""

    driver: Driver
    lap_numbers: tuple[int, ...]
    lap_durations: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class BestSectors:
    """Melhor tempo de cada setor de um piloto e a volta ideal resultante."""

    driver_number: int
    sector_1: float | None
    sector_2: float | None
    sector_3: float | None

    @property
    def ideal_lap(self) -> float | None:
        """Soma dos melhores setores, quando os três existem."""
        if self.sector_1 is None or self.sector_2 is None or self.sector_3 is None:
            return None
        return round(self.sector_1 + self.sector_2 + self.sector_3, 3)


@dataclass(frozen=True, slots=True)
class StintBar:
    """Stint pronto para a linha do tempo de estratégia."""

    driver: Driver
    stint_number: int
    compound: str
    lap_start: int
    lap_end: int
    tyre_age_at_start: int | None


@dataclass(frozen=True, slots=True)
class PitEntry:
    """Pit stop pronto para exibição."""

    driver: Driver
    lap_number: int
    lane_duration: float | None
    stop_duration: float | None


@dataclass(frozen=True, slots=True)
class ClassificationEntry:
    """Linha da classificação final, com o piloto resolvido."""

    position: int | None
    driver: Driver
    durations: tuple[float | None, ...]
    gaps: tuple[GapValue, ...]
    number_of_laps: int | None
    status: str


@dataclass(frozen=True, slots=True)
class WeatherSummary:
    """Resumo do clima da sessão."""

    air_min: float | None
    air_max: float | None
    air_last: float | None
    track_min: float | None
    track_max: float | None
    track_last: float | None
    humidity_last: float | None
    rained: bool
    samples: int


@dataclass(frozen=True, slots=True)
class SessionOverview:
    """Tudo o que a tela de uma sessão precisa exibir."""

    session: Session
    drivers: tuple[Driver, ...]
    classification: tuple[ClassificationEntry, ...]
    fastest_laps: tuple[FastestLapEntry, ...]
    """Melhor volta de cada piloto (um piloto por linha)."""
    fastest_laps_overall: tuple[FastestLapEntry, ...]
    """Voltas mais rápidas da sessão; o mesmo piloto pode se repetir."""
    pace: tuple[PaceSeries, ...]
    best_sectors: tuple[BestSectors, ...]
    stints: tuple[StintBar, ...]
    pit_stops: tuple[PitEntry, ...]
    weather: WeatherSummary | None
