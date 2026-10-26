# Como rodar localmente

## Pré-requisitos

- Python `>=3.12,<4.0` (desenvolvido com 3.12.10)
- Poetry `>=2.0` (desenvolvido com 2.5.1), instalado fora do projeto
- Acesso à internet (o dashboard consulta a OpenF1 na hora)

## Instalação

```bash
poetry env use 3.12
poetry install --with docs
```

!!! tip "Windows"
    Se outro ambiente virtual estiver ativo, o Poetry pode usá-lo por engano. Antes dos
    comandos, rode `Remove-Item Env:VIRTUAL_ENV -ErrorAction SilentlyContinue` e confira
    com `poetry env info`.

## Configuração (opcional)

Os valores padrão já funcionam. Para alterar, copie o exemplo e edite:

```bash
cp .env.example .env
```

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `OPENF1_BASE_URL` | `https://api.openf1.org/v1` | URL base da API |
| `OPENF1_TIMEOUT` | `10` | Timeout de cada requisição, em segundos |
| `ENVIRONMENT` | `development` | `development`, `staging` ou `production`; define o TTL do cache (1 h ou 24 h) |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` ou `CRITICAL` |

Valores inválidos impedem a inicialização com uma mensagem que cita o nome da variável.

## Executar o dashboard

```bash
poetry run streamlit run src/projetof1/dashboard/app.py
```

Abra `http://localhost:8501`.

## Documentação local

```bash
poetry run task docs                               # http://127.0.0.1:8000
poetry run mkdocs build -f docs/mkdocs.yml --strict
```

`poetry run task docs` é o atalho de `poetry run mkdocs serve -f docs/mkdocs.yml`. Os
demais atalhos (`test`, `lint`, `format`) estão em [Como rodar os testes](running-tests.md).

## Solução de problemas

| Sintoma | Solução |
| --- | --- |
| "Não foi possível consultar a OpenF1 agora" | A API falhou após 3 tentativas (rede ou limite de requisições). Aguarde e recarregue. |
| Aba com "Sem dados para esta sessão" | A OpenF1 não tem esse dado para a sessão (ex.: resultado de alguns treinos). |
| "Esta sessão ainda não aconteceu" | Escolha uma sessão anterior. |
| `'utf-8' codec can't decode byte 0xff` no `poetry install` | Algum arquivo (ex.: `README.md`) foi salvo em UTF-16 pelo PowerShell. Salve-o em UTF-8. |
| `Config file 'mkdocs.yml' does not exist` | Passe `-f docs/mkdocs.yml`. |
