import pytest

from backend.application.dto import PersistenceOutcome
from backend.application.mappers.model_mapper import ModelMapper
from backend.application.mappers.snapshot_assembler import SnapshotAssembler
from backend.application.services.model_publisher import ModelPublisher
from backend.application.use_cases._base import SimulationNotStartedError
from backend.application.use_cases.advance_cycle import AdvanceCycleUseCase
from backend.application.use_cases.change_input import ChangeInputUseCase
from backend.application.use_cases.get_simulation_snapshot import GetSimulationSnapshotUseCase
from backend.application.use_cases.restart_simulation import RestartSimulationUseCase
from backend.application.use_cases.start_simulation import StartSimulationUseCase
from backend.domain.services.initial_state_calculator import InitialStateCalculator
from tests.application.fakes import FakeDefaults, FakeRepository, InMemorySimulationStore


@pytest.fixture
def store():
    return InMemorySimulationStore()


@pytest.fixture
def repository():
    return FakeRepository()


@pytest.fixture
def start(store, repository, mapper, migrator, default_system):
    defaults = FakeDefaults(lambda: default_system.clone())
    return StartSimulationUseCase(store, repository, defaults, migrator)


@pytest.fixture
def started(start, store):
    start.execute()
    return store


def test_use_cases_fail_clearly_before_start(store, engine):
    with pytest.raises(SimulationNotStartedError):
        AdvanceCycleUseCase(store, engine).execute()


class TestStartSimulation:
    def test_falls_back_to_default_model(self, start, store):
        start.execute()
        assert store.simulation is not None and store.simulation.cycle == 0

    def test_uses_remote_model_and_resets_its_state(self, store, mapper, migrator, default_system):
        remote = default_system.clone()
        remote.set_value("Rentabilidade", 999_999)  # estado "sujo" vindo da nuvem
        remote.set_value("Pt", 111)
        start = StartSimulationUseCase(
            store, FakeRepository(remote=remote), FakeDefaults(lambda: default_system), migrator
        )
        start.execute()
        system = store.simulation.system
        assert system.value_of("Pt") == 111          # modelo/inputs vêm da nuvem
        assert system.value_of("Rentabilidade") == 0  # estado NÃO

    def test_is_idempotent_unless_forced(self, start, store):
        start.execute()
        first = store.simulation
        start.execute()
        assert store.simulation is first
        start.execute(force_reload=True)
        assert store.simulation is not first


class TestAdvanceAndRestart:
    def test_advance_records_history(self, started, engine):
        AdvanceCycleUseCase(started, engine).execute()
        AdvanceCycleUseCase(started, engine).execute()
        simulation = started.simulation
        assert simulation.cycle == 2
        assert [r.cycle for r in simulation.history] == [1, 2]
        assert simulation.history[0].profit == pytest.approx(214.41088829550878 - 26474.735921904525)

    def test_restart_clears_progress_but_keeps_inputs(self, started, engine, repository):
        publisher = ModelPublisher(repository, InitialStateCalculator(engine._evaluator))
        ChangeInputUseCase(started, publisher).execute("budget_promo", 12345)
        AdvanceCycleUseCase(started, engine).execute()
        RestartSimulationUseCase(started, engine).execute()
        simulation = started.simulation
        assert simulation.cycle == 0 and simulation.history == []
        assert simulation.system.value_of("Rentabilidade") == 0
        assert simulation.system.value_of("budget_promo") == 12345


class TestChangeInput:
    def _use_case(self, store, repository, engine):
        publisher = ModelPublisher(repository, InitialStateCalculator(engine._evaluator))
        return ChangeInputUseCase(store, publisher)

    def test_unchanged_value_is_a_noop(self, started, repository, engine):
        result = self._use_case(started, repository, engine).execute("Pt", 150.0)
        assert not result.changed and repository.saved == []

    def test_publishes_model_with_initial_state(self, started, repository, engine):
        AdvanceCycleUseCase(started, engine).execute()   # estado sujo localmente
        result = self._use_case(started, repository, engine).execute("Pt", 120.0)
        assert result.changed and result.persistence is PersistenceOutcome.SAVED
        published = repository.saved[-1]
        assert published.value_of("Pt") == 120.0
        assert published.value_of("Rentabilidade") == 0          # cloud nunca acumula ciclos
        assert started.simulation.system.value_of("Rentabilidade") != 0  # sessão local intacta

    def test_reports_failure_and_skip(self, started, engine):
        failing = self._use_case(started, FakeRepository(fail_on_save=True), engine)
        assert failing.execute("Pt", 100.0).persistence is PersistenceOutcome.FAILED
        offline = self._use_case(started, FakeRepository(persistent=False), engine)
        assert offline.execute("Pt", 90.0).persistence is PersistenceOutcome.SKIPPED

    def test_unknown_variable(self, started, repository, engine):
        from backend.domain.exceptions import NodeNotFoundError
        with pytest.raises(NodeNotFoundError):
            self._use_case(started, repository, engine).execute("Nope", 1)


class TestSnapshot:
    def test_snapshot_exposes_dtos_only(self, started, repository, mapper, engine):
        AdvanceCycleUseCase(started, engine).execute()
        snapshot = GetSimulationSnapshotUseCase(started, repository, SnapshotAssembler(mapper)).execute()
        assert snapshot.cycle == 1 and snapshot.cloud_enabled is True
        assert snapshot.kpis.served_quantity == pytest.approx(1.6816540258471278)
        assert snapshot.variable("Pt").value == 150.0
        assert snapshot.variable("inexistente") is None
        assert len(snapshot.variables) == 30
        assert len(snapshot.history) == 1
        assert set(snapshot.model_payload) >= {"nodes", "links", "price_scale"}

    def test_snapshot_is_immutable(self, started, repository, mapper):
        snapshot = GetSimulationSnapshotUseCase(started, repository, SnapshotAssembler(mapper)).execute()
        with pytest.raises(Exception):
            snapshot.cycle = 99
