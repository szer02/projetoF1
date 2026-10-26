from collections.abc import Iterable, Mapping

from projetof1.domain.models import Driver


def build_driver_index(drivers: Iterable[Driver]) -> dict[int, Driver]:
    """Indexa os pilotos por número; em duplicidade, a primeira ocorrência prevalece."""
    index: dict[int, Driver] = {}
    for driver in drivers:
        index.setdefault(driver.driver_number, driver)
    return index


def resolve_driver(index: Mapping[int, Driver], driver_number: int) -> Driver:
    """Retorna o piloto de `driver_number` ou um substituto genérico.

    A OpenF1 às vezes traz voltas ou resultados de um número ausente em
    `/drivers`; o substituto evita perder essas linhas no dashboard.
    """
    driver = index.get(driver_number)
    if driver is not None:
        return driver
    return Driver(
        driver_number=driver_number,
        full_name=f"Piloto #{driver_number}",
        name_acronym=str(driver_number),
    )
