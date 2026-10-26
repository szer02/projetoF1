import logging
from collections.abc import Iterator

import pytest

from projetof1.utils.logger import configure_logging, get_logger


@pytest.fixture(autouse=True)
def restore_root_logger() -> Iterator[None]:
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    yield
    root.handlers[:] = handlers
    root.setLevel(level)


def test_get_logger_returns_named_logger() -> None:
    assert get_logger("projetof1.teste").name == "projetof1.teste"


def test_configure_logging_is_idempotent_and_sets_level() -> None:
    configure_logging("DEBUG")
    configure_logging("WARNING")

    root = logging.getLogger()
    assert len(root.handlers) == 1
    assert root.level == logging.WARNING
