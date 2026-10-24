import pytest

from backend.application.mappers.model_mapper import ModelMapper
from backend.domain.entities.causal_system import CausalSystem
from backend.domain.services.expression_evaluator import ExpressionEvaluator
from backend.domain.services.initial_state_calculator import InitialStateCalculator
from backend.domain.services.model_migrator import ModelMigrator
from backend.domain.services.simulation_engine import SimulationEngine
from backend.infrastructure.persistence.json_default_model_provider import JsonDefaultModelProvider


@pytest.fixture
def mapper() -> ModelMapper:
    return ModelMapper()


@pytest.fixture
def evaluator() -> ExpressionEvaluator:
    return ExpressionEvaluator()


@pytest.fixture
def engine(evaluator) -> SimulationEngine:
    return SimulationEngine(evaluator, InitialStateCalculator(evaluator))


@pytest.fixture
def migrator(engine) -> ModelMigrator:
    return ModelMigrator(engine)


@pytest.fixture
def default_system(mapper) -> CausalSystem:
    return JsonDefaultModelProvider(mapper).provide()


@pytest.fixture
def migrated_system(default_system, migrator) -> CausalSystem:
    return migrator.migrate(default_system)
