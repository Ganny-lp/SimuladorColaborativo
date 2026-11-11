import copy
from datetime import date, datetime, timezone
from backend.application.use_cases._base import require_simulation
from backend.domain.services.input_validation import validate_input
from backend.domain.exceptions import InvalidModelError

ALLOWED={"Inflacao","Nc","Carga_Tributaria","Alfa","Beta_1","Preco_Equipamento_Novo","Inovacao_Fabricantes","Influencia_Avaliacoes_Online"}

class CalibrateInputUseCase:
    def __init__(self,store,publisher,engine):
        self._store,self._publisher,self._engine=store,publisher,engine
    def execute(self,name,value,source,reference,method):
        simulation=require_simulation(self._store)
        if simulation.cycle: raise InvalidModelError("Reinicie antes de calibrar o cenário.")
        if name not in ALLOWED: raise InvalidModelError("Parâmetro fora da calibração.")
        if not isinstance(source,str) or len(source.strip())<8 or len(source)>2000:
            raise InvalidModelError("Informe a fonte verificável (URL ou documento e recorte).")
        if method not in {"Observação local declarada","Estimativa empírica declarada","Série oficial consultada"}:
            raise InvalidModelError("Método inválido.")
        try: observed=date.fromisoformat(reference)
        except (ValueError,TypeError): raise InvalidModelError("Data de referência inválida.")
        if observed>date.today(): raise InvalidModelError("A referência não pode estar no futuro.")
        value=validate_input(simulation.system.node(name),value)
        candidate=copy.deepcopy(simulation)
        candidate.set_input(name,value)
        candidate.system.extras.setdefault("calibration",{})[name]={"value":value,"source":source.strip(),"reference":reference,"method":method,"registered_at":datetime.now(timezone.utc).isoformat()}
        self._engine.reset_state(candidate.system)
        self._engine.recompute_derived(candidate.system)
        candidate.baseline=candidate.system.values()
        self._store.put(candidate)
        return self._publisher.publish(candidate.system)
