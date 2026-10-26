from collections.abc import Iterable

from projetof1.domain.models import Weather, WeatherSummary


def summarize_weather(samples: Iterable[Weather]) -> WeatherSummary | None:
    """Resume o clima da sessão; retorna `None` quando não há amostras."""
    ordered = sorted(samples, key=lambda sample: sample.date)
    if not ordered:
        return None

    air = [s.air_temperature for s in ordered if s.air_temperature is not None]
    track = [s.track_temperature for s in ordered if s.track_temperature is not None]
    humidity = [s.humidity for s in ordered if s.humidity is not None]

    return WeatherSummary(
        air_min=min(air, default=None),
        air_max=max(air, default=None),
        air_last=air[-1] if air else None,
        track_min=min(track, default=None),
        track_max=max(track, default=None),
        track_last=track[-1] if track else None,
        humidity_last=humidity[-1] if humidity else None,
        rained=any((s.rainfall or 0) > 0 for s in ordered),
        samples=len(ordered),
    )
