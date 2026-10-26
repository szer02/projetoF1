from collections.abc import Iterable, Mapping, Sequence

from projetof1.domain.models import ClassificationEntry, Driver, SessionResult
from projetof1.processing.drivers import resolve_driver

STATUS_FINISHED = "Classificado"
STATUS_DNF = "DNF"
STATUS_DNS = "DNS"
STATUS_DSQ = "DSQ"


def result_status(result: SessionResult) -> str:
    """Status do piloto; desclassificação prevalece sobre não largar e abandono."""
    if result.dsq:
        return STATUS_DSQ
    if result.dns:
        return STATUS_DNS
    if result.dnf:
        return STATUS_DNF
    return STATUS_FINISHED


def build_classification(
    results: Iterable[SessionResult], drivers: Mapping[int, Driver]
) -> list[ClassificationEntry]:
    """Monta a classificação ordenada por posição, com posições nulas no fim."""
    entries = [
        ClassificationEntry(
            position=result.position,
            driver=resolve_driver(drivers, result.driver_number),
            durations=tuple(result.duration),
            gaps=tuple(result.gap_to_leader),
            number_of_laps=result.number_of_laps,
            status=result_status(result),
        )
        for result in results
    ]
    return sorted(
        entries,
        key=lambda entry: (
            entry.position is None,
            entry.position or 0,
            entry.driver.driver_number,
        ),
    )


def last_known[T](values: Sequence[T | None]) -> T | None:
    """Último valor não nulo (na classificação, a melhor fase alcançada)."""
    for value in reversed(values):
        if value is not None:
            return value
    return None
