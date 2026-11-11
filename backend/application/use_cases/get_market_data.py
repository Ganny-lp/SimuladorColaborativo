"""Read-only market query with injected source."""
class GetMarketDataUseCase:
    def __init__(self,provider): self._provider=provider
    def execute(self): return self._provider()
