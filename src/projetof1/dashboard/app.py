"""Ponto de entrada do dashboard (composition root).

Executar com: `poetry run streamlit run src/projetof1/dashboard/app.py`
"""

from collections.abc import Callable
from datetime import UTC, datetime

import streamlit as st

from projetof1.dashboard import charts, components
from projetof1.domain.models import Meeting, Session, SessionOverview
from projetof1.domain.repositories import DataSourceError
from projetof1.domain.services import F1DashboardService
from projetof1.ingestion.http_client import HttpClient
from projetof1.ingestion.openf1_repositories import build_repositories
from projetof1.utils.config import ConfigError, Settings, load_settings
from projetof1.utils.logger import configure_logging, get_logger

logger = get_logger(__name__)

FIRST_SEASON = 2023
DEFAULT_PACE_DRIVERS = 3
VIEW_PER_DRIVER = "Melhor volta de cada piloto"
VIEW_OVERALL = "Voltas mais rápidas da sessão (geral)"
TOP_N_OPTIONS = [5, 10, 15, 20]
DEFAULT_TOP_N_PER_DRIVER = 10
DEFAULT_TOP_N_OVERALL = 5
API_ERROR_MESSAGE = (
    "Não foi possível consultar a OpenF1 agora. Tente novamente em instantes."
)


@st.cache_resource
def get_settings() -> Settings:
    """Carrega a configuração e o logging uma única vez por processo."""
    settings = load_settings()
    configure_logging(settings.log_level)
    return settings


@st.cache_resource
def get_service(settings: Settings) -> F1DashboardService:
    """Monta o serviço com os repositórios OpenF1 (injeção de dependência)."""
    client = HttpClient(settings.base_url, settings.timeout)
    return F1DashboardService(build_repositories(client))


def _load_meetings(year: int) -> list[Meeting]:
    return get_service(get_settings()).list_meetings(year)


def _load_sessions(meeting_key: int) -> list[Session]:
    return get_service(get_settings()).list_sessions(meeting_key)


def _load_overview(session_key: int, _session: Session) -> SessionOverview:
    # `session_key` é a chave do cache; `_session` (prefixo _) não é hasheado.
    return get_service(get_settings()).get_session_overview(_session)


def render_sidebar(
    load_meetings: Callable[[int], list[Meeting]],
    load_sessions: Callable[[int], list[Session]],
) -> tuple[Meeting, Session] | None:
    """Seletores de temporada, GP e sessão.

    Cada seletor dependente tem `key` ligada ao item pai (GP por temporada,
    sessão por GP). Sem isso, o Streamlit reaproveita a escolha anterior quando
    o rótulo se repete (ex.: "Race"), e o GP novo exibiria a sessão do antigo.
    """
    st.sidebar.title("🏎️ F1 Dashboard")
    now = datetime.now(tz=UTC)
    seasons = list(range(now.year, FIRST_SEASON - 1, -1))
    year = st.sidebar.selectbox("Temporada", seasons)

    meetings = {meeting.meeting_key: meeting for meeting in load_meetings(year)}
    if not meetings:
        st.sidebar.info("Nenhum GP disponível para esta temporada.")
        return None
    meeting_key = st.sidebar.selectbox(
        "Grande Prêmio",
        list(meetings),
        index=components.default_meeting_index(list(meetings.values()), now),
        format_func=lambda key: meetings[key].meeting_name,
        key=f"meeting-{year}",
    )
    meeting = meetings[meeting_key]

    sessions = {s.session_key: s for s in load_sessions(meeting.meeting_key)}
    if not sessions:
        st.sidebar.info("Nenhuma sessão disponível para este GP.")
        return None
    session_key = st.sidebar.selectbox(
        "Sessão",
        list(sessions),
        index=components.default_session_index(list(sessions.values()), now),
        format_func=lambda key: sessions[key].session_name,
        key=f"session-{meeting.meeting_key}",
    )
    st.sidebar.caption("Dados históricos de 2023 em diante, via OpenF1.")
    return meeting, sessions[session_key]


def render_result_tab(overview: SessionOverview) -> None:
    """Pódio e classificação."""
    if not overview.classification:
        st.info("Resultado indisponível para esta sessão.")
        return
    components.render_podium(overview.classification)
    st.dataframe(
        components.classification_rows(overview.classification),
        hide_index=True,
    )


def render_fastest_tab(overview: SessionOverview) -> None:
    """Ranking de voltas mais rápidas, em duas visões comparáveis."""
    if not overview.fastest_laps:
        st.info("Sem voltas cronometradas para esta sessão.")
        return

    view = st.radio(
        "Visão",
        [VIEW_PER_DRIVER, VIEW_OVERALL],
        horizontal=True,
        key="fastest-view",
        help=(
            "Por piloto: um piloto por linha, como na transmissão oficial. "
            "Geral: as voltas mais rápidas da sessão; o mesmo piloto pode se repetir."
        ),
    )
    per_driver = view == VIEW_PER_DRIVER
    quantity = st.select_slider(
        "Quantidade",
        options=TOP_N_OPTIONS,
        value=DEFAULT_TOP_N_PER_DRIVER if per_driver else DEFAULT_TOP_N_OVERALL,
        key=f"fastest-quantity-{view}",
    )
    ranking = overview.fastest_laps if per_driver else overview.fastest_laps_overall
    entries = ranking[:quantity]
    title = (
        f"Top {quantity} · melhor volta de cada piloto"
        if per_driver
        else f"Top {quantity} · voltas mais rápidas da sessão"
    )

    st.plotly_chart(
        charts.fastest_laps_bar(entries, title=title, show_lap_in_label=not per_driver),
        theme=None,
    )
    st.dataframe(
        components.fastest_lap_rows(entries, overview.best_sectors),
        hide_index=True,
    )
    st.caption(
        f"{components.FASTEST_SECTOR_MARK} setor mais rápido entre as voltas exibidas."
    )


def render_pace_tab(overview: SessionOverview) -> None:
    """Comparação de ritmo entre pilotos escolhidos."""
    if not overview.pace:
        st.info("Sem voltas cronometradas para esta sessão.")
        return
    by_acronym = {series.driver.name_acronym: series for series in overview.pace}
    options = list(by_acronym)
    selected = st.multiselect(
        "Pilotos",
        options,
        default=options[:DEFAULT_PACE_DRIVERS],
        max_selections=8,
        key=f"pace-{overview.session.session_key}",  # pilotos mudam por sessão
    )
    st.plotly_chart(
        charts.pace_lines([by_acronym[acronym] for acronym in selected]), theme=None
    )
    st.caption(
        "Voltas de saída do pit e acima de 107% da mediana do piloto são omitidas."
    )


def render_strategy_tab(overview: SessionOverview) -> None:
    """Estratégia de pneus e pit stops."""
    st.plotly_chart(charts.stint_timeline(overview.stints), theme=None)
    if not overview.session.is_race:
        st.caption("Pit stops são exibidos apenas em corridas e sprints.")
        return
    if overview.pit_stops:
        st.subheader("Pit stops")
        st.dataframe(components.pit_rows(overview.pit_stops), hide_index=True)
    else:
        st.info("Sem pit stops registrados.")


def main() -> None:
    """Desenha o dashboard."""
    st.set_page_config(page_title="F1 Dashboard", page_icon="🏁", layout="wide")
    components.inject_css()

    try:
        settings = get_settings()
    except ConfigError as exc:
        st.error(f"Configuração inválida: {exc}")
        return

    ttl = settings.cache_ttl_seconds
    load_meetings = st.cache_data(ttl=ttl, show_spinner="Carregando GPs...")(
        _load_meetings
    )
    load_sessions = st.cache_data(ttl=ttl, show_spinner="Carregando sessões...")(
        _load_sessions
    )
    load_overview = st.cache_data(
        ttl=ttl, show_spinner="Carregando dados da sessão..."
    )(_load_overview)

    try:
        selection = render_sidebar(load_meetings, load_sessions)
        if selection is None:
            return
        meeting, session = selection
        components.render_header(meeting, session)
        if session.date_start > datetime.now(tz=UTC):
            st.info("Esta sessão ainda não aconteceu. Escolha uma sessão anterior.")
            return
        overview = load_overview(session.session_key, session)
    except DataSourceError:
        logger.exception("falha ao consultar a OpenF1")
        st.error(API_ERROR_MESSAGE)
        return

    components.render_weather(overview.weather)

    result, fastest, pace, strategy = st.tabs(
        ["🏆 Resultado", "⏱️ Voltas mais rápidas", "📈 Ritmo", "🛞 Estratégia"]
    )
    with result:
        render_result_tab(overview)
    with fastest:
        render_fastest_tab(overview)
    with pace:
        render_pace_tab(overview)
    with strategy:
        render_strategy_tab(overview)

    components.render_footer()


if __name__ == "__main__":
    main()
