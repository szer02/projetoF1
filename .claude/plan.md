# Plano de Criação — Dashboard F1 (OpenF1)

## Contexto

O objetivo do projeto é um **dashboard interativo em Streamlit** que consome a **OpenF1 API** (`https://api.openf1.org/v1/`) e mostra os dados históricos da F1 (2023 em diante, sem autenticação): resultado, voltas mais rápidas, ritmo, estratégia de pneus e clima de cada sessão.

O padrão de engenharia é o **SKILL.md**: Poetry, camadas `ingestion/`, `processing/`, `domain/` e `utils/`, Ruff, pytest com cobertura ≥ 50% e MkDocs Material em `docs/`. Os endpoints vêm de [doc_api.md](doc_api.md).

> A [.claude/skill.md](skill.md) foi alinhada ao SKILL.md do professor: camadas, ABCs com injeção de dependência, `utils/config.py` com `python-dotenv`, `--cov` em `addopts`, `docs/mkdocs.yml` com as 6 páginas, `detect-secrets`, ambientes e regras de PR. As referências "SKILL §N" abaixo seguem a numeração do documento do professor.

Estado atual do repositório: `pyproject.toml` mínimo (pacote `projetof1` em `src/`, `requires-python = ">=3.12"`), `.python-version` 3.12.10, `README.md` só com o título, `src/projetof1/__init__.py` e `tests/__init__.py`.

---

## 1. Stack e decisões

| Item | Escolha | Justificativa |
|---|---|---|
| Gerenciador | Poetry | Obrigatório (SKILL §2) |
| Python | `>=3.12,<4.0` | Mantém o `.python-version`; o limite superior evita conflito de resolução com o Streamlit |
| HTTP | `httpx` | Timeout explícito; `MockTransport` permite testar sem rede |
| Modelos | `pydantic` v2 | Validação tipada dos payloads da OpenF1 |
| UI | `streamlit` | Dashboard com cache nativo |
| Gráficos | `plotly` | Gráficos interativos com cores das equipes, linha do tempo de pneus e hover detalhado. Os gráficos nativos do Streamlit não permitem esse nível de controle visual |
| Config | `python-dotenv` | `.env` por ambiente (SKILL §7.3) |
| Lint/Format | `ruff` | Obrigatório (SKILL §4.2) |
| Testes | `pytest`, `pytest-cov`, `pytest-mock` | Cobertura ≥ 50% (SKILL §5) |
| Docs | `mkdocs-material` | Obrigatório (SKILL §6) |
| Pre-commit | `pre-commit` + `detect-secrets` | SKILL §7.4 e §7.5 |

O `pandas` entra como dependência transitiva do Streamlit e só é usado na camada de UI, para `st.dataframe`. Ele não é adicionado diretamente.

---

## 2. Estrutura de diretórios

```
projetoF1/
├── pyproject.toml
├── poetry.lock
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── .secrets.baseline              # gerado pelo detect-secrets
├── .streamlit/config.toml         # tema visual (seção 7)
├── README.md
├── src/projetof1/
│   ├── __init__.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── http_client.py         # HttpClient: timeout + retry/backoff
│   │   └── openf1_repositories.py # implementações concretas dos repositórios
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── laps.py                # voltas válidas, top N, séries de ritmo, melhores setores
│   │   ├── stints.py              # linha do tempo de pneus e pit stops
│   │   ├── results.py             # classificação e normalização quali × corrida
│   │   ├── weather.py             # resumo do clima da sessão
│   │   └── formatting.py          # 83.456 → "1:23.456", hex de equipe, etc.
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── models.py              # modelos pydantic
│   │   ├── repositories.py        # ABCs, uma por endpoint
│   │   └── services.py            # F1DashboardService
│   ├── dashboard/
│   │   ├── __init__.py
│   │   ├── app.py                 # composition root Streamlit (entrada)
│   │   ├── charts.py              # funções que montam figuras Plotly (puras, testáveis)
│   │   └── components.py          # cards, cabeçalho, CSS, tabelas
│   └── utils/
│       ├── __init__.py
│       ├── config.py              # Settings carregado por load_settings()
│       └── logger.py              # get_logger (modelo SKILL §7.2)
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── fixtures/                  # JSON sintéticos pequenos por endpoint
│   ├── unit/
│   │   ├── __init__.py
│   │   └── test_*.py              # seção 8
│   └── integration/
│       ├── __init__.py
│       └── test_openf1_live.py
└── docs/
    ├── mkdocs.yml
    └── docs/
        ├── index.md
        ├── architecture.md
        ├── project-structure.md
        ├── running-locally.md
        ├── running-tests.md
        └── contributing.md
```

**Desvio justificado (SKILL §1):** o pacote `dashboard/` não existe na estrutura padrão. Ele separa a camada de apresentação das regras de negócio, e assim `charts.py` pode ser testado sem subir o Streamlit.

**Regra de dependência:** `dashboard` → `domain.services` → (`domain.repositories`, `processing`) → `domain.models`. `ingestion` implementa `domain.repositories`. `domain` nunca importa `ingestion`, `httpx` nem `streamlit` (SKILL §3.3). Os imports são sempre absolutos (`from projetof1...`, SKILL §9.2).

---

## 3. Domain

### 3.1 `domain/models.py` (pydantic v2)
Modelos que espelham o payload da API, ignorando campos extras:
- `Meeting`: `meeting_key`, `meeting_name`, `country_name`, `circuit_short_name`, `year`, `date_start`
- `Session`: `session_key`, `meeting_key`, `session_name`, `session_type`, `date_start`, `date_end`, `year`
- `Driver`: `driver_number`, `full_name`, `name_acronym`, `team_name`, `team_colour`, `headshot_url | None`
- `Lap`: `driver_number`, `lap_number`, `lap_duration | None`, `duration_sector_1..3 | None`, `i1_speed`, `i2_speed`, `st_speed`, `is_pit_out_lap`
- `Stint`: `driver_number`, `stint_number`, `compound`, `lap_start`, `lap_end`, `tyre_age_at_start`
- `PitStop`: `driver_number`, `lap_number`, `lane_duration | None`, `stop_duration | None` (este último só existe a partir do GP dos EUA de 2024)
- `SessionResult`: `driver_number`, `position | None`, `duration` e `gap_to_leader` normalizados para `list[float | None]` (escalar na corrida, Q1–Q3 na quali), `number_of_laps`, `dnf`, `dns`, `dsq`
- `Weather`: `date`, `air_temperature`, `track_temperature`, `humidity`, `rainfall`, `wind_speed`, `wind_direction`

Projeções produzidas pelo `processing`:
- `FastestLapEntry`: piloto + melhor volta + setores
- `StintBar`: piloto, composto, volta inicial e final
- `WeatherSummary`
- `SessionOverview`: agrega tudo o que a tela da sessão precisa

### 3.2 `domain/repositories.py`
Uma ABC por endpoint (SKILL §3.4):
- `MeetingRepository.list(year)`
- `SessionRepository.list(meeting_key)`
- `DriverRepository.list(session_key)`
- `LapRepository.list(session_key, driver_number=None)`
- `StintRepository.list(session_key)`
- `PitRepository.list(session_key)`
- `SessionResultRepository.list(session_key)`
- `WeatherRepository.list(session_key)`

### 3.3 `domain/services.py`
`F1DashboardService` recebe os repositórios por injeção no construtor e expõe:
- `list_meetings(year) -> list[Meeting]`, ordenado por data
- `list_sessions(meeting_key) -> list[Session]`
- `get_session_overview(session_key, top_n=10) -> SessionOverview`, que traz pilotos, resultado, top N voltas, estratégia, pit stops e clima

O serviço só orquestra: busca nos repositórios e chama funções puras de `processing`.

---

## 4. Processing (funções puras, sem I/O)

- `laps.py`:
  - `filter_valid_laps(laps)`: descarta voltas sem `lap_duration` e voltas de saída do pit
  - `build_driver_index(drivers) -> dict[int, Driver]`
  - `compute_top_n_laps(laps, index, n)`: devolve a melhor volta **por piloto**, ordenada
  - `lap_time_series(laps, driver_numbers)`: série de ritmo, sem outliers acima de 107% da mediana do piloto (safety car, por exemplo)
  - `best_sectors(laps)`: melhor tempo de cada setor por piloto
- `stints.py`: `build_stint_timeline(stints, drivers)` e `pit_summary(pits, drivers)`
- `results.py`: `build_classification(results, drivers)` ordena por posição, deixa os nulos no fim e marca DNF, DNS e DSQ
- `weather.py`: `summarize_weather(weather)` calcula mínimo, máximo e último valor de temperatura e indica se choveu
- `formatting.py`: `format_lap_time(83.456) -> "1:23.456"`, `format_gap`, `team_color("3671C6") -> "#3671C6"` (com cor padrão quando nulo), `COMPOUND_COLORS`

---

## 5. Ingestion

### 5.1 `ingestion/http_client.py`
- `HttpClient(base_url, timeout, max_retries=3, sleep=time.sleep)`
- `get(endpoint, params) -> list[dict]`
- Faz retry com backoff exponencial apenas em timeout, erro de transporte, 429 e 5xx. Erros 4xx falham na hora.
- Cada tentativa é logada.
- Depois de esgotar as tentativas, levanta `OpenF1ApiError` encadeado com `from exc`.
- O `sleep` é injetável para que os testes não esperem de verdade.

### 5.2 `ingestion/openf1_repositories.py`
Implementações concretas das ABCs. Cada uma monta a query (`year`, `meeting_key`, `session_key`), chama `HttpClient.get` e valida cada item com pydantic. Itens inválidos são **ignorados, com log da contagem**, para manter o dashboard resiliente.

---

## 6. Utils

- `config.py`: dataclass `Settings` com `base_url`, `timeout`, `environment` e `log_level`, mais a função `load_settings()`, que chama `load_dotenv()` e lê o ambiente. Nada é lido na importação, então os testes passam um ambiente controlado.
  - O `environment` (`development`, `staging`, `production`, conforme SKILL §7.6) controla o nível de log e o TTL do cache: 1 h em `development` e 24 h nos demais.
- `logger.py`: `get_logger(name)`, conforme SKILL §7.2.

---

## 7. Dashboard (visual)

### 7.1 Tema: `.streamlit/config.toml`
Tema escuro com primária vermelha F1 (`#E10600`), fundo grafite e layout `wide`.

### 7.2 `dashboard/app.py` (composition root)
1. `load_settings()` → `HttpClient` → repositórios → `F1DashboardService`, com `@st.cache_resource`.
2. **Sidebar:** seletores de temporada (2023 até o ano atual), GP e sessão, mais um link de crédito para a OpenF1.
3. **Cabeçalho:** nome do GP, circuito, data e tipo de sessão, e `st.metric` com temperatura do ar e da pista, umidade e chuva.
4. **Abas:**

| Aba | Conteúdo |
|---|---|
| Resultado | Pódio em 3 cards (foto, nome, equipe na cor da equipe, tempo/gap) + tabela de classificação com DNF/DNS/DSQ |
| Voltas mais rápidas | Top 10 em barras horizontais na cor de cada equipe + tabela com setores (melhor setor destacado) |
| Ritmo | Multiselect de pilotos (padrão: top 3) → linha de tempo por volta |
| Estratégia | Linha do tempo de stints por piloto, colorida por composto (SOFT vermelho, MEDIUM amarelo, HARD branco, INTER verde, WET azul) + tabela de pit stops |

As buscas usam `@st.cache_data(ttl=...)` por `session_key`. Quando a API falha, a tela mostra `st.error` com mensagem amigável e o detalhe vai para o log. Sessões sem dados mostram `st.info`, como acontece com treinos, que não têm `session_result` completo.

### 7.3 `dashboard/charts.py` e `components.py`
- `charts.py` tem funções puras que recebem as projeções do domínio e devolvem `plotly.graph_objects.Figure`: `fastest_laps_bar`, `pace_lines`, `stint_timeline`. Todas usam um template escuro comum.
- `components.py` tem os cards do pódio (HTML/CSS via `st.markdown`), o cabeçalho e as tabelas formatadas.

---

## 8. Testes

| Arquivo (`tests/unit/`) | Foco |
|---|---|
| `test_http_client.py` | `MockTransport`: sucesso, retry em 429/5xx/timeout, 4xx sem retry, erro após esgotar tentativas |
| `test_openf1_repositories.py` | Query montada corretamente, itens inválidos ignorados e contados |
| `test_models.py` | Parsing das fixtures; `duration` escalar × array |
| `test_processing_laps.py` | Voltas válidas, top N com empate, entrada vazia, outliers no ritmo |
| `test_processing_stints.py`, `test_processing_results.py`, `test_processing_weather.py`, `test_formatting.py` | Funções puras e casos limite |
| `test_services.py` | `F1DashboardService` com repositórios mockados (`pytest-mock`) |
| `test_charts.py` | Número de traces, cores das equipes e títulos das figuras |
| `test_config.py` | Padrões e leitura de variáveis via `monkeypatch` |

**Integração:** `tests/integration/test_openf1_live.py` usa `@pytest.mark.integration` e consulta a API real com uma **sessão histórica fixa** (`session_key=9161`). Uma sessão fixa dá resultado estável; `latest` mudaria a cada fim de semana.

**`pyproject.toml`** (SKILL §5.2):
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=src/projetof1 --cov-report=term-missing --cov-fail-under=50"
markers = ["integration: testes que acessam a API real"]
```

A meta é ≥ 50%; o alvo realista é mais de 75%, porque `processing` e `charts` são puros. Os testes de integração rodam com `--no-cov`, para não esbarrar no limite de cobertura.

---

## 9. Configuração e qualidade

- **`pyproject.toml`:**
  - Mantém o formato `[project]` existente, ajustando `description` e `requires-python`.
  - Dependências entram só via `poetry add` (grupos `dev` e `docs`).
  - `[tool.ruff]` segue a SKILL §4.2, com `target-version = "py312"` e `known-first-party = ["projetof1"]`.
- **`.env.example`:**
  ```
  OPENF1_BASE_URL=https://api.openf1.org/v1
  OPENF1_TIMEOUT=10
  ENVIRONMENT=development
  LOG_LEVEL=INFO
  ```
- **`.gitignore`:** `.env`, `*.pem`, `*.key`, `credentials.json`, `*.secret`, `.venv/`, caches, `htmlcov/`, `.coverage`, `docs/site/`.
- **`.pre-commit-config.yaml`:** `ruff` (`--fix`), `ruff-format` e `detect-secrets` (com `.secrets.baseline`).
- **Padrões:** type hints em todas as funções, `get_logger(__name__)` em vez de `print`, imports absolutos e nomes conforme SKILL §9.

---

## 10. Documentação (`docs/`)

- `docs/mkdocs.yml` segue a SKILL §6.3, com `language: pt`, `navigation.tabs` e as 6 páginas.
- As páginas ficam em `docs/docs/` e cobrem:
  - propósito e créditos à OpenF1, com o aviso de projeto não oficial;
  - diagrama de camadas e fluxo de injeção;
  - árvore comentada do projeto;
  - como rodar localmente (Poetry + `streamlit run`);
  - testes e cobertura;
  - checklist de PR (SKILL §8).
- Comandos: `poetry run mkdocs serve -f docs/mkdocs.yml` e `poetry run mkdocs build -f docs/mkdocs.yml`.

---

## 11. Ordem de execução

> No Windows, rode `Remove-Item Env:VIRTUAL_ENV -ErrorAction SilentlyContinue` antes dos comandos Poetry, para não usar um venv herdado.

1. **Bootstrap:**
   - ajustar `pyproject.toml`;
   - rodar `poetry add httpx pydantic streamlit plotly python-dotenv`;
   - rodar `poetry add --group dev pytest pytest-cov pytest-mock ruff pre-commit`;
   - rodar `poetry add --group docs mkdocs-material`;
   - criar `.gitignore`, `.env.example`, pre-commit e `.streamlit/config.toml`.
2. **Utils:** `logger.py` e `config.py`, com testes.
3. **Domain:** `models.py` → `repositories.py`, com as fixtures JSON e `test_models`.
4. **Processing:** módulos e testes (primeiros testes verdes).
5. **Ingestion:** `http_client.py` → `openf1_repositories.py`, com testes via `MockTransport`.
6. **Service:** `services.py` e `test_services`.
7. **Dashboard:** `charts.py` (com testes) → `components.py` → `app.py`.
8. **Integração:** `test_openf1_live.py`.
9. **Docs:** `docs/mkdocs.yml` e as 6 páginas.
10. **README.md:** visão geral e guia rápido. Depois, `pre-commit install` e `pre-commit run --all-files`.

---

## 12. Verificação fim a fim

```powershell
poetry install
poetry run ruff check .
poetry run ruff format . --check
poetry run pytest tests/unit/                                  # cobertura >= 50%
poetry run pytest tests/integration/ -m integration --no-cov   # requer internet
poetry run mkdocs build -f docs/mkdocs.yml
poetry run streamlit run src/projetof1/dashboard/app.py        # http://localhost:8501
```

**Critério de pronto:**
- Lint e formatação 100% verdes.
- Testes unitários passando, com cobertura ≥ 50%.
- O build da documentação passa.
- Verificação manual: no dashboard, escolher 2024 → um GP → Race. As 4 abas devem renderizar com as cores das equipes. Repetir com uma sessão de Qualifying, que exercita o `duration` em formato de array.
