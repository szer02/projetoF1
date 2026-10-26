# OpenF1 API — Resumo

Fonte: https://openf1.org/docs/

## Visão geral
- **URL base:** `https://api.openf1.org/v1/`
- **Dados históricos (2023+):** gratuitos e sem autenticação.
- **Tempo real:** exige assinatura paga.
- Projeto não oficial (sem vínculo com a Formula 1).

## Formato de resposta
- JSON por padrão.
- CSV: adicione `csv=true` → `https://api.openf1.org/v1/sessions?year=2023&csv=true`

## Filtros
- Feitos via query string, em qualquer atributo (exceto arrays).
- Operadores: `=`, `>`, `>=`, `<`, `<=` (ex.: `speed>=315`).
- `meeting_key=latest` / `session_key=latest` → evento/sessão atual ou mais recente.
- Datas: `date>=2023-01-01&date<2023-09-01` (formatos aceitos pelo `dateutil.parser`).
- Parâmetros repetidos funcionam como "OU" (ex.: `driver_number=4&driver_number=81`).

## Conceitos-chave
| Chave | Significado |
|---|---|
| `meeting_key` | Fim de semana de GP ou teste (agrupa sessões) |
| `session_key` | Sessão: treino, quali, sprint, corrida |
| `driver_number` | Número do piloto |

## Endpoints
| Endpoint | Descrição | Campos principais |
|---|---|---|
| `/car_data` | Telemetria (~3,7 Hz) | `speed`, `rpm`, `n_gear`, `throttle`, `brake`, `drs`, `date` |
| `/championship_drivers` (beta) | Classificação de pilotos (só corridas) | `points_current`, `points_start`, `position_current`, `position_start` |
| `/championship_teams` (beta) | Classificação de construtores (só corridas) | `team_name`, `points_current`, `position_current` |
| `/drivers` | Pilotos da sessão | `full_name`, `name_acronym`, `team_name`, `team_colour`, `headshot_url` |
| `/intervals` | Gaps entre pilotos (só corridas, ~4 s) | `gap_to_leader`, `interval`, `date` |
| `/laps` | Dados por volta | `lap_number`, `lap_duration`, `duration_sector_1..3`, `i1_speed`, `i2_speed`, `st_speed`, `is_pit_out_lap` |
| `/location` | Posição 3D aproximada na pista (~3,7 Hz) | `x`, `y`, `z`, `date` |
| `/meetings` | Fins de semana de GP/testes | `meeting_name`, `year`, `country_name`, `circuit_short_name`, `date_start`, `date_end` |
| `/overtakes` | Trocas de posição (só corridas, pode estar incompleto) | `overtaking_driver_number`, `overtaken_driver_number`, `position` |
| `/pit` | Passagens pelo pit lane | `lap_number`, `lane_duration`, `stop_duration` |
| `/position` | Posição dos pilotos ao longo da sessão | `position`, `date` |
| `/race_control` | Bandeiras, safety car, incidentes | `category`, `flag`, `message`, `scope`, `sector`, `lap_number` |
| `/sessions` | Sessões de um meeting | `session_name`, `session_type`, `date_start`, `date_end`, `year` |
| `/session_result` | Resultado final da sessão | `position`, `duration`, `gap_to_leader`, `number_of_laps`, `dnf`, `dns`, `dsq` |
| `/starting_grid` | Grid de largada | `position`, `lap_duration` |
| `/stints` | Stints e pneus | `stint_number`, `compound`, `lap_start`, `lap_end`, `tyre_age_at_start` |
| `/team_radio` | Rádio piloto/equipe (seleção limitada) | `recording_url`, `date` |
| `/weather` | Clima na pista (a cada minuto) | `air_temperature`, `track_temperature`, `humidity`, `rainfall`, `wind_speed`, `wind_direction` |

> Quase todos os endpoints também retornam `meeting_key`, `session_key` e, quando aplicável, `driver_number`.

## Observações
- `intervals`, `overtakes` e `championship_*` existem só para corridas.
- Na quali, `session_result.duration` e `gap_to_leader` vêm como arrays [Q1, Q2, Q3].
- Campos obsoletos (removidos após 2026): `drivers.country_code`, `pit.pit_duration`.
- `stop_duration` existe a partir do GP dos EUA de 2024.
- `team_radio` quase não tem dados em 2026.
- `meetings` e `sessions` são atualizados diariamente, à meia-noite UTC.

## Exemplos rápidos
```
https://api.openf1.org/v1/sessions?year=2023&session_name=Race
https://api.openf1.org/v1/laps?session_key=9161&driver_number=63
https://api.openf1.org/v1/drivers?session_key=latest
https://api.openf1.org/v1/car_data?driver_number=55&session_key=9159&speed>=315
```
