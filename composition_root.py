"""
Raiz de composição: único lugar que conhece TODAS as camadas e liga as implementações
concretas às portas (injeção de dependência manual).
"""
from __future__ import annotations

from typing import Any, MutableMapping

from backend.application.mappers.model_mapper import ModelMapper
from backend.application.mappers.snapshot_assembler import SnapshotAssembler
from backend.application.ports.model_repository import ModelRepository
from backend.application.services.model_publisher import ModelPublisher
from backend.application.use_cases.advance_cycle import AdvanceCycleUseCase
from backend.application.use_cases.change_input import ChangeInputUseCase
from backend.application.use_cases.get_simulation_snapshot import GetSimulationSnapshotUseCase
from backend.application.use_cases.restart_simulation import RestartSimulationUseCase
from backend.application.use_cases.start_simulation import StartSimulationUseCase
from backend.domain.services.expression_evaluator import ExpressionEvaluator
from backend.domain.services.initial_state_calculator import InitialStateCalculator
from backend.domain.services.model_migrator import ModelMigrator
from backend.domain.services.simulation_engine import SimulationEngine
from backend.infrastructure.config.settings import JsonBinSettings
from backend.infrastructure.persistence.json_default_model_provider import JsonDefaultModelProvider
from backend.infrastructure.persistence.jsonbin_model_repository import JsonBinModelRepository
from backend.infrastructure.persistence.null_model_repository import NullModelRepository
from frontend.components.cld_diagram import CldDiagram
from frontend.components.cycle_charts import CycleCharts
from frontend.components.kpi_cards import KpiCards
from frontend.components.page_header import PageHeader
from frontend.components.price_slider import PriceSlider
from frontend.components.theme import Theme
from frontend.components.variables_table import VariablesTable
from frontend.config import APP_VERSION, PRICE_RULER_KEY, PRICE_SYNC_KEY, CloudCredentials
from frontend.session.session_simulation_store import SessionStateSimulationStore
from frontend.session.ui_state import UiState
from frontend.views.diagram_tab import DiagramTab
from frontend.views.main_page import MainPage
from frontend.views.simulation_tab import SimulationTab
from frontend.views.variables_tab import VariablesTab


def build_main_page(secrets: Any, session_state: MutableMapping) -> MainPage:
    # ── backend: domínio ────────────────────────────────────────────────────
    evaluator = ExpressionEvaluator()
    initial_state = InitialStateCalculator(evaluator)
    engine = SimulationEngine(evaluator, initial_state)
    migrator = ModelMigrator(engine)

    # ── backend: infraestrutura ─────────────────────────────────────────────
    mapper = ModelMapper()
    settings = JsonBinSettings.from_secrets(secrets)
    repository: ModelRepository = (
        JsonBinModelRepository(settings, mapper) if settings.is_configured else NullModelRepository()
    )
    defaults = JsonDefaultModelProvider(mapper)

    # ── backend: aplicação ──────────────────────────────────────────────────
    store = SessionStateSimulationStore(session_state, APP_VERSION)
    publisher = ModelPublisher(repository, initial_state)
    start = StartSimulationUseCase(store, repository, defaults, migrator)
    snapshot = GetSimulationSnapshotUseCase(store, repository, SnapshotAssembler(mapper))
    change_input = ChangeInputUseCase(store, publisher)
    advance = AdvanceCycleUseCase(store, engine)
    restart = RestartSimulationUseCase(store, engine)

    # ── frontend ────────────────────────────────────────────────────────────
    credentials = CloudCredentials(settings.api_key, settings.bin_id)
    tabs = [
        DiagramTab(CldDiagram(credentials), start),
        SimulationTab(
            KpiCards(), PriceSlider(PRICE_SYNC_KEY, PRICE_RULER_KEY), CycleCharts(),
            change_input, advance, restart,
        ),
        VariablesTab(VariablesTable(), UiState(session_state)),
    ]
    return MainPage(Theme(), PageHeader(), tabs, start, snapshot)
