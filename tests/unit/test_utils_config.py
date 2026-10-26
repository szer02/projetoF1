import pytest

from projetof1.utils.config import (
    DEFAULT_BASE_URL,
    DEFAULT_CACHE_TTL_SECONDS,
    DEVELOPMENT_CACHE_TTL_SECONDS,
    ConfigError,
    Settings,
    load_settings,
)


def test_from_env_without_variables_uses_defaults() -> None:
    settings = Settings.from_env({})

    assert settings == Settings()
    assert settings.base_url == DEFAULT_BASE_URL
    assert settings.environment == "development"


def test_from_env_reads_and_normalizes_variables() -> None:
    settings = Settings.from_env(
        {
            "OPENF1_BASE_URL": "https://example.com/v1/",
            "OPENF1_TIMEOUT": "2.5",
            "ENVIRONMENT": " Production ",
            "LOG_LEVEL": "debug",
        }
    )

    assert settings == Settings(
        base_url="https://example.com/v1",
        timeout=2.5,
        environment="production",
        log_level="DEBUG",
    )


@pytest.mark.parametrize(
    ("env", "variable"),
    [
        pytest.param({"ENVIRONMENT": "qa"}, "ENVIRONMENT", id="ambiente-desconhecido"),
        pytest.param({"LOG_LEVEL": "verbose"}, "LOG_LEVEL", id="nivel-de-log"),
        pytest.param({"OPENF1_TIMEOUT": "abc"}, "OPENF1_TIMEOUT", id="timeout-texto"),
        pytest.param({"OPENF1_TIMEOUT": "0"}, "OPENF1_TIMEOUT", id="timeout-zero"),
        pytest.param({"OPENF1_TIMEOUT": "-1"}, "OPENF1_TIMEOUT", id="timeout-negativo"),
        pytest.param(
            {"OPENF1_BASE_URL": "ftp://x"}, "OPENF1_BASE_URL", id="url-sem-http"
        ),
    ],
)
def test_from_env_with_invalid_value_names_the_variable(
    env: dict[str, str], variable: str
) -> None:
    with pytest.raises(ConfigError, match=variable):
        Settings.from_env(env)


def test_invalid_value_is_not_leaked_in_error_message() -> None:
    with pytest.raises(ConfigError) as error:
        Settings.from_env({"OPENF1_TIMEOUT": "segredo-123"})

    assert "segredo-123" not in str(error.value)


def test_blank_timeout_falls_back_to_default() -> None:
    assert Settings.from_env({"OPENF1_TIMEOUT": "  "}).timeout == Settings().timeout


@pytest.mark.parametrize(
    ("environment", "ttl"),
    [
        ("development", DEVELOPMENT_CACHE_TTL_SECONDS),
        ("staging", DEFAULT_CACHE_TTL_SECONDS),
        ("production", DEFAULT_CACHE_TTL_SECONDS),
    ],
)
def test_cache_ttl_depends_on_environment(environment: str, ttl: int) -> None:
    assert Settings(environment=environment).cache_ttl_seconds == ttl


def test_load_settings_reads_process_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("OPENF1_TIMEOUT", "7")

    settings = load_settings()

    assert settings.environment == "staging"
    assert settings.timeout == 7.0
