# Estrutura do projeto

```text
projetoF1/
├── pyproject.toml              # metadados, dependências e config (Ruff, pytest, coverage)
├── poetry.lock                 # versões exatas (gerado pelo Poetry)
├── README.md                   # visão geral e início rápido
├── .env.example                # variáveis de ambiente esperadas (sem valores reais)
├── .gitignore
├── .pre-commit-config.yaml     # Ruff, detect-secrets e checagens básicas
├── .secrets.baseline           # baseline do detect-secrets
├── .streamlit/config.toml      # tema escuro com vermelho F1
├── src/projetof1/
│   ├── dashboard/
│   │   ├── app.py              # entrada do Streamlit: monta dependências e desenha a tela
│   │   ├── charts.py           # figuras Plotly (barras, ritmo, estratégia)
│   │   └── components.py       # cabeçalho, clima, pódio, tabelas e CSS
│   ├── domain/
│   │   ├── models.py           # payloads da OpenF1 (pydantic) e projeções (dataclasses)
│   │   ├── repositories.py     # contratos (ABCs), F1Repositories e DataSourceError
│   │   └── services.py         # F1DashboardService
│   ├── ingestion/
│   │   ├── http_client.py      # HttpClient: timeout, retry com backoff, 404 = vazio
│   │   └── openf1_repositories.py  # repositórios concretos + build_repositories
│   ├── processing/
│   │   ├── drivers.py          # índice de pilotos e piloto substituto
│   │   ├── laps.py             # voltas válidas, top N, ritmo, melhores setores
│   │   ├── stints.py           # linha do tempo de pneus e pit stops
│   │   ├── results.py          # classificação, status e último valor conhecido
│   │   ├── weather.py          # resumo do clima
│   │   └── formatting.py       # tempos, gaps, cores de equipe e de pneus
│   └── utils/
│       ├── config.py           # Settings e load_settings()
│       └── logger.py           # get_logger e configure_logging
├── tests/
│   ├── conftest.py             # fixtures e fábricas compartilhadas
│   ├── fixtures/               # JSON sintéticos por endpoint
│   ├── unit/                   # testes sem rede (cobertura >= 50%)
│   └── integration/            # testes contra a OpenF1 real (marcador integration)
└── docs/
    ├── mkdocs.yml              # configuração do MkDocs
    └── docs/                   # estas páginas
```
