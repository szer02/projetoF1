"""Contratos de acesso aos dados da F1; implementados em `ingestion/`."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

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


class DataSourceError(RuntimeError):
    """Falha ao obter dados da fonte externa (rede, HTTP ou payload inválido)."""


class MeetingRepository(ABC):
    """Fins de semana de GP por temporada."""

    @abstractmethod
    def fetch(self, year: int) -> list[Meeting]:
        """Retorna os meetings de `year`.

        Raises:
            DataSourceError: Se a fonte não puder ser consultada.
        """


class SessionRepository(ABC):
    """Sessões de um meeting."""

    @abstractmethod
    def fetch(self, meeting_key: int) -> list[Session]:
        """Retorna as sessões de `meeting_key`.

        Raises:
            DataSourceError: Se a fonte não puder ser consultada.
        """


class DriverRepository(ABC):
    """Pilotos de uma sessão."""

    @abstractmethod
    def fetch(self, session_key: int) -> list[Driver]:
        """Retorna os pilotos de `session_key`.

        Raises:
            DataSourceError: Se a fonte não puder ser consultada.
        """


class LapRepository(ABC):
    """Voltas de uma sessão."""

    @abstractmethod
    def fetch(self, session_key: int, driver_number: int | None = None) -> list[Lap]:
        """Retorna as voltas da sessão, opcionalmente de um único piloto.

        Raises:
            DataSourceError: Se a fonte não puder ser consultada.
        """


class StintRepository(ABC):
    """Stints de pneus de uma sessão."""

    @abstractmethod
    def fetch(self, session_key: int) -> list[Stint]:
        """Retorna os stints de `session_key`.

        Raises:
            DataSourceError: Se a fonte não puder ser consultada.
        """


class PitRepository(ABC):
    """Passagens pelo pit lane de uma sessão."""

    @abstractmethod
    def fetch(self, session_key: int) -> list[PitStop]:
        """Retorna os pit stops de `session_key`.

        Raises:
            DataSourceError: Se a fonte não puder ser consultada.
        """


class SessionResultRepository(ABC):
    """Resultado final de uma sessão."""

    @abstractmethod
    def fetch(self, session_key: int) -> list[SessionResult]:
        """Retorna o resultado de `session_key`.

        Raises:
            DataSourceError: Se a fonte não puder ser consultada.
        """


class WeatherRepository(ABC):
    """Amostras de clima de uma sessão."""

    @abstractmethod
    def fetch(self, session_key: int) -> list[Weather]:
        """Retorna as amostras de clima de `session_key`.

        Raises:
            DataSourceError: Se a fonte não puder ser consultada.
        """


@dataclass(frozen=True, slots=True)
class F1Repositories:
    """Conjunto de repositórios injetado no `F1DashboardService`."""

    meetings: MeetingRepository
    sessions: SessionRepository
    drivers: DriverRepository
    laps: LapRepository
    stints: StintRepository
    pits: PitRepository
    results: SessionResultRepository
    weather: WeatherRepository
