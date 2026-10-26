from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from statistics import median

from projetof1.domain.models import (
    BestSectors,
    Driver,
    FastestLapEntry,
    Lap,
    PaceSeries,
)
from projetof1.processing.drivers import resolve_driver

OUTLIER_FACTOR = 1.07
"""Voltas acima de 107% da mediana do piloto (safety car, tráfego) saem do ritmo."""


def filter_valid_laps(laps: Iterable[Lap]) -> list[Lap]:
    """Mantém apenas voltas cronometradas que não são de saída do pit."""
    return [
        lap
        for lap in laps
        if lap.lap_duration is not None
        and lap.lap_duration > 0
        and not lap.is_pit_out_lap
    ]


def _ranking_key(lap: Lap) -> tuple[float, int, int]:
    # Empates de tempo: vence a volta mais antiga e, depois, o menor número.
    return (lap.lap_duration or 0.0, lap.lap_number, lap.driver_number)


def _check_n(n: int) -> None:
    if n < 1:
        msg = "n deve ser maior ou igual a 1"
        raise ValueError(msg)


def _to_entries(
    ranked: Sequence[Lap], drivers: Mapping[int, Driver]
) -> list[FastestLapEntry]:
    if not ranked:
        return []
    fastest = ranked[0].lap_duration or 0.0
    return [
        FastestLapEntry(
            position=position,
            driver=resolve_driver(drivers, lap.driver_number),
            lap_number=lap.lap_number,
            lap_duration=lap.lap_duration or 0.0,
            sector_1=lap.duration_sector_1,
            sector_2=lap.duration_sector_2,
            sector_3=lap.duration_sector_3,
            gap_to_fastest=round((lap.lap_duration or 0.0) - fastest, 3),
        )
        for position, lap in enumerate(ranked, start=1)
    ]


def compute_top_n_laps(
    laps: Iterable[Lap], drivers: Mapping[int, Driver], n: int
) -> list[FastestLapEntry]:
    """Ranqueia a melhor volta válida de cada piloto (um piloto por linha).

    Empates de tempo são desfeitos pela volta mais antiga e, depois, pelo
    número do piloto, de modo que o resultado é determinístico.

    Args:
        laps: Voltas da sessão.
        drivers: Índice de pilotos por número.
        n: Quantidade máxima de pilotos no ranking.

    Returns:
        Até `n` entradas, da volta mais rápida para a mais lenta.

    Raises:
        ValueError: Se `n` for menor que 1.
    """
    _check_n(n)
    best: dict[int, Lap] = {}
    for lap in filter_valid_laps(laps):
        current = best.get(lap.driver_number)
        if current is None or _ranking_key(lap) < _ranking_key(current):
            best[lap.driver_number] = lap
    return _to_entries(sorted(best.values(), key=_ranking_key)[:n], drivers)


def compute_top_n_laps_overall(
    laps: Iterable[Lap], drivers: Mapping[int, Driver], n: int
) -> list[FastestLapEntry]:
    """Ranqueia as voltas válidas mais rápidas da sessão, de qualquer piloto.

    Diferente de `compute_top_n_laps`, o mesmo piloto pode aparecer mais de
    uma vez. Empates seguem o mesmo critério determinístico.

    Args:
        laps: Voltas da sessão.
        drivers: Índice de pilotos por número.
        n: Quantidade máxima de voltas no ranking.

    Returns:
        Até `n` entradas, da volta mais rápida para a mais lenta.

    Raises:
        ValueError: Se `n` for menor que 1.
    """
    _check_n(n)
    return _to_entries(sorted(filter_valid_laps(laps), key=_ranking_key)[:n], drivers)


def lap_time_series(
    laps: Iterable[Lap],
    drivers: Mapping[int, Driver],
    driver_numbers: Sequence[int] | None = None,
) -> list[PaceSeries]:
    """Monta a série de ritmo por piloto, sem voltas fora do padrão.

    Args:
        laps: Voltas da sessão.
        drivers: Índice de pilotos por número.
        driver_numbers: Pilotos e ordem desejados; quando omitido, todos os
            pilotos com voltas válidas, em ordem de número.

    Returns:
        Uma série por piloto com ao menos uma volta representativa.
    """
    by_driver: defaultdict[int, list[Lap]] = defaultdict(list)
    for lap in filter_valid_laps(laps):
        by_driver[lap.driver_number].append(lap)

    order = list(driver_numbers) if driver_numbers is not None else sorted(by_driver)
    series: list[PaceSeries] = []
    for number in order:
        driver_laps = by_driver.get(number)
        if not driver_laps:
            continue
        limit = median(lap.lap_duration or 0.0 for lap in driver_laps) * OUTLIER_FACTOR
        kept = sorted(
            (lap for lap in driver_laps if (lap.lap_duration or 0.0) <= limit),
            key=lambda lap: lap.lap_number,
        )
        series.append(
            PaceSeries(
                driver=resolve_driver(drivers, number),
                lap_numbers=tuple(lap.lap_number for lap in kept),
                lap_durations=tuple(lap.lap_duration or 0.0 for lap in kept),
            )
        )
    return series


def best_sectors(laps: Iterable[Lap]) -> list[BestSectors]:
    """Calcula o melhor tempo de cada setor por piloto, em voltas válidas."""
    sectors: defaultdict[int, list[list[float]]] = defaultdict(lambda: [[], [], []])
    for lap in filter_valid_laps(laps):
        values = (lap.duration_sector_1, lap.duration_sector_2, lap.duration_sector_3)
        for bucket, value in zip(sectors[lap.driver_number], values, strict=True):
            if value is not None and value > 0:
                bucket.append(value)

    return [
        BestSectors(
            driver_number=number,
            sector_1=min(s1, default=None),
            sector_2=min(s2, default=None),
            sector_3=min(s3, default=None),
        )
        for number, (s1, s2, s3) in sorted(sectors.items())
    ]
