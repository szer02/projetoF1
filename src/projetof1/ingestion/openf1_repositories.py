"""Implementações dos repositórios de `domain` sobre a OpenF1 API."""

from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel, ValidationError

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
from projetof1.ingestion.http_client import HttpClient, QueryParams
from projetof1.utils.logger import get_logger

logger = get_logger(__name__)


def parse_items[M: BaseModel](
    items: Iterable[dict[str, Any]], model: type[M], endpoint: str
) -> list[M]:
    """Valida cada item com `model`; itens inválidos são ignorados e contados.

    Args:
        items: Registros brutos da API.
        model: Modelo pydantic de destino.
        endpoint: Nome do endpoint, usado apenas no log.

    Returns:
        Itens válidos, na ordem original.
    """
    parsed: list[M] = []
    invalid = 0
    for item in items:
        try:
            parsed.append(model.model_validate(item))
        except ValidationError:
            invalid += 1
    if invalid:
        logger.warning(
            "itens inválidos ignorados: endpoint=%s invalidos=%d validos=%d",
            endpoint,
            invalid,
            len(parsed),
        )
    return parsed


class _OpenF1Source:
    """Base comum: consulta um endpoint e valida o resultado."""

    def __init__(self, client: HttpClient) -> None:
        self._client = client

    def _fetch[M: BaseModel](
        self, endpoint: str, model: type[M], params: QueryParams
    ) -> list[M]:
        return parse_items(self._client.get(endpoint, params), model, endpoint)


class OpenF1MeetingRepository(_OpenF1Source, MeetingRepository):
    """Meetings via `/meetings`."""

    def fetch(self, year: int) -> list[Meeting]:
        """Retorna os meetings de `year`."""
        return self._fetch("meetings", Meeting, {"year": year})


class OpenF1SessionRepository(_OpenF1Source, SessionRepository):
    """Sessões via `/sessions`."""

    def fetch(self, meeting_key: int) -> list[Session]:
        """Retorna as sessões de `meeting_key`."""
        return self._fetch("sessions", Session, {"meeting_key": meeting_key})


class OpenF1DriverRepository(_OpenF1Source, DriverRepository):
    """Pilotos via `/drivers`."""

    def fetch(self, session_key: int) -> list[Driver]:
        """Retorna os pilotos de `session_key`."""
        return self._fetch("drivers", Driver, {"session_key": session_key})


class OpenF1LapRepository(_OpenF1Source, LapRepository):
    """Voltas via `/laps`."""

    def fetch(self, session_key: int, driver_number: int | None = None) -> list[Lap]:
        """Retorna as voltas da sessão, opcionalmente de um único piloto."""
        params: dict[str, int] = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number
        return self._fetch("laps", Lap, params)


class OpenF1StintRepository(_OpenF1Source, StintRepository):
    """Stints via `/stints`."""

    def fetch(self, session_key: int) -> list[Stint]:
        """Retorna os stints de `session_key`."""
        return self._fetch("stints", Stint, {"session_key": session_key})


class OpenF1PitRepository(_OpenF1Source, PitRepository):
    """Pit stops via `/pit`."""

    def fetch(self, session_key: int) -> list[PitStop]:
        """Retorna os pit stops de `session_key`."""
        return self._fetch("pit", PitStop, {"session_key": session_key})


class OpenF1SessionResultRepository(_OpenF1Source, SessionResultRepository):
    """Resultado via `/session_result`."""

    def fetch(self, session_key: int) -> list[SessionResult]:
        """Retorna o resultado de `session_key`."""
        return self._fetch(
            "session_result", SessionResult, {"session_key": session_key}
        )


class OpenF1WeatherRepository(_OpenF1Source, WeatherRepository):
    """Clima via `/weather`."""

    def fetch(self, session_key: int) -> list[Weather]:
        """Retorna as amostras de clima de `session_key`."""
        return self._fetch("weather", Weather, {"session_key": session_key})


def build_repositories(client: HttpClient) -> F1Repositories:
    """Cria o conjunto completo de repositórios OpenF1 sobre `client`."""
    return F1Repositories(
        meetings=OpenF1MeetingRepository(client),
        sessions=OpenF1SessionRepository(client),
        drivers=OpenF1DriverRepository(client),
        laps=OpenF1LapRepository(client),
        stints=OpenF1StintRepository(client),
        pits=OpenF1PitRepository(client),
        results=OpenF1SessionResultRepository(client),
        weather=OpenF1WeatherRepository(client),
    )
