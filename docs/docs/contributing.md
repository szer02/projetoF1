# Como contribuir

## Fluxo

1. Crie uma branch a partir da `main`. Merge direto na `main` não é permitido.
2. Instale o ambiente: `poetry install --with docs` e `poetry run pre-commit install`.
3. Escreva ou ajuste o teste que descreve o comportamento esperado.
4. Implemente respeitando as camadas (veja [Arquitetura](architecture.md)).
5. Atualize a documentação afetada no mesmo PR.
6. Rode o fluxo de [validação](running-tests.md).
7. Abra o PR com o modelo abaixo. Ele precisa ser aprovado por outra pessoa.

Não contorne hooks ou checks (`--no-verify` ou equivalente).

## Padrões

- Dependências só via Poetry (`poetry add`, `poetry add --group dev ...`); nunca `pip install`.
- Type hints em todas as funções; docstrings no estilo Google nas públicas.
- `get_logger(__name__)` em vez de `print`; nada de segredos em código ou logs.
- Imports absolutos (`from projetof1...`).
- `domain` não importa `ingestion`, `httpx` nem `streamlit`; `processing` não faz I/O.

## Modelo de descrição do PR

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
