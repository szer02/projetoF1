# ProjetoF1 Dashboard

[![CI](https://github.com/szer02/projetoF1/actions/workflows/ci.yml/badge.svg)](https://github.com/szer02/projetoF1/actions/workflows/ci.yml)
[![Docs](https://github.com/szer02/projetoF1/actions/workflows/docs.yml/badge.svg)](https://szer02.github.io/projetoF1/)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://f1projeto.streamlit.app/)

Dashboard interativo em Streamlit com dados históricos da Fórmula 1 (2023 em diante),
consumidos da [OpenF1 API](https://openf1.org/). Para cada sessão, mostra resultado,
voltas mais rápidas, ritmo volta a volta, estratégia de pneus e clima.

Desenvolvido como projeto da pós-graduação em Engenharia de Dados e IA.

**Veja o dashboard no ar:** <https://f1projeto.streamlit.app/>

## Tecnologias

| Categoria | Ferramenta |
| --- | --- |
| Linguagem | Python 3.12 |
| Dependências e ambiente | Poetry 2 |
| Dashboard | Streamlit |
| Gráficos | Plotly |
| Cliente HTTP | httpx (timeout e retry com backoff) |
| Validação dos dados | pydantic v2 |
| Configuração | python-dotenv |
| Testes | pytest, pytest-cov, pytest-mock |
| Lint e formatação | Ruff |
| Qualidade nos commits | pre-commit, detect-secrets |
| Atalhos de comandos | taskipy |
| Documentação | MkDocs Material |

## Estrutura do projeto

```text
projetoF1/
├── src/projetof1/
│   ├── dashboard/        # tela Streamlit
│   │   ├── app.py        # ponto de entrada: monta as dependências e as abas
│   │   ├── charts.py     # gráficos Plotly
│   │   └── components.py # cards, tabelas e CSS
│   ├── domain/           # regras do negócio
│   │   ├── models.py     # modelos dos dados da API e do que aparece na tela
│   │   ├── repositories.py # contratos de acesso aos dados
│   │   └── services.py   # F1DashboardService: junta tudo para cada sessão
│   ├── ingestion/        # acesso à OpenF1
│   │   ├── http_client.py
│   │   └── openf1_repositories.py
│   ├── processing/       # cálculos (funções puras): voltas, stints, resultado, clima
│   └── utils/            # configuração (.env) e logging
├── tests/
│   ├── unit/             # sem acesso à rede
│   ├── integration/      # contra a API real
│   └── fixtures/         # JSONs de exemplo
├── docs/                 # documentação MkDocs
├── .streamlit/config.toml # tema do dashboard
├── .env.example          # variáveis de ambiente de exemplo
└── pyproject.toml        # dependências e configuração das ferramentas
```

O fluxo é: `dashboard` → `domain/services` → `ingestion` (busca na API) e
`processing` (calcula) → de volta para a tela. Detalhes em
[Arquitetura](docs/docs/architecture.md).

## Instalação

Requisitos: Python `>=3.12,<4.0` (desenvolvido com 3.12.10) e Poetry `>=2.0`.

```bash
git clone https://github.com/szer02/projetoF1.git
cd projetoF1
poetry install --with docs
poetry run pre-commit install
cp .env.example .env    # opcional: os valores padrão já funcionam
```

> No Windows, se outro ambiente virtual estiver ativo, rode antes
> `Remove-Item Env:VIRTUAL_ENV -ErrorAction SilentlyContinue`.

## Como executar o dashboard

```bash
poetry run streamlit run src/projetof1/dashboard/app.py
```

O dashboard abre em `http://localhost:8501`. Na barra lateral, escolha
**temporada → Grande Prêmio → sessão**.

Para só ver o resultado, sem instalar nada, acesse a versão publicada no Streamlit
Community Cloud: <https://f1projeto.streamlit.app/>.

## Testes

```bash
poetry run task test                                          # unitários + cobertura (mínimo 50%)
poetry run pytest tests/integration/ -m integration --no-cov  # integração, requer internet
```

## Lint e formatação

```bash
poetry run task lint      # verifica, sem alterar arquivos
poetry run task format    # corrige o que for seguro e formata
```

`poetry run task --list` mostra todos os atalhos.

## Documentação

```bash
poetry run task docs
```

Abre em `http://127.0.0.1:8000`, com arquitetura, estrutura, execução, testes e
contribuição. Os arquivos ficam em [`docs/docs/`](docs/docs/index.md).

A versão publicada fica em <https://szer02.github.io/projetoF1/>, atualizada
automaticamente pelo workflow **Docs** a cada push em `main` que altere a documentação.
