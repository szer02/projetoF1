---
name: python-engenharia-dados
description: >-
  Regras, convenções, ferramentas e boas práticas para criar, implementar, testar,
  documentar, revisar e manter projetos Python do time de Engenharia de Dados.
  Stack oficial: Poetry (ambiente e dependências), layout src/ em camadas (ingestion,
  processing, domain, utils), Ruff (lint, formatação e imports), Pytest + pytest-cov
  (cobertura unitária mínima de 50%) e MkDocs Material (documentação). Use ao iniciar
  um projeto, implementar ou alterar código, escrever testes, configurar CI, revisar
  pull requests ou atualizar documentação.
---

# Skill: Desenvolvimento Python para Engenharia de Dados

## 0. Como usar este documento

### 0.1 Níveis de exigência

| Termo | Significado | Consequência do descumprimento |
| --- | --- | --- |
| **MUST** / **MUST NOT** | Requisito obrigatório. | Bloqueia merge e entrega. |
| **SHOULD** / **SHOULD NOT** | Recomendação forte. Desvios exigem justificativa registrada no PR, em comentário no código ou em ADR. | Deve ser discutido na revisão. |
| **MAY** | Prática opcional, adotada conforme contexto. | Nenhuma. |

Cada regra tem um identificador (`DEP-01`, `TST-03` etc.) para ser citada em revisões, PRs e commits.

### 0.2 Precedência

1. Decisões registradas no próprio projeto (ADR em `docs/docs/adr/` ou seção explícita no `README.md`) prevalecem sobre regras **SHOULD** e **MAY** deste documento.
2. Regras **MUST** só podem ser alteradas por decisão do time, registrada em ADR. Um projeto não as relaxa por conta própria.
3. Na ausência de decisão local, vale este documento.

### 0.3 Instruções específicas para agentes de IA

- **MUST** ler `pyproject.toml`, `README.md` e `docs/docs/running-locally.md` (quando existirem) antes de alterar código.
- **MUST** executar o fluxo de validação da [seção 14](#14-fluxo-de-desenvolvimento-e-validação) antes de declarar uma tarefa concluída e relatar o resultado real de cada etapa, incluindo falhas.
- **MUST NOT** reduzir o limite de cobertura, adicionar `# noqa`, `# pragma: no cover`, `per-file-ignores` ou desativar etapas de CI com o objetivo de fazer a validação passar.
- **MUST NOT** editar `poetry.lock` manualmente nem usar `pip` para gerenciar dependências.
- **MUST NOT** adicionar dependências, frameworks ou camadas arquiteturais sem necessidade demonstrada pela tarefa. Ao adicionar uma dependência, justifique-a no resumo da entrega.
- **SHOULD** perguntar quando um requisito de negócio for ambíguo (granularidade, chave de deduplicação, política de rejeição de registros), em vez de presumir.
- **MUST NOT** inventar opções de configuração ou comandos. Em caso de dúvida sobre uma ferramenta, consulte `poetry run <ferramenta> --help`.

---

## 1. Objetivo e escopo

**Objetivo:** garantir que todo projeto Python do time seja simples, modular, legível, testável, reprodutível e documentado, com um fluxo de validação idêntico na máquina local e na CI.

**Escopo:** bibliotecas internas, pipelines de dados (batch e incrementais), jobs agendados, CLIs, dashboards e serviços de integração escritos em Python.

**Fora de escopo:** escolha de frameworks de processamento (Spark, Pandas, Polars), de orquestradores (Airflow, Dagster, Prefect), de frameworks de UI (Streamlit, Dash) e de plataformas de nuvem. Essas escolhas dependem de requisitos explícitos do projeto e **SHOULD** ser registradas em ADR. Este documento **MUST NOT** ser interpretado como exigência para adotar qualquer uma delas.

---

## 2. Resumo das regras obrigatórias

1. Poetry é a única ferramenta de gerenciamento de ambiente e dependências (`DEP-*`).
2. `pyproject.toml` centraliza metadados, dependências e configuração de ferramentas; `poetry.lock` é versionado (`DEP-*`).
3. O código de produção fica em `src/<pacote>/`, organizado nas camadas `ingestion/`, `processing/`, `domain/` e `utils/`; os testes ficam em `tests/` (`EST-*`).
4. Ruff é a única ferramenta de lint, formatação e organização de imports (`LNT-*`).
5. Pytest é a ferramenta de testes. A cobertura da suíte unitária, medida com `pytest-cov` sobre o pacote de produção, **MUST** ser ≥ 50% (`TST-*`).
6. A documentação usa MkDocs com o tema Material, com `docs/mkdocs.yml` e as páginas em `docs/docs/`, e **MUST** compilar com `--strict` (`DOC-*`).
7. Segredos nunca entram no código, nos logs nem no versionamento (`SEG-*`).
8. A CI executa o mesmo fluxo de validação disponível localmente e falha quando qualquer etapa falha (`CI-*`).
9. Todo código entra na branch principal por Pull Request aprovado por outra pessoa (`PR-*`).

---

## 3. Ferramentas oficiais e responsabilidades

| Ferramenta | Responsabilidade | Grupo Poetry | Comando principal | Não usar em paralelo |
| --- | --- | --- | --- | --- |
| Poetry ≥ 2.0 | Ambiente virtual, dependências, lock, build | — (instalado fora do projeto) | `poetry install` | pip, pip-tools, pipenv, conda (para o projeto) |
| Ruff | Lint, formatação, ordenação e limpeza de imports | `dev` | `poetry run ruff check .` | Black, isort, flake8, pylint, pyupgrade, autoflake |
| Pytest | Execução de testes | `dev` | `poetry run pytest` | unittest como runner, nose |
| pytest-cov | Medição de cobertura e limite mínimo (via `addopts`) | `dev` | `poetry run pytest tests/unit/` | `coverage run` em paralelo |
| pytest-mock | Fixture `mocker` para simular dependências externas | `dev` | via `pytest` | — |
| MkDocs + Material | Documentação técnica | `docs` | `poetry run mkdocs build -f docs/mkdocs.yml --strict` | Sphinx (para o mesmo propósito) |
| mkdocstrings[python] | Referência gerada a partir de docstrings (**MAY**) | `docs` | via `docs/mkdocs.yml` | — |
| python-dotenv | Carregar o `.env` no ponto de entrada | produção | `load_dotenv()` | — |
| pre-commit | Verificações antes de cada commit (**SHOULD**) | `dev` | `poetry run pre-commit run --all-files` | — |
| detect-secrets | Bloqueio de segredos antes do commit (hook do pre-commit) | `dev` | `poetry run pre-commit run detect-secrets --all-files` | — |
| mypy | Checagem de tipos (**SHOULD**) | `dev` | `poetry run mypy src` | outro type checker em paralelo |
| pip-audit | Auditoria de vulnerabilidades (**MAY**) | `dev` | `poetry run pip-audit` | — |

> **Nota:** `pip-audit` é uma ferramenta de **auditoria** do ambiente, não de instalação. Seu uso via `poetry run` não contradiz `DEP-01`.

Toda ferramenta adicionada ao projeto **MUST** ter finalidade definida, estar declarada em um grupo do Poetry, estar configurada no `pyproject.toml` (quando a ferramenta suportar) e ter comando documentado em `docs/docs/running-locally.md` ou `docs/docs/running-tests.md`.

---

## 4. Ambiente e dependências com Poetry

### 4.1 Regras

| ID | Nível | Regra |
| --- | --- | --- |
| DEP-01 | MUST NOT | Usar `pip install`, `pip uninstall`, `python -m pip` ou equivalentes para gerenciar dependências do projeto. |
| DEP-02 | MUST | Usar `pyproject.toml` como arquivo central do projeto (metadados, dependências e configuração de ferramentas). Não criar `setup.py`, `setup.cfg` nem `requirements*.txt` como fonte de verdade. |
| DEP-03 | MUST | Adicionar dependências de produção com `poetry add <pacote>` e de desenvolvimento com `poetry add --group dev <pacote>`. |
| DEP-04 | MUST | Remover dependências com `poetry remove <pacote>` (ou `poetry remove --group <grupo> <pacote>`). |
| DEP-05 | MUST | Versionar `poetry.lock`. |
| DEP-06 | MUST NOT | Editar `poetry.lock` manualmente. |
| DEP-07 | MUST | Executar ferramentas do projeto com `poetry run <comando>`. Instalações globais (Ruff, Pytest, MkDocs) **MUST NOT** substituir as versões declaradas no projeto. |
| DEP-08 | MUST | Declarar a faixa de Python suportada em `requires-python` e documentá-la no `README.md`. |
| DEP-09 | MUST | Separar dependências em grupos: produção (`[project] dependencies`), `dev` (lint, testes, pre-commit) e `docs` (MkDocs). Um grupo `test` separado **MAY** ser criado quando houver ambientes que precisem apenas dos testes. |
| DEP-10 | SHOULD | Preferir a biblioteca padrão quando ela resolver o problema com clareza equivalente. Cada nova dependência de produção **SHOULD** ter justificativa no PR. |
| DEP-11 | MUST | Após alterar manualmente um campo de `pyproject.toml` que afete a resolução (por exemplo, `requires-python`), executar `poetry lock` e versionar o lock atualizado. A CI **MUST** verificar a consistência com `poetry check --lock`. |
| DEP-12 | SHOULD NOT | Editar à mão as seções de dependências do `pyproject.toml`. Use `poetry add` / `poetry remove`, que atualizam `pyproject.toml` e `poetry.lock` juntos. |

**Exceção explícita:** a instalação do **próprio Poetry** é uma etapa de bootstrap da máquina e fica fora do projeto. Use o instalador oficial ou `pipx install poetry`. Essa é a única situação em que `pipx` aparece no fluxo.

### 4.2 Comandos e quando usar cada um

| Situação | Comando |
| --- | --- |
| Criar um projeto novo (Poetry 2.x usa o layout `src/` por padrão; confira a estrutura gerada) | `poetry new meu-projeto` |
| Escolher o interpretador do ambiente virtual | `poetry env use 3.12` |
| Ver qual ambiente está em uso | `poetry env info` |
| Instalar o projeto e os grupos não opcionais (após clonar ou após `git pull` com mudança no lock) | `poetry install` |
| Instalar também o grupo opcional de documentação | `poetry install --with docs` |
| Instalar apenas as dependências de produção (imagem de deploy) | `poetry install --only main` |
| Deixar o ambiente idêntico ao lock, removendo pacotes não declarados | `poetry sync` |
| Adicionar dependência de produção | `poetry add httpx` |
| Adicionar dependência de produção com restrição explícita de versão | `poetry add "httpx>=0.27,<1.0"` |
| Adicionar dependências de desenvolvimento | `poetry add --group dev pytest pytest-cov pytest-mock ruff pre-commit detect-secrets` |
| Adicionar dependências de documentação | `poetry add --group docs mkdocs-material "mkdocstrings[python]"` |
| Remover dependência | `poetry remove httpx` / `poetry remove --group dev pre-commit` |
| Atualizar dependências dentro das restrições declaradas | `poetry update` ou `poetry update httpx` |
| Regenerar o lock após editar `pyproject.toml`, sem atualizar versões | `poetry lock` |
| Verificar se `pyproject.toml` e `poetry.lock` estão consistentes | `poetry check --lock` |
| Listar dependências desatualizadas / árvore de dependências | `poetry show --outdated` / `poetry show --tree` |
| Executar uma ferramenta ou o próprio projeto | `poetry run ruff check .` / `poetry run meu-projeto --data 2026-01-31` |
| Gerar artefatos de distribuição (somente se o pacote for distribuído) | `poetry build` |

> `poetry shell` foi removido do núcleo do Poetry 2.x. Prefira `poetry run`. Para ativar o ambiente no terminal, use `poetry env activate`, que imprime o comando de ativação.

### 4.3 Versionamento semântico

| ID | Nível | Regra |
| --- | --- | --- |
| DEP-13 | MUST | O campo `version` do `pyproject.toml` segue SemVer (`MAJOR.MINOR.PATCH`): `MAJOR` para quebra de compatibilidade na API pública, `MINOR` para funcionalidade nova compatível e `PATCH` para correção compatível. |

---

## 5. Estrutura de diretórios

### 5.1 Estrutura de referência

```text
meu-projeto/
├── pyproject.toml
├── poetry.lock
├── README.md
├── .gitignore
├── .env.example
├── .pre-commit-config.yaml
├── .secrets.baseline              # gerado pelo detect-secrets
├── src/
│   └── meu_projeto/
│       ├── __init__.py
│       ├── cli.py                 # ponto de entrada (composition root)
│       ├── ingestion/             # fontes e destinos: leitura, escrita, clientes de API
│       │   └── __init__.py
│       ├── processing/            # transformações, limpeza, enriquecimento, agregações (puras)
│       │   └── __init__.py
│       ├── domain/                # modelos, regras de negócio, validações, contratos (ABCs), serviços
│       │   └── __init__.py
│       └── utils/                 # transversais: config.py, logger.py, helpers genéricos
│           └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   └── __init__.py
│   └── integration/
│       └── __init__.py
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

As quatro camadas são **obrigatórias** como organização do código; dentro delas, módulos são criados conforme a necessidade. O ponto de entrada (`cli.py`, um app de UI ou a função chamada pelo orquestrador) fica na raiz do pacote ou em um subpacote próprio de apresentação e é o único lugar que instancia implementações concretas e as injeta nos serviços. Desvios desta estrutura **MUST** ser justificados em ADR ou no `README.md`.

### 5.2 Regras

| ID | Nível | Regra |
| --- | --- | --- |
| EST-01 | MUST | Colocar todo código de produção em `src/<nome_do_pacote>/`, com `__init__.py`. |
| EST-02 | MUST | Manter testes em `tests/`, documentação em `docs/` (`docs/mkdocs.yml` + páginas em `docs/docs/`) e configuração de ferramentas em `pyproject.toml`, separados do código de produção. |
| EST-03 | MUST | Configurar o Poetry para empacotar o código de `src/`: `packages = [{ include = "meu_projeto", from = "src" }]` em `[tool.poetry]`. |
| EST-04 | MUST NOT | Criar subpacotes ou módulos vazios além das quatro camadas obrigatórias apenas para seguir uma estrutura. |
| EST-05 | MUST | Organizar o código nas camadas `ingestion/`, `processing/`, `domain/` e `utils/` (responsabilidades na [seção 5.1](#51-estrutura-de-referência)) e, dentro delas, por domínio de negócio (`processing/vendas.py`, `processing/estoque.py`). |
| EST-06 | SHOULD | Manter módulos com uma responsabilidade coesa. Um módulo que ultrapassa ~400 linhas ou mistura I/O, regra de negócio e orquestração **SHOULD** ser dividido. O limite é uma referência de revisão, não uma regra automática. |
| EST-07 | MUST NOT | Criar imports circulares. Dependências seguem a direção: ponto de entrada → `domain` (serviços) → (contratos de `domain`, `processing`) → modelos de `domain`; `ingestion` implementa os contratos de `domain`. `domain` **MUST NOT** importar `ingestion` nem bibliotecas de infraestrutura (banco, storage, HTTP); `ingestion` **MUST NOT** conter regra de negócio; `utils` pode ser importado por todas as camadas e não importa nenhuma delas. |
| EST-08 | MUST NOT | Colocar lógica de negócio em scripts de execução, `__main__`, notebooks, `conftest.py` ou arquivos de configuração. |
| EST-09 | MUST | Expor pontos de entrada explícitos via `[project.scripts]` (ex.: `meu-projeto = "meu_projeto.cli:main"`) ou via funções `main()` invocáveis por um orquestrador. |
| EST-10 | SHOULD NOT | Usar nomes genéricos como `helpers.py`, `common.py` ou `misc.py` quando houver nome mais específico (`datas.py`, `particionamento.py`, `cliente_s3.py`). `utils/` abriga apenas código transversal sem regra de negócio: `config.py`, `logger.py` e helpers genéricos. |
| EST-11 | MAY | Manter notebooks exploratórios em `notebooks/`, fora do pacote. Notebooks **MUST NOT** ser importados por código de produção. Lógica reaproveitável **MUST** migrar para o pacote, com testes. |
| EST-12 | SHOULD | Usar `__init__.py` mínimos: sem lógica e sem efeitos colaterais na importação (sem I/O, conexões ou leitura de configuração). |
| EST-13 | MUST | Usar imports absolutos (`from meu_projeto.domain.vendas import Venda`). Imports relativos (`from ..domain import ...`, `from .logger import ...`) são proibidos. |

---

## 6. Modularidade e arquitetura

### 6.1 Princípios gerais

| ID | Nível | Regra |
| --- | --- | --- |
| ARQ-01 | MUST | Aplicar o princípio da responsabilidade única a módulos, classes e funções. |
| ARQ-02 | MUST | Separar regras de negócio, acesso a dados, integração externa, configuração e orquestração em módulos distintos. |
| ARQ-03 | SHOULD | Escrever funções pequenas e coesas. Uma função que precisa de comentários para separar “etapas” internas **SHOULD** ser dividida. |
| ARQ-04 | MUST | Definir contratos explícitos (type hints e docstrings) nas funções públicas de cada módulo: tipos de entrada e saída, exceções levantadas e efeitos colaterais. |
| ARQ-05 | MUST NOT | Depender de estado implícito: variáveis globais mutáveis, leitura de `os.environ` espalhada pelo código, conexões criadas na importação. |
| ARQ-06 | SHOULD | Injetar dependências externas (clientes, conexões, caminhos, relógio) como parâmetros quando isso facilitar testes. Não é necessário usar container de injeção de dependência. Parâmetros de função e construtores bastam. |
| ARQ-07 | MUST | Centralizar a configuração em `utils/config.py` e carregá-la uma vez, no ponto de entrada. |
| ARQ-08 | SHOULD | Desacoplar regra de negócio de infraestrutura com injeção de dependência e abstrações: contratos (`ABC` ou `Protocol`) para fontes e destinos externos ficam em `domain/`, as implementações concretas em `ingestion/`, e o ponto de entrada faz a ligação (ver [6.3](#63-separação-entre-regra-de-negócio-e-infraestrutura)). Fora dessa fronteira, **SHOULD NOT** criar abstrações prematuras (hierarquias de transformações, factories, padrões sem problema concreto); prefira funções e composição. |
| ARQ-09 | SHOULD | Manter transformações determinísticas: mesma entrada, mesma saída. Data atual, aleatoriedade e I/O entram como parâmetros. |
| ARQ-10 | SHOULD | Separar leitura, transformação e escrita, de modo que a transformação seja testável sem I/O. |

### 6.2 Arquitetura de pipelines de dados

```text
cli / app / orquestrador externo   (carrega utils.config, instancia ingestion e injeta)
        │  parâmetros de execução, ex.: data de referência
        ▼
ingestion (leitura) ──► domain (validação) ──► processing ──► ingestion (escrita)
                              │
                              └──► registros rejeitados (contados, logados, opcionalmente persistidos)
```

| ID | Nível | Regra |
| --- | --- | --- |
| ARQ-11 | MUST | Separar ingestão e persistência (`ingestion/`), validação e regras (`domain/`), transformação (`processing/`) e composição (ponto de entrada). Scripts monolíticos que misturam I/O, regra de negócio e transformação são proibidos. |
| ARQ-12 | MUST | Validar explicitamente schema, tipos, nulidade e regras de negócio na entrada do pipeline (ver [seção 12](#12-padrões-de-engenharia-de-dados)). |
| ARQ-13 | MUST | Definir e documentar o comportamento de reprocessamento: idempotência, deduplicação e sobrescrita de partições. |
| ARQ-14 | SHOULD | Processar dados em fluxo (iteradores, geradores, leitura em lotes) quando o volume puder exceder a memória disponível. |
| ARQ-15 | MUST NOT | Introduzir Spark, Pandas, Polars, Airflow ou frameworks equivalentes sem requisito explícito (volume, integração existente, decisão do time). |
| ARQ-16 | SHOULD | Tornar o pipeline invocável por função (`executar(config, data_referencia)`), de modo que qualquer orquestrador o chame sem duplicar lógica. |

### 6.3 Separação entre regra de negócio e infraestrutura

O contrato fica em `domain/`, a implementação concreta em `ingestion/` e o serviço recebe o contrato pelo construtor. Assim, o teste unitário injeta um mock no lugar da fonte real.

```python
# domain/repositorios.py
from abc import ABC, abstractmethod
from collections.abc import Iterator
from datetime import date

from meu_projeto.domain.vendas import Venda


class FonteVendas(ABC):
    """Contrato de leitura de vendas; implementado em `ingestion/`."""

    @abstractmethod
    def vendas_do_dia(self, dia: date) -> Iterator[Venda]:
        """Retorna as vendas validadas de `dia`."""
```

```python
# domain/servicos.py
from datetime import date
from decimal import Decimal

from meu_projeto.domain.repositorios import FonteVendas


class ServicoReceita:
    """Regras de receita, sem conhecer a origem dos dados."""

    def __init__(self, fonte: FonteVendas) -> None:
        self._fonte = fonte

    def receita_do_dia(self, dia: date) -> Decimal:
        """Soma o valor das vendas de `dia`."""
        return sum(
            (venda.valor for venda in self._fonte.vendas_do_dia(dia)), Decimal(0)
        )
```

```python
# tests/unit/test_domain_servicos.py
from datetime import date
from decimal import Decimal

from pytest_mock import MockerFixture

from meu_projeto.domain.repositorios import FonteVendas
from meu_projeto.domain.servicos import ServicoReceita
from meu_projeto.domain.vendas import Venda


def test_receita_do_dia_soma_vendas_da_fonte(mocker: MockerFixture) -> None:
    fonte = mocker.create_autospec(FonteVendas, instance=True)
    fonte.vendas_do_dia.return_value = iter(
        [
            Venda("P1", date(2026, 1, 1), Decimal("10.00")),
            Venda("P2", date(2026, 1, 1), Decimal("5.50")),
        ]
    )

    assert ServicoReceita(fonte).receita_do_dia(date(2026, 1, 1)) == Decimal("15.50")
    fonte.vendas_do_dia.assert_called_once_with(date(2026, 1, 1))
```

---

## 7. Configuração de referência do `pyproject.toml`

> Os metadados, nomes e versões abaixo são **ilustrativos**. As faixas de versão das dependências são geradas por `poetry add` e **MUST NOT** ser copiadas manualmente. As seções `[tool.*]` de configuração de ferramentas são a **referência obrigatória** do time e podem ser estendidas com justificativa.

```toml
[project]
name = "meu-projeto"
version = "0.1.0"  # SemVer (DEP-13)
description = "Pipelines de dados de vendas."
readme = "README.md"
requires-python = ">=3.12,<3.14"
authors = [{ name = "Time de Engenharia de Dados" }]
dependencies = []  # gerenciado por `poetry add`

[project.scripts]
meu-projeto = "meu_projeto.cli:main"

[build-system]
requires = ["poetry-core>=2.0.0,<3.0.0"]
build-backend = "poetry.core.masonry.api"

# ---------------------------------------------------------------- Poetry
[tool.poetry]
packages = [{ include = "meu_projeto", from = "src" }]

# Grupos gerados por `poetry add --group ...` (versões ilustrativas).
[tool.poetry.group.dev.dependencies]
ruff = "^0.9.0"
pytest = "^8.3.0"
pytest-cov = "^6.0.0"
pytest-mock = "^3.14.0"
pre-commit = "^4.0.0"
detect-secrets = "^1.5.0"

[tool.poetry.group.docs]
optional = true  # instalado com `poetry install --with docs`

[tool.poetry.group.docs.dependencies]
mkdocs-material = "^9.5.0"
mkdocstrings = { version = "^0.27.0", extras = ["python"] }

# ---------------------------------------------------------------- Ruff
[tool.ruff]
target-version = "py312"     # MUST corresponder ao limite inferior de requires-python
line-length = 88
src = ["src", "tests"]       # diretórios de código (classificação first-party dos imports)
extend-exclude = ["notebooks"]

[tool.ruff.lint]
select = [
    # Conjunto mínimo obrigatório
    "E",    # pycodestyle (erros)
    "W",    # pycodestyle (avisos)
    "F",    # pyflakes: nomes indefinidos, imports não utilizados
    "I",    # isort: ordenação de imports
    "N",    # pep8-naming
    "UP",   # pyupgrade: sintaxe moderna para o target-version
    "B",    # flake8-bugbear: bugs prováveis
    "C4",   # flake8-comprehensions
    # Regras adicionais adotadas pelo time
    "SIM",  # flake8-simplify
    "RET",  # flake8-return
    "PTH",  # flake8-use-pathlib
    "BLE",  # flake8-blind-except: `except Exception` sem tratamento
    "T20",  # flake8-print: proíbe print()
    "S",    # flake8-bandit: segurança (eval, segredos, subprocess...)
    "PT",   # flake8-pytest-style
    "D",    # pydocstyle (PEP 257)
    "TID",  # flake8-tidy-imports: proíbe imports relativos (EST-13)
    "RUF",  # regras do Ruff (inclui RUF100: noqa sem uso)
]
ignore = [
    "E501",  # comprimento de linha: gerenciado pelo formatador
    "D100",  # docstring de módulo: opcional
    "D104",  # docstring de pacote (__init__.py): opcional
    "D105",  # docstring de métodos mágicos: opcional
    "D107",  # docstring de __init__: documentar na classe
    "D206",  # conflita com o formatador
    "D300",  # conflita com o formatador
    "W191",  # conflita com o formatador
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = [
    "S101",  # assert é o mecanismo do pytest
    "D",     # docstrings não exigidas em testes
]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.isort]
known-first-party = ["meu_projeto"]

[tool.ruff.lint.flake8-tidy-imports]
ban-relative-imports = "all"

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
docstring-code-format = true

# ---------------------------------------------------------------- Pytest
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
addopts = [
    "-ra",
    "--strict-markers",
    "--strict-config",
    "--import-mode=importlib",
    "--cov=src/meu_projeto",
    "--cov-report=term-missing",
    "--cov-fail-under=50",
]
markers = [
    "integration: testes que dependem de recursos externos ou de execução ponta a ponta",
]

# ---------------------------------------------------------------- Coverage
[tool.coverage.run]
branch = true

[tool.coverage.report]
fail_under = 50
show_missing = true
exclude_also = [
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
    "raise NotImplementedError",
]
```

**Pontos de consistência que MUST ser mantidos:**

- `target-version` do Ruff = limite inferior de `requires-python` (`py312` ↔ `>=3.12`).
- `known-first-party` usa o **nome do pacote importável** (`meu_projeto`) e `--cov=` usa o **caminho** do pacote (`src/meu_projeto`); nenhum dos dois usa o nome do projeto (`meu-projeto`).
- A cobertura fica em `addopts`, então `poetry run pytest tests/unit/` já aplica o limite de 50%. Testes de integração e execuções focadas **MUST** rodar com `--no-cov`, para não inflar nem quebrar o limite.
- As regras do conjunto mínimo obrigatório do Ruff (`E`, `W`, `F`, `I`, `N`, `UP`, `B`, `C4`) **MUST NOT** ser removidas do `select`.

---

## 8. Qualidade de código com Ruff

### 8.1 Regras

| ID | Nível | Regra |
| --- | --- | --- |
| LNT-01 | MUST | Usar Ruff para lint, formatação e organização de imports, configurado em `[tool.ruff]` no `pyproject.toml`. O padrão PEP 8 é obrigatório e verificado pelo Ruff. |
| LNT-02 | MUST | `poetry run ruff check .` e `poetry run ruff format --check .` **MUST** passar sem erros antes de abrir um PR ou considerar uma tarefa concluída. A CI bloqueia merges com falha de lint. |
| LNT-03 | MUST | Remover imports não utilizados (regra `F401`) e manter imports ordenados (regras `I`): biblioteca padrão, terceiros e, por último, o próprio projeto. Ambos são corrigidos por `ruff check --fix`. |
| LNT-04 | MUST NOT | Usar Black, isort, flake8, pylint, autoflake ou pyupgrade para responsabilidades já cobertas pelo Ruff. |
| LNT-05 | MUST | Declarar explicitamente `select`, `target-version` e `src`. Não depender de padrões implícitos. |
| LNT-06 | MUST | Justificar cada supressão. Use `# noqa: <CÓDIGO>` com o código específico e, na mesma linha ou na anterior, o motivo. `# noqa` sem código **MUST NOT** ser usado. |
| LNT-07 | SHOULD | Preferir supressão pontual (`# noqa: CÓDIGO`) a `per-file-ignores`. Use `per-file-ignores` apenas para categorias inteiras de arquivos (como `tests/`). |
| LNT-08 | MUST | Revisar o diff gerado por `ruff check --fix`. Correções automáticas não substituem a análise de lógica. `--unsafe-fixes` **MUST NOT** ser aplicado sem revisão linha a linha. |

### 8.2 Comandos

```bash
poetry run ruff check .                          # lint
poetry run ruff check . --fix                    # lint com correções seguras (inclui imports)
poetry run ruff format .                         # formata
poetry run ruff format --check .                 # verifica formatação sem alterar (CI)
poetry run ruff check . --output-format=github   # anotações no PR (GitHub Actions)
poetry run ruff rule BLE001                      # explica uma regra
```

**Ordem local recomendada:** `ruff check . --fix` → `ruff format .` → `ruff check .`. O formatador pode reorganizar código que o linter verifica.

### 8.3 Supressão: correto × incorreto

```python
# ✅ Correto: código específico + justificativa
resultado = subprocess.run(comando, check=True)  # noqa: S603 - comando montado de lista fixa, sem entrada do usuário

# ❌ Incorreto: supressão genérica, sem motivo
resultado = subprocess.run(comando, shell=True)  # noqa
```

---

## 9. Testes automatizados e cobertura

### 9.1 Regras

| ID | Nível | Regra |
| --- | --- | --- |
| TST-01 | MUST | Usar Pytest, executado sempre via `poetry run pytest`. Testes em `tests/unit/` e, quando houver, `tests/integration/`, cada pasta com `__init__.py`. |
| TST-02 | MUST | Nomear arquivos `test_*.py` e funções `test_*`. Nomes **SHOULD** descrever o comportamento (`test_validar_registro_com_valor_negativo_levanta_erro`). |
| TST-03 | MUST | A suíte unitária **MUST** atingir cobertura ≥ 50%, medida com `pytest-cov` sobre o pacote de produção (`--cov=src/meu_projeto` em `addopts`). A CI **MUST** falhar abaixo desse limite (`--cov-fail-under=50`). Reduções de cobertura em PR **MUST** ser justificadas. |
| TST-04 | MUST | Testes unitários **MUST** ser rápidos (< 1 s cada), determinísticos, independentes de ordem e sem acesso a rede, bancos, serviços de nuvem ou arquivos fora de `tmp_path`. |
| TST-05 | MUST | Marcar testes de integração com `@pytest.mark.integration` e mantê-los em `tests/integration/`. |
| TST-06 | MUST | Testar sucesso, falhas esperadas (`pytest.raises`), limites (vazio, um elemento, valores extremos) e dados inválidos nas funções de validação e transformação. |
| TST-07 | SHOULD | Usar fixtures para cenários reutilizáveis e `@pytest.mark.parametrize` para variações de entrada, com `pytest.param(..., id="...")` para legibilidade. Fixtures compartilhadas ou de escopo amplo (`module`, `session`) ficam em `conftest.py`. |
| TST-08 | SHOULD | Isolar dependências externas por injeção. Use `pytest-mock` (`mocker`), `monkeypatch` ou `unittest.mock` para simular dependências; para contratos `ABC`, prefira `mocker.create_autospec(Contrato, instance=True)`. |
| TST-09 | MUST NOT | Usar credenciais reais, dados pessoais reais ou cópias de dados de produção em testes. Use dados sintéticos e amostras pequenas e representativas. |
| TST-10 | MUST | Calcular a cobertura somente sobre o pacote de produção. Os próprios testes **MUST NOT** entrar no cálculo. |
| TST-11 | MUST | Exclusões de cobertura (`# pragma: no cover`, `exclude_also`, `omit`) **MUST** ser explícitas, pontuais e justificadas em comentário. |
| TST-12 | SHOULD | Regras de negócio, validações, transformações e tratamento de erros **SHOULD** ter testes dedicados, independentemente do percentual global. |
| TST-13 | MUST | Corrigir um bug sempre com um teste que o reproduz. |

> **Cobertura não é qualidade.** 50% é um piso mínimo, não uma meta. Um teste sem asserção relevante aumenta a cobertura e não protege nada. O revisor **MUST** avaliar se os testes verificam comportamento (valores retornados, exceções, efeitos), e não apenas se executam linhas.
>
> Com `branch = true`, o percentual combina linhas e ramificações, o que torna o limite mais rigoroso.

### 9.2 Comandos

```bash
# Suíte unitária com cobertura (mesmo comando da CI; --cov vem de addopts)
poetry run pytest tests/unit/

# Relatório HTML adicional (MAY)
poetry run pytest tests/unit/ --cov-report=html

# Testes de integração (sem cobertura; exigem o ambiente descrito em docs/docs/running-tests.md)
poetry run pytest tests/integration/ -m integration --no-cov

# Execução focada durante o desenvolvimento (sem o limite de cobertura)
poetry run pytest tests/unit/test_domain_validacao_vendas.py -k negativo -x --no-cov
```

> Rodar um único arquivo com o limite ativo falha por cobertura baixa; por isso a execução focada usa `--no-cov`.

### 9.3 Organização

```text
tests/
├── __init__.py
├── conftest.py                       # fixtures compartilhadas (sem lógica de negócio)
├── unit/
│   ├── __init__.py
│   ├── test_domain_validacao_vendas.py
│   ├── test_domain_servicos.py
│   ├── test_processing_vendas.py
│   ├── test_ingestion_armazenamento.py
│   └── test_utils_config.py
└── integration/
    ├── __init__.py
    └── test_pipeline_vendas.py
```

Exemplos completos estão na [seção 15](#15-exemplos-de-implementação-corretos-e-incorretos).

---

## 10. Documentação com MkDocs Material

### 10.1 Regras

| ID | Nível | Regra |
| --- | --- | --- |
| DOC-01 | MUST | Usar MkDocs com o tema Material, configurado em `docs/mkdocs.yml`, com conteúdo Markdown em `docs/docs/`, versionado junto ao código. |
| DOC-02 | MUST | Manter no mínimo as seis páginas da [seção 10.3](#103-conteúdo-mínimo-das-páginas): `index.md`, `architecture.md`, `project-structure.md`, `running-locally.md`, `running-tests.md` e `contributing.md`. |
| DOC-03 | MUST | `poetry run mkdocs build -f docs/mkdocs.yml --strict` **MUST** passar localmente e na CI. Links quebrados, âncoras inválidas e páginas fora da navegação são erros. |
| DOC-04 | MUST | Documentar cada pipeline em `docs/docs/pipelines/<nome>.md` usando o modelo da [seção 12.3](#123-modelo-de-documentação-de-pipeline). |
| DOC-05 | MUST | Atualizar a documentação no mesmo PR que altera comportamento, arquitetura, configuração, comandos ou contratos de dados e de interface. |
| DOC-06 | MUST | Usar links internos relativos para arquivos `.md` (`[Arquitetura](architecture.md)`), nunca URLs absolutas do site publicado. |
| DOC-07 | SHOULD | Manter exemplos de código executáveis e atualizados. Para trechos longos, **MAY** incluir arquivos reais do repositório com `pymdownx.snippets` em vez de copiar o código. |
| DOC-08 | MAY | Gerar páginas de referência a partir de docstrings com `mkdocstrings[python]` quando houver API pública relevante (bibliotecas internas, módulos reutilizados por outros times). |
| DOC-09 | MUST | Registrar decisões arquiteturais relevantes (escolha de framework, desvio da estrutura padrão, mudança de regra MUST) como ADR em `docs/docs/adr/NNNN-titulo.md`. |

**MkDocs Material não é um gerador automático de documentação de API.** Ele renderiza Markdown escrito pelo time. Arquitetura, decisões, operação e contratos de dados são escritos manualmente. A referência gerada (`mkdocstrings`) complementa esse conteúdo e não o substitui.

### 10.2 `docs/mkdocs.yml` de referência

```yaml
site_name: Meu Projeto
site_description: Pipelines de dados de vendas.
repo_url: https://github.com/minha-org/meu-projeto  # ilustrativo
repo_name: minha-org/meu-projeto
docs_dir: docs   # relativo a este arquivo: docs/docs/
site_dir: site   # build em docs/site/ (ignorado no Git)

theme:
  name: material
  language: pt
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.top
    - search.highlight
    - content.code.copy

nav:
  - Início: index.md
  - Arquitetura: architecture.md
  - Estrutura do Projeto: project-structure.md
  - Como Rodar Local: running-locally.md
  - Como Rodar Testes: running-tests.md
  - Como Contribuir: contributing.md
  - Pipelines:
      - Receita diária: pipelines/receita_diaria.md
  - Referência:
      - Validação: reference/validacao.md

plugins:
  - search
  - mkdocstrings:          # remova se não usar referência gerada (DOC-08)
      handlers:
        python:
          paths: [../src]  # relativo a docs/mkdocs.yml
          options:
            docstring_style: google
            show_source: false

markdown_extensions:
  - admonition
  - attr_list
  - toc:
      permalink: true
  - pymdownx.details
  - pymdownx.highlight
  - pymdownx.inlinehilite
  - pymdownx.superfences
  - pymdownx.tabbed:
      alternate_style: true

validation:               # com --strict, cada warn vira erro de build
  omitted_files: warn
  absolute_links: warn
  unrecognized_links: warn
  anchors: warn
```

Página de referência gerada (`docs/docs/reference/validacao.md`):

```markdown
# Validação

::: meu_projeto.domain.validacao_vendas
```

### 10.3 Conteúdo mínimo das páginas

| Página | Conteúdo esperado |
| --- | --- |
| `index.md` | Propósito, contexto e links rápidos. |
| `architecture.md` | Diagrama de camadas e componentes, fluxo de dados, injeção de dependências e decisões técnicas (com links para os ADRs). |
| `project-structure.md` | Árvore de diretórios comentada. |
| `running-locally.md` | Pré-requisitos (versões do Python e do Poetry), `poetry install --with docs`, cópia do `.env.example` para `.env`, execução (`poetry run meu-projeto --data AAAA-MM-DD`), documentação local (`poetry run mkdocs serve -f docs/mkdocs.yml`, em `http://127.0.0.1:8000`) e solução de problemas ([seção 18](#18-solução-de-problemas-comuns)). |
| `running-tests.md` | Comandos de teste, lint e formatação ([seção 14](#14-fluxo-de-desenvolvimento-e-validação)), flags (`-m integration`, `--no-cov`) e como interpretar o relatório de cobertura. |
| `contributing.md` | Fluxo de branch e PR, modelo de descrição e checklist ([seção 14.5](#145-pull-requests)). |

### 10.4 Comandos

```bash
poetry add --group docs mkdocs-material "mkdocstrings[python]"
poetry install --with docs
poetry run mkdocs serve -f docs/mkdocs.yml           # servidor local com recarga automática
poetry run mkdocs build -f docs/mkdocs.yml --strict  # build de validação (CI)
```

---

## 11. Boas práticas de Python

### 11.1 Regras

| ID | Nível | Regra | Verificação |
| --- | --- | --- | --- |
| PY-01 | MUST | Seguir a PEP 8, conforme aplicada pela configuração do Ruff. | Ruff |
| PY-02 | MUST | Documentar funções, classes e métodos públicos com docstrings no estilo Google (PEP 257). | Ruff `D` |
| PY-03 | MUST | Usar type hints (PEP 484 e sintaxe moderna: `list[str]`, `X \| None`, `collections.abc`) em todas as funções e métodos, inclusive privados e testes. | Revisão; mypy (SHOULD) |
| PY-04 | MUST | Usar nomes claros e consistentes: `snake_case` para variáveis, funções, métodos, módulos e pacotes; `PascalCase` para classes; `UPPER_SNAKE_CASE` para constantes. O idioma dos identificadores (português ou inglês) **MUST** ser consistente dentro do projeto. | Ruff `N`, revisão |
| PY-05 | SHOULD | Preferir funções puras. Isolar efeitos colaterais nas bordas (I/O, rede, relógio). | Revisão |
| PY-06 | MUST | Usar context managers (`with`) para arquivos, conexões, locks e recursos com liberação obrigatória. | Ruff `SIM115`, revisão |
| PY-07 | MUST | Capturar exceções específicas. `except Exception` só **MAY** aparecer em fronteiras (ponto de entrada, loop de worker) e com registro (`logger.exception`) ou re-raise. | Ruff `BLE`, `E722` |
| PY-08 | MUST NOT | Capturar exceções para ignorá-las (`except ...: pass`) sem justificativa explícita em comentário. | Ruff `S110`, `SIM105`, revisão |
| PY-09 | MUST | Encadear exceções ao traduzi-las (`raise NovoErro(...) from exc`). | Ruff `B904` |
| PY-10 | MUST | Usar `logging` para observabilidade. `print()` **MUST NOT** aparecer em código de produção, exceto para saída intencional de CLI (com `# noqa: T201` justificado). | Ruff `T20` |
| PY-11 | MUST | Obter loggers por módulo com `get_logger(__name__)` de `utils/logger.py` ([seção 13.1](#131-logger-utilsloggerpy)). Handler e formato são configurados uma única vez, no ponto de entrada, com `configurar_logging`. | Revisão |
| PY-12 | MUST NOT | Usar estado global mutável ou argumentos default mutáveis. | Ruff `B006`, `B008`, revisão |
| PY-13 | SHOULD | Usar `pathlib.Path` em vez de `os.path` e strings para caminhos. | Ruff `PTH` |
| PY-14 | SHOULD | Usar `dataclasses` (de preferência `frozen=True, slots=True`) para estruturas de dados e `Enum` para conjuntos fechados de valores. Para validar payloads externos complexos (por exemplo, JSON de API), **MAY** usar `pydantic`, com justificativa (DEP-10). | Revisão |
| PY-15 | MUST NOT | Usar valores mágicos repetidos. Extraia constantes nomeadas ou `Enum`. | Revisão |
| PY-16 | MUST NOT | Usar `eval`, `exec`, `pickle` de fontes não confiáveis, `yaml.load` sem `SafeLoader` ou `subprocess` com `shell=True` sobre entrada externa. | Ruff `S` |
| PY-17 | SHOULD | Usar `Decimal` para valores monetários e `datetime` com timezone (`datetime.now(tz=UTC)`) para timestamps. | Ruff `DTZ` (MAY ativar), revisão |
| PY-18 | SHOULD | Adotar mypy para checar os type hints. Se adotado, **MUST** rodar na CI. | CI |
| PY-19 | SHOULD NOT | Duplicar lógica. Antes de escrever, procure implementação equivalente no projeto. | Revisão |

### 11.2 Como escolher entre abordagens válidas

Quando houver mais de uma solução correta, escolha a primeira que atender, nesta ordem:

1. **Biblioteca padrão** antes de dependência externa (`csv`, `json`, `dataclasses`, `pathlib`, `itertools`, `logging`).
2. **Função** antes de classe. Use classe quando houver estado coeso ou várias operações sobre os mesmos dados.
3. **Composição** antes de herança.
4. **Explícito** antes de implícito (parâmetro em vez de variável global; retorno em vez de mutação).
5. **Menos código para manter**, desde que legível. Não sacrifique clareza por concisão.

---

## 12. Padrões de Engenharia de Dados

### 12.1 Regras

| ID | Nível | Regra |
| --- | --- | --- |
| DAD-01 | MUST | Validar os dados na fronteira de entrada (após a leitura, antes da transformação), convertendo registros brutos em tipos de domínio. |
| DAD-02 | MUST | Definir schemas e contratos explícitos: campos, tipos, nulidade, chaves, unidades e regras de negócio, no código (`dataclass`, validadores) e na documentação do pipeline. |
| DAD-03 | MUST | Definir a política para registros inválidos: rejeitar e contar, enviar para quarentena ou falhar a execução. A política **MUST** estar documentada. Registros inválidos **MUST NOT** ser descartados silenciosamente. |
| DAD-04 | MUST | Tratar duplicidades com chave de deduplicação documentada. |
| DAD-05 | MUST | Separar regras de negócio de detalhes de infraestrutura. Uma transformação não sabe se os dados vieram de CSV, banco ou API. |
| DAD-06 | SHOULD | Tornar a persistência idempotente: sobrescrita atômica de partição, `MERGE`/upsert por chave ou escrita em local temporário seguida de substituição. Reexecutar com os mesmos parâmetros **MUST** produzir o mesmo resultado. |
| DAD-07 | MUST | Parametrizar execuções por data ou intervalo de referência explícito, em vez de “agora”, para permitir reprocessamento previsível. |
| DAD-08 | MUST | Registrar logs úteis: início e fim, parâmetros da execução, contagens (lidos, válidos, rejeitados, gravados), destino e duração. |
| DAD-09 | MUST NOT | Registrar em logs dados pessoais, credenciais, tokens ou conteúdo de registros sensíveis. Registre identificadores técnicos e contagens. |
| DAD-10 | SHOULD | Considerar volume, particionamento, processamento incremental e memória. Prefira iteradores e lotes a carregar o conjunto inteiro quando o volume não for comprovadamente pequeno. |
| DAD-11 | MUST | Definir timeout explícito em toda chamada a serviço externo (HTTP, banco, storage). |
| DAD-12 | SHOULD | Aplicar retry com backoff e número máximo de tentativas apenas a erros transitórios e a operações idempotentes. Cada tentativa **SHOULD** ser logada. |
| DAD-13 | MUST | Documentar premissas, granularidade, periodicidade, dependências upstream e downstream e procedimento de reprocessamento (modelo em [12.3](#123-modelo-de-documentação-de-pipeline)). |
| DAD-14 | MUST | Testar transformações com amostras pequenas e casos extremos: entrada vazia, nulos, duplicados, limites de data e valores negativos ou zero. |
| DAD-15 | MUST NOT | Assumir que todo projeto precisa de arquitetura distribuída, data lake ou orquestrador. Comece pela solução mais simples que atenda volume e SLA. |

### 12.2 Idempotência: padrões aceitos

| Destino | Padrão |
| --- | --- |
| Arquivos / object storage | Escrever em caminho temporário e substituir o destino da partição (`data=AAAA-MM-DD/`) por inteiro. |
| Banco relacional | `MERGE` / `INSERT ... ON CONFLICT` por chave natural, ou `DELETE` da partição + `INSERT` na mesma transação. |
| APIs externas | Chave de idempotência suportada pela API, ou verificação de existência antes do envio. |

### 12.3 Modelo de documentação de pipeline

```markdown
# Pipeline: receita diária

| Item | Descrição |
| --- | --- |
| Objetivo | Receita total por dia a partir dos pedidos. |
| Fonte | `vendas_AAAAMMDD.csv` no diretório de entrada. |
| Destino | `data=AAAA-MM-DD/receita.csv` no diretório de saída. |
| Granularidade | Uma linha por data. |
| Periodicidade | Diária, após a disponibilização do arquivo de vendas. |
| Chave de deduplicação | `id_pedido` (primeira ocorrência prevalece). |
| Registros inválidos | Rejeitados, contados e logados; a execução continua. |
| Idempotência | A partição de destino é sobrescrita atomicamente. |
| Reprocessamento | `poetry run meu-projeto --data AAAA-MM-DD`. |
| Dependências | Upstream: exportação de vendas. Downstream: painel financeiro. |

## Contrato de entrada

| Campo | Tipo | Obrigatório | Regra |
| --- | --- | --- | --- |
| id_pedido | texto | sim | não vazio |
| data | data ISO 8601 | sim | `AAAA-MM-DD` |
| valor | decimal | sim | finito e ≥ 0 |
```

---

## 13. Configuração e segurança

| ID | Nível | Regra |
| --- | --- | --- |
| SEG-01 | MUST | Centralizar configurações em `utils/config.py`, com valores padrão explícitos para as não sensíveis. Nunca escrever credenciais, URLs de banco, chaves de API ou configurações sensíveis no código. |
| SEG-02 | MUST | Ler parâmetros específicos de ambiente (caminhos, URLs, credenciais) de variáveis de ambiente, carregadas do `.env` com `python-dotenv` (`load_dotenv()`), ou de um gerenciador de segredos, uma única vez, no ponto de entrada. `load_dotenv()` **MUST NOT** ser chamado na importação de módulos. |
| SEG-03 | MUST | Validar configurações obrigatórias na inicialização e falhar com mensagem clara que indique o **nome** da variável ausente ou inválida, nunca o valor. |
| SEG-04 | MUST | Manter `.env` fora do versionamento (`.gitignore`). |
| SEG-05 | MUST | Fornecer `.env.example` com todas as variáveis esperadas e valores fictícios. |
| SEG-06 | MUST NOT | Versionar credenciais, tokens, chaves privadas, strings de conexão com senha ou dados sensíveis. |
| SEG-07 | MUST NOT | Incluir segredos em logs, mensagens de exceção, relatórios de teste ou na representação (`repr`) de objetos de configuração. Campos sensíveis em dataclasses **MUST** usar `field(repr=False)`. |
| SEG-08 | MUST | Fixar dependências via `poetry.lock` e revisar no PR as mudanças no lock. |
| SEG-09 | MAY | Auditar vulnerabilidades com `poetry run pip-audit` quando exigido pelo projeto ou pela área de segurança. Se adotado, **MUST** rodar na CI. |
| SEG-10 | MUST | Ativar o hook `detect-secrets` no pre-commit, com `.secrets.baseline` versionado, e a varredura de segredos da plataforma Git, quando disponível. Vazamento acidental de segredo é incidente de segurança: revogar a credencial imediatamente e avisar o time. |
| SEG-11 | MAY | Usar `pydantic-settings` para configurações com muitos campos, tipos complexos ou múltiplas fontes. Para poucos campos, `dataclass` + `os.environ` (após `load_dotenv()`) basta. |
| SEG-12 | MUST | Suportar os ambientes `development` (local, dados sintéticos ou amostras), `staging` (espelho de produção) e `production`, selecionados pela variável `ENVIRONMENT` (padrão `development`). Ela controla comportamentos por ambiente, como nível de log, endpoints e parâmetros de performance. Valor fora da lista é erro de configuração (SEG-03). |

`.gitignore` mínimo:

```gitignore
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.mypy_cache/
.coverage
coverage.xml
htmlcov/
site/
docs/site/
dist/
.env
*.pem
*.key
*.secret
credentials.json
```

`.env.example`:

```dotenv
ENVIRONMENT=development
MEU_PROJETO_ENTRADA=/caminho/para/entrada
MEU_PROJETO_SAIDA=/caminho/para/saida
MEU_PROJETO_NIVEL_LOG=INFO
```

### 13.1 Logger: `utils/logger.py`

```python
import logging
import sys

FORMATO = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
FORMATO_DATA = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    """Retorna o logger do módulo `name`, sem configurar handlers."""
    return logging.getLogger(name)


def configurar_logging(nivel: str = "INFO") -> None:
    """Configura o handler único da aplicação. Chamar apenas no ponto de entrada."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt=FORMATO, datefmt=FORMATO_DATA))
    raiz = logging.getLogger()
    raiz.handlers[:] = [handler]
    raiz.setLevel(nivel)
```

Uso: `logger = get_logger(__name__)` no topo de cada módulo; `configurar_logging(config.nivel_log)` apenas no ponto de entrada. Assim, não há handlers duplicados nem configuração na importação (EST-12).

---

## 14. Fluxo de desenvolvimento e validação

### 14.1 Fluxo mínimo (local = CI)

| # | Etapa | Comando | Obrigatória |
| --- | --- | --- | --- |
| 1 | Consistência do lock | `poetry check --lock` | MUST |
| 2 | Instalação reprodutível | `poetry install --with docs` | MUST |
| 3 | Lint | `poetry run ruff check .` | MUST |
| 4 | Formatação | `poetry run ruff format --check .` | MUST |
| 5 | Testes unitários + cobertura ≥ 50% | `poetry run pytest tests/unit/` (cobertura via `addopts`) | MUST |
| 6 | Documentação | `poetry run mkdocs build -f docs/mkdocs.yml --strict` | MUST |
| 7 | Tipagem | `poetry run mypy src` | Se configurado (PY-18) |
| 8 | Vulnerabilidades | `poetry run pip-audit` | Se configurado (SEG-09) |
| 9 | Integração | `poetry run pytest tests/integration/ -m integration --no-cov` | Se houver ambiente disponível |

```bash
poetry check --lock
poetry install --with docs
poetry run ruff check .
poetry run ruff format --check .
poetry run pytest tests/unit/
poetry run mkdocs build -f docs/mkdocs.yml --strict
```

| ID | Nível | Regra |
| --- | --- | --- |
| CI-01 | MUST | A CI executa as etapas 1–6 em todo PR e em todo push para a branch principal. |
| CI-02 | MUST | Qualquer falha de etapa falha o pipeline de CI. Nenhuma etapa usa `continue-on-error` ou equivalente. |
| CI-03 | MUST | A CI instala dependências exclusivamente com Poetry, a partir do `poetry.lock` versionado. |
| CI-04 | SHOULD | Fixar a versão do Poetry usada na CI e documentá-la em `docs/docs/running-locally.md`. |
| CI-05 | SHOULD | Usar pre-commit ([seção 14.2](#142-pre-commit-pre-commit-configyaml)). O `rev` do hook do Ruff **MUST** ser a mesma versão do Ruff no `poetry.lock`, para que hook e CI apliquem as mesmas regras. |
| CI-06 | SHOULD | Executar testes de integração em job separado, com recursos efêmeros (containers, contas de teste) e sem bloquear a validação unitária. |
| CI-07 | MUST NOT | Duplicar ferramentas ou etapas sem benefício claro (por exemplo, rodar Ruff via pre-commit **e** via outra action de lint na mesma CI). |

### 14.2 pre-commit (`.pre-commit-config.yaml`)

Os hooks do Ruff vêm do repositório oficial `ruff-pre-commit`, e o `detect-secrets` bloqueia segredos antes do commit. Ao atualizar o Ruff com `poetry update ruff`, atualize também o `rev` do hook (CI-05).

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: check-merge-conflict
      - id: check-toml
      - id: check-yaml
      - id: check-added-large-files
      - id: end-of-file-fixer
      - id: trailing-whitespace

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.0  # MUST ser a versão do Ruff no poetry.lock (CI-05)
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: [--baseline, .secrets.baseline]

  - repo: local
    hooks:
      - id: poetry-check-lock
        name: poetry check --lock
        entry: poetry check --lock
        language: system
        files: ^(pyproject\.toml|poetry\.lock)$
        pass_filenames: false
```

```bash
poetry add --group dev pre-commit detect-secrets
poetry run detect-secrets scan > .secrets.baseline   # no PowerShell 5.1, rode no Git Bash: `>` grava UTF-16
poetry run pre-commit install
poetry run pre-commit run --all-files
```

### 14.3 GitHub Actions (`.github/workflows/ci.yml`)

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  validacao:
    runs-on: ubuntu-latest
    env:
      POETRY_VERSION: "2.1.3"  # versão adotada pelo time (CI-04)
    steps:
      - uses: actions/checkout@v4

      - name: Instalar Poetry (bootstrap da ferramenta, fora do projeto)
        run: pipx install "poetry==${POETRY_VERSION}"

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: poetry

      - name: Selecionar interpretador
        run: poetry env use python

      - name: Verificar consistência do lock
        run: poetry check --lock

      - name: Instalar dependências
        run: poetry install --with docs

      - name: Lint
        run: poetry run ruff check . --output-format=github

      - name: Formatação
        run: poetry run ruff format --check .

      - name: Testes unitários e cobertura (limite via addopts)
        run: poetry run pytest tests/unit/

      - name: Documentação
        run: poetry run mkdocs build -f docs/mkdocs.yml --strict
```

### 14.4 Fluxo de trabalho de uma alteração

1. Criar branch a partir da principal.
2. `poetry install --with docs` (ou `poetry sync --with docs` se o lock mudou).
3. Escrever ou ajustar o teste que descreve o comportamento esperado.
4. Implementar seguindo as seções 5, 6 e 11.
5. Atualizar a documentação afetada (DOC-05) e, se a mudança for de versão, o campo `version` (DEP-13).
6. Executar o fluxo da [seção 14.1](#141-fluxo-mínimo-local--ci).
7. Abrir o PR com a descrição da [seção 14.5](#145-pull-requests), incluindo justificativa de novas dependências e supressões e o resultado da validação.
8. Revisão por outra pessoa com a checklist da [seção 16](#16-checklist-de-revisão).

### 14.5 Pull Requests

| ID | Nível | Regra |
| --- | --- | --- |
| PR-01 | MUST NOT | Fazer merge direto na branch principal. Todo código entra por Pull Request. |
| PR-02 | MUST NOT | Aprovar o próprio Pull Request. |
| PR-03 | MUST NOT | Contornar checks de CI ou hooks (`--no-verify` ou equivalente). |
| PR-04 | MUST | Descrever o PR com o modelo abaixo. |

```markdown
## O que mudou
Resumo objetivo das alterações.

## Motivo
Contexto técnico ou de negócio da alteração.

## Como validar
Passos para reproduzir e verificar localmente.

## Checklist
- [ ] `poetry run ruff check .` e `poetry run ruff format --check .` passam
- [ ] `poetry run pytest tests/unit/` passa com cobertura ≥ 50%
- [ ] `poetry run mkdocs build -f docs/mkdocs.yml --strict` passa
- [ ] Documentação atualizada, se aplicável
- [ ] Novas dependências e supressões justificadas
- [ ] Nenhum segredo ou dado sensível incluído
```

---

## 15. Exemplos de implementação corretos e incorretos

Os exemplos a seguir formam um pipeline mínimo e coerente (pacote `meu_projeto`) que segue todas as regras deste documento. São **ilustrativos** quanto ao domínio e **normativos** quanto à forma.

### 15.1 Domínio: `src/meu_projeto/domain/vendas.py`

```python
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Venda:
    """Venda validada, na granularidade de um pedido."""

    id_pedido: str
    data: date
    valor: Decimal
```

### 15.2 Validação na fronteira: `src/meu_projeto/domain/validacao_vendas.py`

```python
from collections.abc import Mapping
from datetime import date
from decimal import Decimal, InvalidOperation

from meu_projeto.domain.vendas import Venda

CAMPOS_OBRIGATORIOS = frozenset({"id_pedido", "data", "valor"})


class RegistroInvalidoError(ValueError):
    """Registro de entrada não atende ao contrato de dados."""


def validar_registro(registro: Mapping[str, str]) -> Venda:
    """Converte um registro bruto em `Venda`, aplicando o contrato de entrada.

    Args:
        registro: Linha bruta lida da fonte.

    Returns:
        Venda validada.

    Raises:
        RegistroInvalidoError: Se houver campo ausente ou valor inválido.
    """
    ausentes = CAMPOS_OBRIGATORIOS - {
        campo for campo, valor in registro.items() if valor
    }
    if ausentes:
        msg = f"campos ausentes ou vazios: {sorted(ausentes)}"
        raise RegistroInvalidoError(msg)

    try:
        data = date.fromisoformat(registro["data"])
        valor = Decimal(registro["valor"])
    except (ValueError, InvalidOperation) as exc:
        msg = "data ou valor em formato inválido"
        raise RegistroInvalidoError(msg) from exc

    if not valor.is_finite() or valor < 0:
        msg = "valor deve ser finito e não negativo"
        raise RegistroInvalidoError(msg)

    return Venda(id_pedido=registro["id_pedido"], data=data, valor=valor)
```

### 15.3 Transformações puras: `src/meu_projeto/processing/vendas.py`

```python
from collections import defaultdict
from collections.abc import Iterable, Iterator
from datetime import date
from decimal import Decimal

from meu_projeto.domain.vendas import Venda


def remover_duplicadas(vendas: Iterable[Venda]) -> Iterator[Venda]:
    """Remove vendas repetidas por `id_pedido`, mantendo a primeira ocorrência."""
    vistos: set[str] = set()
    for venda in vendas:
        if venda.id_pedido not in vistos:
            vistos.add(venda.id_pedido)
            yield venda


def receita_por_dia(vendas: Iterable[Venda]) -> dict[date, Decimal]:
    """Agrega a receita total por data, em ordem cronológica."""
    totais: defaultdict[date, Decimal] = defaultdict(Decimal)
    for venda in vendas:
        totais[venda.data] += venda.valor
    return dict(sorted(totais.items()))
```

### 15.4 Ingestão em fluxo: `src/meu_projeto/ingestion/arquivos_csv.py`

```python
import csv
from collections.abc import Iterator
from pathlib import Path


def ler_registros(caminho: Path) -> Iterator[dict[str, str]]:
    """Lê um CSV linha a linha, sem carregar o arquivo inteiro em memória."""
    with caminho.open(newline="", encoding="utf-8") as arquivo:
        yield from csv.DictReader(arquivo)
```

### 15.5 Persistência idempotente: `src/meu_projeto/ingestion/armazenamento_local.py`

```python
import csv
from collections.abc import Mapping
from datetime import date
from decimal import Decimal
from pathlib import Path


def gravar_receita_diaria(destino: Path, receita: Mapping[date, Decimal]) -> None:
    """Grava a receita substituindo o arquivo de destino por inteiro.

    A escrita ocorre em arquivo temporário no mesmo diretório e termina com uma
    substituição, de modo que reexecuções produzem o mesmo resultado e leitores
    nunca observam um arquivo parcial.
    """
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_name(f"{destino.name}.tmp")
    with temporario.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["data", "receita"])
        for dia, valor in receita.items():
            escritor.writerow([dia.isoformat(), str(valor)])
    temporario.replace(destino)
```

### 15.6 Configuração validada: `src/meu_projeto/utils/config.py`

```python
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Self

VARIAVEIS_OBRIGATORIAS = ("MEU_PROJETO_ENTRADA", "MEU_PROJETO_SAIDA")
AMBIENTES = frozenset({"development", "staging", "production"})


class ConfiguracaoInvalidaError(RuntimeError):
    """Configuração obrigatória ausente ou inválida."""


@dataclass(frozen=True, slots=True)
class Configuracao:
    """Configuração de execução do pipeline."""

    diretorio_entrada: Path
    diretorio_saida: Path
    nivel_log: str = "INFO"
    ambiente: str = "development"

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Self:
        """Carrega e valida a configuração a partir de variáveis de ambiente.

        Args:
            env: Variáveis a usar. Quando omitido, usa `os.environ`, já preenchido
                pelo `load_dotenv()` do ponto de entrada.

        Raises:
            ConfiguracaoInvalidaError: Se alguma variável obrigatória estiver
                ausente ou se `ENVIRONMENT` não for um ambiente suportado.
        """
        env = os.environ if env is None else env
        ausentes = [nome for nome in VARIAVEIS_OBRIGATORIAS if not env.get(nome)]
        if ausentes:
            msg = f"variáveis de ambiente obrigatórias ausentes: {ausentes}"
            raise ConfiguracaoInvalidaError(msg)
        ambiente = env.get("ENVIRONMENT", "development")
        if ambiente not in AMBIENTES:
            msg = f"ENVIRONMENT inválido; use um de {sorted(AMBIENTES)}"
            raise ConfiguracaoInvalidaError(msg)
        return cls(
            diretorio_entrada=Path(env["MEU_PROJETO_ENTRADA"]),
            diretorio_saida=Path(env["MEU_PROJETO_SAIDA"]),
            nivel_log=env.get("MEU_PROJETO_NIVEL_LOG", "INFO"),
            ambiente=ambiente,
        )
```

### 15.7 Composição do pipeline: `src/meu_projeto/pipeline_vendas.py`

Fica na raiz do pacote porque liga `ingestion`, `domain` e `processing`; `domain` não pode importar `ingestion` (EST-07).

```python
from datetime import date
from pathlib import Path

from meu_projeto.domain.validacao_vendas import RegistroInvalidoError, validar_registro
from meu_projeto.domain.vendas import Venda
from meu_projeto.ingestion.armazenamento_local import gravar_receita_diaria
from meu_projeto.ingestion.arquivos_csv import ler_registros
from meu_projeto.processing.vendas import receita_por_dia, remover_duplicadas
from meu_projeto.utils.config import Configuracao
from meu_projeto.utils.logger import get_logger

logger = get_logger(__name__)


def executar(config: Configuracao, data_referencia: date) -> Path:
    """Processa a partição de `data_referencia` e retorna o caminho gravado.

    Idempotente: reexecutar com a mesma data sobrescreve a mesma partição.
    """
    origem = config.diretorio_entrada / f"vendas_{data_referencia:%Y%m%d}.csv"
    destino = (
        config.diretorio_saida / f"data={data_referencia.isoformat()}" / "receita.csv"
    )
    logger.info("iniciando pipeline: data=%s origem=%s", data_referencia, origem)

    validas: list[Venda] = []
    rejeitadas = 0
    for registro in ler_registros(origem):
        try:
            validas.append(validar_registro(registro))
        except RegistroInvalidoError:
            rejeitadas += 1

    receita = receita_por_dia(remover_duplicadas(validas))
    gravar_receita_diaria(destino, receita)

    logger.info(
        "pipeline concluído: data=%s validas=%d rejeitadas=%d destino=%s",
        data_referencia,
        len(validas),
        rejeitadas,
        destino,
    )
    return destino
```

> Para volumes que não cabem em memória, substitua a lista por um gerador encadeado. As transformações já aceitam `Iterable`, então não precisam mudar (ARQ-14).

### 15.8 Ponto de entrada: `src/meu_projeto/cli.py`

```python
import argparse
import sys
from datetime import date

from dotenv import load_dotenv

from meu_projeto import pipeline_vendas
from meu_projeto.utils.config import Configuracao, ConfiguracaoInvalidaError
from meu_projeto.utils.logger import configurar_logging, get_logger

logger = get_logger(__name__)


def main(argv: list[str] | None = None) -> int:
    """Executa o pipeline de receita diária. Retorna o código de saída do processo."""
    parser = argparse.ArgumentParser(description="Calcula a receita diária de vendas.")
    parser.add_argument(
        "--data",
        type=date.fromisoformat,
        required=True,
        help="Data de referência no formato AAAA-MM-DD.",
    )
    args = parser.parse_args(argv)

    configurar_logging()
    load_dotenv()  # lê o .env apenas no ponto de entrada (SEG-02)
    try:
        config = Configuracao.from_env()
    except ConfiguracaoInvalidaError:
        logger.exception("configuração inválida")
        return 2
    configurar_logging(config.nivel_log)

    try:
        pipeline_vendas.executar(config, args.data)
    except Exception:  # fronteira do processo: registra e sinaliza a falha
        logger.exception("falha na execução do pipeline")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### 15.9 Testes

`tests/conftest.py`:

```python
from datetime import date
from decimal import Decimal

import pytest

from meu_projeto.domain.vendas import Venda


@pytest.fixture
def vendas_exemplo() -> list[Venda]:
    return [
        Venda("P1", date(2026, 1, 1), Decimal("10.00")),
        Venda("P2", date(2026, 1, 1), Decimal("5.50")),
        Venda("P3", date(2026, 1, 2), Decimal("1.00")),
    ]
```

`tests/unit/test_domain_validacao_vendas.py`:

```python
from datetime import date
from decimal import Decimal

import pytest

from meu_projeto.domain.validacao_vendas import RegistroInvalidoError, validar_registro


def test_validar_registro_valido_retorna_venda() -> None:
    venda = validar_registro(
        {"id_pedido": "P1", "data": "2026-01-31", "valor": "10.50"}
    )

    assert venda.data == date(2026, 1, 31)
    assert venda.valor == Decimal("10.50")


@pytest.mark.parametrize(
    "registro",
    [
        pytest.param({"data": "2026-01-31", "valor": "1"}, id="sem-id"),
        pytest.param({"id_pedido": "P1", "data": "", "valor": "1"}, id="data-vazia"),
        pytest.param(
            {"id_pedido": "P1", "data": "31/01/2026", "valor": "1"},
            id="data-fora-do-padrao",
        ),
        pytest.param(
            {"id_pedido": "P1", "data": "2026-01-31", "valor": "abc"},
            id="valor-nao-numerico",
        ),
        pytest.param(
            {"id_pedido": "P1", "data": "2026-01-31", "valor": "-1"},
            id="valor-negativo",
        ),
        pytest.param(
            {"id_pedido": "P1", "data": "2026-01-31", "valor": "NaN"}, id="valor-nan"
        ),
    ],
)
def test_validar_registro_invalido_levanta_erro(registro: dict[str, str]) -> None:
    with pytest.raises(RegistroInvalidoError):
        validar_registro(registro)
```

`tests/unit/test_processing_vendas.py`:

```python
from datetime import date
from decimal import Decimal

from meu_projeto.domain.vendas import Venda
from meu_projeto.processing.vendas import receita_por_dia, remover_duplicadas


def test_receita_por_dia_agrega_por_data(vendas_exemplo: list[Venda]) -> None:
    assert receita_por_dia(vendas_exemplo) == {
        date(2026, 1, 1): Decimal("15.50"),
        date(2026, 1, 2): Decimal("1.00"),
    }


def test_receita_por_dia_com_entrada_vazia_retorna_vazio() -> None:
    assert receita_por_dia([]) == {}


def test_remover_duplicadas_mantem_primeira_ocorrencia(
    vendas_exemplo: list[Venda],
) -> None:
    duplicada = Venda("P1", date(2026, 1, 3), Decimal("99.00"))

    assert list(remover_duplicadas([*vendas_exemplo, duplicada])) == vendas_exemplo
```

`tests/unit/test_ingestion_armazenamento.py` (I/O isolado em `tmp_path`):

```python
from datetime import date
from decimal import Decimal
from pathlib import Path

from meu_projeto.ingestion.armazenamento_local import gravar_receita_diaria


def test_gravar_receita_diaria_e_idempotente(tmp_path: Path) -> None:
    destino = tmp_path / "data=2026-01-01" / "receita.csv"
    receita = {date(2026, 1, 1): Decimal("15.50")}

    gravar_receita_diaria(destino, receita)
    gravar_receita_diaria(destino, receita)

    assert destino.read_text(encoding="utf-8").splitlines() == [
        "data,receita",
        "2026-01-01,15.50",
    ]
    assert list(destino.parent.iterdir()) == [destino]
```

`tests/unit/test_utils_config.py` (dependência injetada, sem alterar o ambiente real):

```python
import pytest

from meu_projeto.utils.config import Configuracao, ConfiguracaoInvalidaError


def test_configuracao_sem_variaveis_obrigatorias_falha() -> None:
    with pytest.raises(ConfiguracaoInvalidaError, match="MEU_PROJETO_ENTRADA"):
        Configuracao.from_env({})


def test_configuracao_com_ambiente_invalido_falha() -> None:
    env = {"MEU_PROJETO_ENTRADA": "e", "MEU_PROJETO_SAIDA": "s", "ENVIRONMENT": "qa"}

    with pytest.raises(ConfiguracaoInvalidaError, match="ENVIRONMENT"):
        Configuracao.from_env(env)
```

`tests/unit/test_domain_servicos.py`: ver o exemplo com `pytest-mock` na [seção 6.3](#63-separação-entre-regra-de-negócio-e-infraestrutura).

`tests/integration/test_pipeline_vendas.py` (rodar com `--no-cov`):

```python
from datetime import date
from pathlib import Path

import pytest

from meu_projeto.pipeline_vendas import executar
from meu_projeto.utils.config import Configuracao


@pytest.mark.integration
def test_pipeline_ponta_a_ponta(tmp_path: Path) -> None:
    entrada = tmp_path / "entrada"
    entrada.mkdir()
    (entrada / "vendas_20260101.csv").write_text(
        "id_pedido,data,valor\n"
        "P1,2026-01-01,10.00\n"
        "P1,2026-01-01,10.00\n"  # duplicado: deve ser removido
        "P2,2026-01-01,-5\n",  # inválido: deve ser rejeitado
        encoding="utf-8",
    )
    config = Configuracao(diretorio_entrada=entrada, diretorio_saida=tmp_path / "saida")

    destino = executar(config, date(2026, 1, 1))

    assert destino.read_text(encoding="utf-8").splitlines() == [
        "data,receita",
        "2026-01-01,10.00",
    ]
```

### 15.10 Anti-padrões

**Gerenciamento de dependências**

```bash
# ❌ Incorreto (DEP-01, DEP-07)
pip install requests
python -m pip install -r requirements.txt
ruff check .                 # Ruff global, versão diferente do lock

# ✅ Correto
poetry add requests
poetry install
poetry run ruff check .
```

**Lógica no script, `print`, segredo, exceção engolida, estado global**

```python
# ❌ Incorreto
import os
import pandas as pd  # framework sem requisito (ARQ-15)

TOKEN = "sk_live_9f8a..."  # segredo no código (SEG-06)
resultados = []  # estado global mutável (PY-12)


def processa(arquivo, cache={}):  # default mutável, sem tipos (PY-03, PY-12)
    df = pd.read_csv(os.path.join("dados", arquivo))  # os.path (PY-13); tudo em memória
    for _, linha in df.iterrows():
        try:
            resultados.append(eval(linha["valor"]))  # eval (PY-16)
        except:  # except genérico (PY-07)
            pass  # erro ignorado (PY-08, DAD-03)
    print("ok", TOKEN)  # print + segredo em log (PY-10, SEG-07)
```

O correto é a separação mostrada em 15.2–15.8: validação tipada, transformação pura, I/O isolado, configuração injetada e logs sem dados sensíveis.

**Configuração e imports**

```python
# ❌ Incorreto: .env lido na importação, variável lida fora do ponto de entrada, import relativo
from dotenv import load_dotenv
from ..domain.vendas import Venda  # import relativo (EST-13)

load_dotenv()  # efeito colateral na importação (SEG-02, EST-12)
SAIDA = os.environ["MEU_PROJETO_SAIDA"]  # estado global lido na importação (ARQ-05)

# ✅ Correto: import absoluto; load_dotenv() e Configuracao.from_env() apenas no ponto de entrada
from meu_projeto.domain.vendas import Venda
```

**Tratamento de exceções**

```python
# ❌ Incorreto: perde a causa e a stack trace
try:
    valor = Decimal(bruto)
except Exception:
    raise ValueError("valor inválido")

# ✅ Correto: exceção específica, encadeada (PY-07, PY-09)
try:
    valor = Decimal(bruto)
except InvalidOperation as exc:
    msg = f"valor inválido no campo 'valor' (pedido {id_pedido})"
    raise RegistroInvalidoError(msg) from exc
```

**Logging**

```python
# ❌ Incorreto: dado pessoal e credencial em log (DAD-09, SEG-07); f-string formatada mesmo sem log ativo
logger.info(f"cliente {cliente.cpf} autenticado com senha {senha}")

# ✅ Correto: identificador técnico, formatação preguiçosa
logger.info("cliente autenticado: id_cliente=%s", cliente.id)
```

**Abstração prematura**

```python
# ❌ Incorreto: hierarquia para uma transformação pura, sem infraestrutura a isolar (ARQ-08)
class BaseTransformer(ABC):
    @abstractmethod
    def transform(self, data): ...


class ReceitaTransformer(BaseTransformer):
    def transform(self, data): ...


# ✅ Correto: uma função com contrato claro; ABCs ficam para fontes e destinos externos (6.3)
def receita_por_dia(vendas: Iterable[Venda]) -> dict[date, Decimal]: ...
```

**Testes**

```python
# ❌ Incorreto: executa linhas sem verificar comportamento; depende de rede e de dado real
def test_pipeline():
    executar(Configuracao.from_env(), date.today())


# ✅ Correto: entrada sintética, resultado verificado, sem dependência externa
def test_receita_por_dia_com_entrada_vazia_retorna_vazio() -> None:
    assert receita_por_dia([]) == {}
```

---

## 16. Checklist de revisão

Use a checklist em todo PR. Um item **MUST** não atendido bloqueia o merge.

**Estrutura e arquitetura**

- [ ] O código de produção está em `src/<pacote>/`, nas camadas `ingestion/`, `processing/`, `domain/` e `utils/`; testes em `tests/`; docs em `docs/` (EST-01, EST-02, EST-05).
- [ ] Cada módulo novo ou alterado tem responsabilidade única e nome específico (ARQ-01, EST-10).
- [ ] Não há imports circulares, a direção das dependências entre camadas é respeitada e os imports são absolutos (EST-07, EST-13).
- [ ] Não há lógica de negócio em `cli.py`, `__main__`, notebooks ou configuração (EST-08).
- [ ] Infraestrutura entra nos serviços por contratos injetados; não há outras abstrações, frameworks ou camadas sem justificativa (ARQ-08, ARQ-15).

**Contratos e código**

- [ ] Todas as funções têm type hints; as públicas têm docstrings com entradas, saídas e exceções (ARQ-04, PY-02, PY-03).
- [ ] Exceções são específicas, encadeadas e nunca silenciadas (PY-07, PY-08, PY-09).
- [ ] Logging via `get_logger`, sem `print` e sem dados sensíveis (PY-10, PY-11, DAD-09).
- [ ] Recursos usam context managers (PY-06).

**Dados**

- [ ] Dados são validados na entrada, com contrato documentado (DAD-01, DAD-02).
- [ ] A política de registros inválidos e de duplicidade está definida e documentada (DAD-03, DAD-04).
- [ ] Persistência e reprocessamento são idempotentes ou a limitação está documentada (DAD-06, DAD-07).
- [ ] Chamadas externas têm timeout; retries apenas para erros transitórios (DAD-11, DAD-12).

**Qualidade e testes**

- [ ] `poetry run ruff check .` e `poetry run ruff format --check .` passam (LNT-02).
- [ ] Cada supressão (`noqa`, `pragma: no cover`) tem código específico e justificativa (LNT-06, TST-11).
- [ ] Os testes relevantes foram criados ou atualizados e verificam comportamento, incluindo casos de erro e limites (TST-06, TST-12).
- [ ] A cobertura unitária é ≥ 50% e o limite não foi alterado (TST-03).
- [ ] Testes unitários não acessam rede, bancos ou serviços reais (TST-04).

**Dependências, configuração e segurança**

- [ ] Dependências foram alteradas apenas via Poetry; `poetry.lock` está atualizado e consistente (DEP-03, DEP-06, DEP-11).
- [ ] Cada nova dependência de produção tem justificativa (DEP-10).
- [ ] Não há segredos no código, nos testes, nos logs ou no histórico do PR; o `detect-secrets` passa (SEG-06, SEG-07, SEG-10).
- [ ] Novas variáveis de configuração estão no `.env.example` e são validadas na inicialização (SEG-03, SEG-05, SEG-12).

**Documentação**

- [ ] A documentação afetada foi atualizada no mesmo PR (DOC-05).
- [ ] `poetry run mkdocs build -f docs/mkdocs.yml --strict` passa (DOC-03).

**Pull Request**

- [ ] O PR segue o modelo da [seção 14.5](#145-pull-requests) e foi aprovado por outra pessoa (PR-01, PR-02, PR-04).
- [ ] Nenhum check ou hook foi contornado (PR-03).

---

## 17. Critérios objetivos de conclusão (Definition of Done)

Uma tarefa está **concluída** somente quando **todos** os itens abaixo são verdadeiros:

1. `poetry check --lock` termina com código 0.
2. `poetry run ruff check .` termina com código 0.
3. `poetry run ruff format --check .` termina com código 0.
4. `poetry run pytest tests/unit/` termina com código 0 (cobertura ≥ 50% via `addopts`).
5. `poetry run mkdocs build -f docs/mkdocs.yml --strict` termina com código 0.
6. Etapas opcionais configuradas no projeto (mypy, pip-audit, integração) terminam com código 0.
7. Todo comportamento novo ou alterado tem teste que falharia sem a alteração.
8. A documentação afetada foi atualizada.
9. Nenhuma supressão, exclusão de cobertura ou dependência nova ficou sem justificativa.
10. A CI do PR está verde e o PR foi aprovado por outra pessoa.

Para agentes de IA: ao entregar, informe o resultado de cada comando dos itens 1–6 (sucesso ou falha, com a saída relevante), liste as dependências adicionadas com justificativa e descreva as limitações conhecidas. **Não declare conclusão se qualquer item falhar.**

---

## 18. Solução de problemas comuns

| Sintoma | Causa provável | Solução |
| --- | --- | --- |
| `ModuleNotFoundError: meu_projeto` nos testes | Pacote não instalado no ambiente ou `packages` ausente | Conferir `[tool.poetry] packages` (EST-03) e executar `poetry install`. |
| Poetry instala em outro ambiente ou ignora o `.venv` do projeto | Variável `VIRTUAL_ENV` herdada de outro ambiente ativado; o Poetry usa o ambiente ativo | Desativar o ambiente ativo ou remover `VIRTUAL_ENV` da sessão antes de rodar `poetry`; conferir com `poetry env info`. |
| `pyproject.toml changed significantly since poetry.lock was last generated` | `pyproject.toml` editado sem atualizar o lock | `poetry lock` e versionar o lock (DEP-11). |
| Ruff classifica o próprio pacote como third-party | `src` ou `known-first-party` incorretos | Conferir `[tool.ruff] src` e `[tool.ruff.lint.isort] known-first-party`. |
| Cobertura 0% ou “module was never imported” | `--cov` com o nome do projeto (`meu-projeto`) ou caminho errado | Usar `--cov=src/meu_projeto` em `addopts`. |
| `Required test coverage of 50% not reached` ao rodar integração ou um único arquivo | O limite vem de `addopts` | Rodar com `--no-cov`. |
| `Config file 'mkdocs.yml' does not exist` | O MkDocs procura o arquivo na raiz | Passar `-f docs/mkdocs.yml`. |
| `mkdocs build --strict` falha com aviso de link | Link quebrado, âncora inexistente ou página fora do `nav` | Corrigir o link ou incluir a página no `nav` (DOC-03, DOC-06). |
| `mkdocs` não encontrado | Grupo opcional `docs` não instalado | `poetry install --with docs`. |
| Hooks do pre-commit falham com `poetry: command not found` | Poetry fora do `PATH` no shell usado pelo Git | Garantir o Poetry no `PATH` (instalação via instalador oficial ou `pipx`). |
| `detect-secrets` falha ao ler `.secrets.baseline` | Baseline gerado no PowerShell 5.1 (UTF-16) | Gerar de novo no Git Bash: `poetry run detect-secrets scan > .secrets.baseline`. |
| Comando com `\` falha no PowerShell | Continuação de linha diferente | Usar crase (`` ` ``) ou a forma em uma linha. |

---

## 19. Rastreabilidade: regra → verificação

| Regra | Como é verificada |
| --- | --- |
| DEP-05, DEP-06, DEP-11 | `poetry check --lock` (CI e pre-commit); revisão do diff do lock |
| DEP-01, DEP-07 | Revisão; ausência de `requirements*.txt` e de `pip install` em scripts, Dockerfiles, CI e documentação |
| EST-01, EST-03 | `poetry install` + importação nos testes; revisão |
| EST-13 | Ruff `TID252` (`ban-relative-imports = "all"`) |
| LNT-01 a LNT-05 | `ruff check` e `ruff format --check` na CI |
| PY-01, PY-02, PY-06 a PY-10, PY-12, PY-13, PY-16 | Regras do Ruff selecionadas em `[tool.ruff.lint]` |
| PY-03 | Revisão; mypy na CI quando adotado |
| TST-03, TST-10 | `--cov=src/meu_projeto --cov-fail-under=50` em `addopts`, executado na CI |
| TST-05 | `--strict-markers` + marcador `integration` declarado |
| DOC-03, DOC-06 | `mkdocs build -f docs/mkdocs.yml --strict` com `validation` configurado |
| SEG-04, SEG-06, SEG-10 | `.gitignore`, hook `detect-secrets`, regras `S` do Ruff (ex.: `S105`, `S106`), revisão |
| PR-01 a PR-03 | Proteção da branch principal na plataforma Git (PR obrigatório, aprovação de outra pessoa, checks obrigatórios) |
| ARQ-*, DAD-*, demais SHOULD | Checklist de revisão (seção 16) |
