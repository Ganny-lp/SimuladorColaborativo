from backend.application.ports.model_repository import ModelRepository
from backend.domain.entities.causal_system import CausalSystem


class NullModelRepository(ModelRepository):
    """Null Object: usado quando não há credenciais; a app funciona só com o modelo padrão."""

    @property
    def is_persistent(self) -> bool:
        return False

    def load(self) -> CausalSystem | None:
        return None

    def save(self, system: CausalSystem) -> None:
        return None
