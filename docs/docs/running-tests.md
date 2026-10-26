# Como rodar os testes

## Atalhos

Atalhos do [taskipy](https://github.com/taskipy/taskipy), definidos em
`[tool.taskipy.tasks]` no `pyproject.toml`:

| Comando | Equivale a |
| --- | --- |
| `poetry run task test` | `poetry run pytest tests/unit/` |
| `poetry run task lint` | `poetry run ruff check .` |
| `poetry run task format` | `poetry run ruff check . --fix` e `poetry run ruff format .` |
| `poetry run task docs` | `poetry run mkdocs serve -f docs/mkdocs.yml` |

`poetry run task --list` mostra todos os atalhos.

## Fluxo de validação (local = CI)

```bash
poetry check --lock
poetry install --with docs
poetry run ruff check .
poetry run ruff format --check .
poetry run pytest tests/unit/
poetry run mkdocs build -f docs/mkdocs.yml --strict
```

## CI (GitHub Actions)

O workflow `.github/workflows/ci.yml` roda a cada push em `main` e `dev` e em todo pull
request. O job `validacao` executa o fluxo acima, mais a checagem de segredos com
`detect-secrets`.

Os testes de integração ficam no job `integracao`, que só roda sob demanda: na aba
**Actions** do GitHub, escolha **CI → Run workflow**. Assim, uma instabilidade da OpenF1
não quebra o CI dos pushes.

## Testes unitários

```bash
poetry run pytest tests/unit/
```

- A cobertura vem do `addopts` no `pyproject.toml` (`--cov=src/projetof1
  --cov-report=term-missing --cov-fail-under=50`). Abaixo de 50%, o comando falha.
- Nenhum teste unitário acessa a rede: o `HttpClient` usa `httpx.MockTransport` e o
  serviço recebe repositórios mockados com `pytest-mock`.
- As fixtures JSON sintéticas ficam em `tests/fixtures/`.

### Interpretando o relatório

O relatório `term-missing` lista, por arquivo, as linhas (`Missing`) e as ramificações
(`BrPart`) não executadas. Com `branch = true`, o percentual combina linhas e
ramificações. O `dashboard/app.py` só monta a tela no Streamlit e não tem teste unitário;
a lógica que ele usa (`charts.py` e `components.py`) é testada separadamente.

## Testes de integração

```bash
poetry run pytest tests/integration/ -m integration --no-cov
```

Consultam a OpenF1 real (requer internet) com sessões históricas fixas do GP de
Singapura 2023. Use `--no-cov`: sem ele, o limite de cobertura do `addopts` faz o
comando falhar.

## Execução focada

```bash
poetry run pytest tests/unit/test_processing_laps.py -k top_n -x --no-cov
```

## Lint e formatação

```bash
poetry run ruff check . --fix   # corrige o que for seguro
poetry run ruff format .        # formata
poetry run ruff check .         # confere
```
