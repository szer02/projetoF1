from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from projetof1.domain.models import Weather
from projetof1.processing.weather import summarize_weather

type LoadFixture = Callable[[str], list[dict[str, Any]]]


def test_summarize_weather_without_samples_returns_none() -> None:
    assert summarize_weather([]) is None


def test_summarize_weather_uses_chronological_order(load_fixture: LoadFixture) -> None:
    samples = [Weather.model_validate(item) for item in load_fixture("weather")]

    summary = summarize_weather(samples)

    assert summary is not None
    assert (summary.air_min, summary.air_max, summary.air_last) == (27.5, 28.0, 27.5)
    assert (summary.track_min, summary.track_max, summary.track_last) == (
        33.0,
        35.0,
        33.0,
    )
    assert summary.humidity_last == 40.0
    assert summary.rained is False
    assert summary.samples == 2


def test_summarize_weather_detects_rain_and_tolerates_missing_values() -> None:
    samples = [
        Weather(date=datetime(2023, 1, 1, 12, tzinfo=UTC), rainfall=0),
        Weather(date=datetime(2023, 1, 1, 12, 1, tzinfo=UTC), rainfall=1),
    ]

    summary = summarize_weather(samples)

    assert summary is not None
    assert summary.rained is True
    assert summary.air_last is None
    assert summary.track_min is None
