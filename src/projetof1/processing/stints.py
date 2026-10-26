from collections.abc import Iterable, Mapping, Sequence

from projetof1.domain.models import Driver, PitEntry, PitStop, Stint, StintBar
from projetof1.processing.drivers import resolve_driver

UNKNOWN_COMPOUND = "UNKNOWN"


def build_stint_timeline(
    stints: Iterable[Stint],
    drivers: Mapping[int, Driver],
    driver_order: Sequence[int] = (),
) -> list[StintBar]:
    """Converte os stints em barras para a linha do tempo de estratégia.

    Stints sem volta inicial são descartados; sem volta final, ocupam uma
    única volta. Pilotos em `driver_order` vêm primeiro, nessa ordem; os demais
    seguem por número.
    """
    position = {number: index for index, number in enumerate(driver_order)}
    bars = [
        StintBar(
            driver=resolve_driver(drivers, stint.driver_number),
            stint_number=stint.stint_number,
            compound=(stint.compound or UNKNOWN_COMPOUND).upper(),
            lap_start=stint.lap_start,
            lap_end=max(stint.lap_end or stint.lap_start, stint.lap_start),
            tyre_age_at_start=stint.tyre_age_at_start,
        )
        for stint in stints
        if stint.lap_start is not None
    ]
    return sorted(
        bars,
        key=lambda bar: (
            position.get(bar.driver.driver_number, len(position)),
            bar.driver.driver_number,
            bar.stint_number,
        ),
    )


def pit_summary(
    pits: Iterable[PitStop], drivers: Mapping[int, Driver]
) -> list[PitEntry]:
    """Lista os pit stops com tempo no pit lane, em ordem de volta."""
    entries = [
        PitEntry(
            driver=resolve_driver(drivers, pit.driver_number),
            lap_number=pit.lap_number,
            lane_duration=pit.lane_duration,
            stop_duration=pit.stop_duration,
        )
        for pit in pits
        if pit.lane_duration is not None
    ]
    return sorted(
        entries, key=lambda entry: (entry.lap_number, entry.driver.driver_number)
    )
