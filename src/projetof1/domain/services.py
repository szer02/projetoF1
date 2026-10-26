from projetof1.domain.models import Meeting, Session, SessionOverview
from projetof1.domain.repositories import F1Repositories
from projetof1.processing.drivers import build_driver_index
from projetof1.processing.laps import (
    best_sectors,
    compute_top_n_laps,
    compute_top_n_laps_overall,
    lap_time_series,
)
from projetof1.processing.results import build_classification
from projetof1.processing.stints import build_stint_timeline, pit_summary
from projetof1.processing.weather import summarize_weather
from projetof1.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_TOP_N = 20
"""Teto dos rankings de voltas; a tela escolhe quantas exibir (5 a 20)."""


class F1DashboardService:
    """Casos de uso do dashboard, sem conhecer a origem dos dados.

    Busca nos repositórios injetados e delega os cálculos às funções puras de
    `processing`. Erros da fonte (`DataSourceError`) são propagados para que a
    camada de apresentação decida como exibi-los.
    """

    def __init__(self, repositories: F1Repositories) -> None:
        self._repos = repositories

    def list_meetings(self, year: int) -> list[Meeting]:
        """Meetings não cancelados de `year`, em ordem cronológica."""
        meetings = self._repos.meetings.fetch(year)
        return sorted(
            (meeting for meeting in meetings if not meeting.is_cancelled),
            key=lambda meeting: meeting.date_start,
        )

    def list_sessions(self, meeting_key: int) -> list[Session]:
        """Sessões não canceladas de `meeting_key`, em ordem cronológica."""
        sessions = self._repos.sessions.fetch(meeting_key)
        return sorted(
            (session for session in sessions if not session.is_cancelled),
            key=lambda session: session.date_start,
        )

    def get_session_overview(
        self, session: Session, top_n: int = DEFAULT_TOP_N
    ) -> SessionOverview:
        """Reúne os dados e as projeções exibidos na tela de uma sessão.

        Args:
            session: Sessão selecionada.
            top_n: Tamanho máximo dos dois rankings de voltas mais rápidas
                (melhor volta por piloto e voltas gerais da sessão).

        Returns:
            Visão consolidada da sessão; partes sem dados vêm vazias.

        Raises:
            DataSourceError: Se algum endpoint não puder ser consultado.
            ValueError: Se `top_n` for menor que 1.
        """
        if top_n < 1:
            msg = "top_n deve ser maior ou igual a 1"
            raise ValueError(msg)
        key = session.session_key
        logger.info("montando visão da sessão: session_key=%s", key)

        drivers = self._repos.drivers.fetch(key)
        laps = self._repos.laps.fetch(key)
        stints = self._repos.stints.fetch(key)
        pits = self._repos.pits.fetch(key)
        results = self._repos.results.fetch(key)
        weather = self._repos.weather.fetch(key)

        index = build_driver_index(drivers)
        classification = build_classification(results, index)
        order = [entry.driver.driver_number for entry in classification]
        order += [number for number in sorted(index) if number not in order]

        overview = SessionOverview(
            session=session,
            drivers=tuple(index[number] for number in order if number in index),
            classification=tuple(classification),
            fastest_laps=tuple(compute_top_n_laps(laps, index, top_n)),
            fastest_laps_overall=tuple(compute_top_n_laps_overall(laps, index, top_n)),
            pace=tuple(lap_time_series(laps, index, order)),
            best_sectors=tuple(best_sectors(laps)),
            stints=tuple(build_stint_timeline(stints, index, order)),
            pit_stops=tuple(pit_summary(pits, index)),
            weather=summarize_weather(weather),
        )
        logger.info(
            "visão montada: session_key=%s pilotos=%d voltas=%d stints=%d pits=%d resultado=%d",
            key,
            len(drivers),
            len(laps),
            len(stints),
            len(pits),
            len(results),
        )
        return overview
