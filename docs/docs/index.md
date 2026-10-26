# projetoF1

Dashboard interativo em **Streamlit** com dados históricos da Fórmula 1, de 2023 em
diante, consumidos da [OpenF1 API](https://openf1.org/). Os dados históricos são
gratuitos e não exigem autenticação.

!!! note "Projeto não oficial"
    Este projeto não tem vínculo com a Formula 1. Os dados vêm da OpenF1, também
    não oficial.

## O que o dashboard mostra

Na barra lateral, escolha **temporada → Grande Prêmio → sessão**. Por padrão, o
dashboard abre na corrida mais recente que já aconteceu.

| Área | Conteúdo |
| --- | --- |
| Cabeçalho | GP, circuito, sessão, data e clima (ar, pista, umidade, chuva) |
| 🏆 Resultado | Pódio em cards com foto e cor da equipe, e a classificação completa com DNF/DNS/DSQ |
| ⏱️ Voltas mais rápidas | Ranking em barras na cor de cada equipe e tabela com setores (🟣 = setor mais rápido) e volta ideal, em duas visões (abaixo) |
| 📈 Ritmo | Tempo volta a volta dos pilotos escolhidos, sem voltas de saída do pit e outliers |
| 🛞 Estratégia | Linha do tempo de pneus por composto e tabela de pit stops (corridas e sprints) |

## Duas visões de voltas mais rápidas

| Visão | Critério | Padrão |
| --- | --- | --- |
| Melhor volta de cada piloto | Um piloto por linha, como na transmissão oficial | Top 10 |
| Voltas mais rápidas da sessão (geral) | As voltas mais rápidas de qualquer piloto; o mesmo piloto pode se repetir | Top 5 |

A quantidade pode ir de 5 a 20. Exemplo no GP do Bahrein 2024 (corrida): na visão
geral, Verstappen aparece três vezes no top 5 (voltas 39, 43 e 46); na visão por
piloto, aparece uma vez, e Alonso, Pérez e Norris completam o top 5.

## Links rápidos

- [Como rodar localmente](running-locally.md)
- [Arquitetura](architecture.md)
- [Estrutura do projeto](project-structure.md)
- [Como rodar os testes](running-tests.md)
- [Como contribuir](contributing.md)
