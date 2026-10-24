from backend.application.ports.simulation_store import SimulationStore
from backend.domain.entities.simulation import Simulation


class SimulationNotStartedError(RuntimeError):
    """Um caso de uso foi chamado antes de StartSimulationUseCase."""


def require_simulation(store: SimulationStore) -> Simulation:
    simulation = store.get()
    if simulation is None:
        raise SimulationNotStartedError("Nenhuma simulação iniciada.")
    return simulation
