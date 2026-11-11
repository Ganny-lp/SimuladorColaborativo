import pytest
from backend.application.mappers.model_mapper import ModelMapper
from backend.infrastructure.persistence.json_default_model_provider import JsonDefaultModelProvider
from backend.domain.services.expression_evaluator import ExpressionEvaluator
from backend.domain.services.initial_state_calculator import InitialStateCalculator
from backend.domain.services.simulation_engine import SimulationEngine
from backend.domain.services.model_migrator import ModelMigrator

@pytest.fixture
def mapper(): return ModelMapper()
@pytest.fixture
def evaluator(): return ExpressionEvaluator()
@pytest.fixture
def engine(evaluator): return SimulationEngine(evaluator, InitialStateCalculator(evaluator))
@pytest.fixture
def default_system(mapper): return JsonDefaultModelProvider(mapper).provide()
@pytest.fixture
def migrator(engine,default_system): return ModelMigrator(engine,default_system)
@pytest.fixture
def migrated_system(migrator,default_system): return migrator.migrate(default_system)
