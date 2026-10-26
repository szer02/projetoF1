import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Self

from dotenv import load_dotenv

from projetof1.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_BASE_URL = "https://api.openf1.org/v1"
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_ENVIRONMENT = "development"
DEFAULT_LOG_LEVEL = "INFO"

ENVIRONMENTS = frozenset({"development", "staging", "production"})
LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})

DEVELOPMENT_CACHE_TTL_SECONDS = 60 * 60
DEFAULT_CACHE_TTL_SECONDS = 24 * 60 * 60


class ConfigError(RuntimeError):
    """Configuração ausente ou inválida."""


@dataclass(frozen=True, slots=True)
class Settings:
    """Configuração de execução do dashboard."""

    base_url: str = DEFAULT_BASE_URL
    timeout: float = DEFAULT_TIMEOUT_SECONDS
    environment: str = DEFAULT_ENVIRONMENT
    log_level: str = DEFAULT_LOG_LEVEL

    @property
    def cache_ttl_seconds(self) -> int:
        """Tempo de cache das consultas à API, conforme o ambiente."""
        if self.environment == "development":
            return DEVELOPMENT_CACHE_TTL_SECONDS
        return DEFAULT_CACHE_TTL_SECONDS

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> Self:
        """Cria a configuração a partir de variáveis de ambiente.

        Args:
            env: Variáveis a usar (normalmente `os.environ`).

        Returns:
            Configuração validada, com valores padrão para variáveis ausentes.

        Raises:
            ConfigError: Se alguma variável tiver valor inválido. A mensagem
                cita o nome da variável, nunca o valor.
        """
        timeout = _parse_timeout(env.get("OPENF1_TIMEOUT"))

        environment = env.get("ENVIRONMENT", DEFAULT_ENVIRONMENT).strip().lower()
        if environment not in ENVIRONMENTS:
            msg = f"ENVIRONMENT inválido; use um de {sorted(ENVIRONMENTS)}"
            raise ConfigError(msg)

        log_level = env.get("LOG_LEVEL", DEFAULT_LOG_LEVEL).strip().upper()
        if log_level not in LOG_LEVELS:
            msg = f"LOG_LEVEL inválido; use um de {sorted(LOG_LEVELS)}"
            raise ConfigError(msg)

        base_url = env.get("OPENF1_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")
        if not base_url.startswith(("http://", "https://")):
            msg = "OPENF1_BASE_URL inválida; use uma URL http(s)"
            raise ConfigError(msg)

        return cls(
            base_url=base_url,
            timeout=timeout,
            environment=environment,
            log_level=log_level,
        )


def _parse_timeout(raw: str | None) -> float:
    if raw is None or not raw.strip():
        return DEFAULT_TIMEOUT_SECONDS
    try:
        timeout = float(raw)
    except ValueError as exc:
        msg = "OPENF1_TIMEOUT inválido; use um número de segundos"
        raise ConfigError(msg) from exc
    if timeout <= 0:
        msg = "OPENF1_TIMEOUT deve ser maior que zero"
        raise ConfigError(msg)
    return timeout


def load_settings() -> Settings:
    """Carrega o `.env` (se existir) e lê a configuração do ambiente.

    Deve ser chamada apenas no ponto de entrada.

    Raises:
        ConfigError: Se alguma variável tiver valor inválido.
    """
    load_dotenv()
    settings = Settings.from_env(os.environ)
    logger.debug("configuração carregada: environment=%s", settings.environment)
    return settings
