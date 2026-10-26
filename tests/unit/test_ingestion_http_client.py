from collections.abc import Callable

import httpx
import pytest

from projetof1.domain.repositories import DataSourceError
from projetof1.ingestion.http_client import HttpClient, OpenF1ApiError

BASE_URL = "https://api.test/v1"
type Handler = Callable[[httpx.Request], httpx.Response]


class FakeSleep:
    """Registra as esperas sem dormir de verdade."""

    def __init__(self) -> None:
        self.calls: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


def make_client(handler: Handler, sleep: FakeSleep, max_retries: int = 3) -> HttpClient:
    return HttpClient(
        BASE_URL,
        timeout=1.0,
        max_retries=max_retries,
        backoff_seconds=1.0,
        sleep=sleep,
        transport=httpx.MockTransport(handler),
    )


def sequence_handler(responses: list[httpx.Response | Exception]) -> Handler:
    """Devolve as respostas em ordem; exceções são levantadas."""
    pending = list(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        outcome = pending.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    return handler


def test_get_returns_records_and_sends_query_params() -> None:
    seen: list[httpx.URL] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url)
        return httpx.Response(200, json=[{"session_key": 9161}])

    client = make_client(handler, FakeSleep())

    assert client.get("laps", {"session_key": 9161, "driver_number": 1}) == [
        {"session_key": 9161}
    ]
    assert seen[0].path == "/v1/laps"
    assert dict(seen[0].params) == {"session_key": "9161", "driver_number": "1"}


def test_not_found_means_no_results() -> None:
    handler = sequence_handler(
        [httpx.Response(404, json={"detail": "No results found."})]
    )

    assert make_client(handler, FakeSleep()).get("pit", {"session_key": 1}) == []


def test_transient_status_is_retried_with_exponential_backoff() -> None:
    sleep = FakeSleep()
    handler = sequence_handler(
        [
            httpx.Response(429),
            httpx.Response(503),
            httpx.Response(200, json=[{"ok": 1}]),
        ]
    )

    assert make_client(handler, sleep).get("drivers") == [{"ok": 1}]
    assert sleep.calls == [1.0, 2.0]


def test_timeout_is_retried() -> None:
    sleep = FakeSleep()
    handler = sequence_handler(
        [httpx.ReadTimeout("lento"), httpx.Response(200, json=[])]
    )

    assert make_client(handler, sleep).get("weather") == []
    assert sleep.calls == [1.0]


def test_exhausted_retries_raise_chained_error() -> None:
    sleep = FakeSleep()
    handler = sequence_handler([httpx.Response(500)] * 3)

    with pytest.raises(OpenF1ApiError, match="3 tentativas") as error:
        make_client(handler, sleep).get("laps")

    assert isinstance(error.value, DataSourceError)
    assert isinstance(error.value.__cause__, httpx.HTTPStatusError)
    assert sleep.calls == [1.0, 2.0]  # não espera depois da última tentativa


def test_exhausted_transport_errors_raise() -> None:
    handler = sequence_handler([httpx.ConnectError("offline")] * 2)

    with pytest.raises(OpenF1ApiError) as error:
        make_client(handler, FakeSleep(), max_retries=2).get("laps")

    assert isinstance(error.value.__cause__, httpx.ConnectError)


def test_client_error_is_not_retried() -> None:
    sleep = FakeSleep()
    handler = sequence_handler([httpx.Response(400, json={"detail": "bad"})])

    with pytest.raises(OpenF1ApiError, match="HTTP 400"):
        make_client(handler, sleep).get("laps")
    assert sleep.calls == []


@pytest.mark.parametrize(
    "response",
    [
        pytest.param(httpx.Response(200, text="<html>"), id="nao-json"),
        pytest.param(httpx.Response(200, json={"detail": "x"}), id="nao-lista"),
    ],
)
def test_unexpected_payload_raises(response: httpx.Response) -> None:
    with pytest.raises(OpenF1ApiError, match="endpoint=laps"):
        make_client(sequence_handler([response]), FakeSleep()).get("laps")


def test_non_object_items_are_dropped() -> None:
    handler = sequence_handler([httpx.Response(200, json=[{"a": 1}, 2, "x"])])

    assert make_client(handler, FakeSleep()).get("laps") == [{"a": 1}]


def test_invalid_max_retries_is_rejected() -> None:
    with pytest.raises(ValueError, match="max_retries"):
        HttpClient(BASE_URL, timeout=1.0, max_retries=0)


def test_context_manager_closes_client() -> None:
    handler = sequence_handler([httpx.Response(200, json=[])])

    with make_client(handler, FakeSleep()) as client:
        client.get("laps")

    with pytest.raises(RuntimeError):
        client.get("laps")
