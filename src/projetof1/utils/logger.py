import logging
import sys

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    """Retorna o logger do módulo `name`, sem configurar handlers."""
    return logging.getLogger(name)


def configure_logging(level: str = "INFO") -> None:
    """Configura o handler único da aplicação.

    Deve ser chamado apenas no ponto de entrada. Substitui handlers existentes,
    então chamadas repetidas (por exemplo, a cada rerun do Streamlit) não
    duplicam a saída.

    Args:
        level: Nome do nível de log (`DEBUG`, `INFO`, `WARNING`...).
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT))
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
