import time
from collections.abc import Callable, Mapping
from types import TracebackType
from typing import Any, Self

import httpx

from projetof1.domain.repositories import DataSourceError
from projetof1.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_SECONDS = 1.0
RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})
NO_RESULTS_STATUS = 404
"""A OpenF1 responde 404 (`{"detail": "No results found."}`) a consultas vazias."""

type QueryParams = Mapping[str, str | int]


class OpenF1ApiError(DataSourceError):
    """Falha definitiva ao consultar a OpenF1 API."""


class HttpClient:
    """Cliente HTTP da OpenF1 com timeout explícito e retry com backoff.

    Só repete em erros transitórios (timeout, falha de transporte, 429 e 5xx).
    Demais erros HTTP falham na primeira tentativa.
    """

    def __init__(
        self,
        base_url: str,
        timeout: float,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
        sleep: Callable[[float], None] = time.sleep,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        """Cria o cliente.

        Args:
            base_url: URL base da API (ex.: `https://api.openf1.org/v1`).
            timeout: Timeout de cada requisição, em segundos.
            max_retries: Número máximo de tentativas por requisição.
            backoff_seconds: Espera antes da 2ª tentativa; dobra a cada nova.
            sleep: Função de espera, injetável para testes.
            transport: Transporte httpx alternativo, usado nos testes.
        """
        if max_retries < 1:
            msg = "max_retries deve ser maior ou igual a 1"
            raise ValueError(msg)
        self._max_retries = max_retries
        self._backoff_seconds = backoff_seconds
        self._sleep = sleep
        self._client = httpx.Client(
            base_url=f"{base_url.rstrip('/')}/", timeout=timeout, transport=transport
        )

    def get(
        self, endpoint: str, params: QueryParams | None = None
    ) -> list[dict[str, Any]]:
        """Consulta um endpoint e retorna a lista de registros.

        Args:
            endpoint: Nome do endpoint, sem barra (ex.: `laps`).
            params: Filtros da query string.

        Returns:
            Registros retornados; lista vazia quando a API não encontra dados.

        Raises:
            OpenF1ApiError: Em erro HTTP não transitório, payload inválido ou
                após esgotar as tentativas.
        """
        last_error: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                response = self._client.get(endpoint, params=params)
            except httpx.TransportError as exc:
                last_error = exc
                logger.warning(
                    "falha de transporte: endpoint=%s tentativa=%d/%d erro=%s",
                    endpoint,
                    attempt,
                    self._max_retries,
                    type(exc).__name__,
                )
            else:
                if response.status_code not in RETRYABLE_STATUS:
                    return self._parse(endpoint, response)
                last_error = httpx.HTTPStatusError(
                    f"HTTP {response.status_code}",
                    request=response.request,
                    response=response,
                )
                logger.warning(
                    "erro transitório: endpoint=%s status=%d tentativa=%d/%d",
                    endpoint,
                    response.status_code,
                    attempt,
                    self._max_retries,
                )
            if attempt < self._max_retries:
                self._sleep(self._backoff_seconds * 2 ** (attempt - 1))

        msg = f"OpenF1 indisponível após {self._max_retries} tentativas: endpoint={endpoint}"
        raise OpenF1ApiError(msg) from last_error

    @staticmethod
    def _parse(endpoint: str, response: httpx.Response) -> list[dict[str, Any]]:
        if response.status_code == NO_RESULTS_STATUS:
            return []
        if response.is_error:
            msg = f"OpenF1 respondeu HTTP {response.status_code}: endpoint={endpoint}"
            raise OpenF1ApiError(msg)
        try:
            payload = response.json()
        except ValueError as exc:
            msg = f"resposta não é JSON: endpoint={endpoint}"
            raise OpenF1ApiError(msg) from exc
        if not isinstance(payload, list):
            msg = f"resposta inesperada (esperava lista): endpoint={endpoint}"
            raise OpenF1ApiError(msg)
        return [item for item in payload if isinstance(item, dict)]

    def close(self) -> None:
        """Fecha as conexões abertas."""
        self._client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
