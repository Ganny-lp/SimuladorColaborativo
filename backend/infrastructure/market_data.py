"""Official monthly IPCA, without substituting assumptions on request failure."""
from datetime import datetime, timezone
import math
import requests

IPCA_URL="https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados/ultimos/1?formato=json"

def fetch_ipca():
    response=requests.get(IPCA_URL,timeout=8)
    response.raise_for_status()
    rows=response.json()
    if not isinstance(rows,list) or len(rows)!=1:
        raise ValueError("Resposta IPCA inválida")
    row=rows[0]
    reference=datetime.strptime(row["data"],"%d/%m/%Y").date()
    value=float(str(row["valor"]).replace(",","."))/100
    if not math.isfinite(value) or not -0.99 <= value <= 1:
        raise ValueError("IPCA fora do intervalo suportado")
    return {"value":value,"reference":reference.isoformat(),"source":IPCA_URL,"retrieved_at":datetime.now(timezone.utc).isoformat()}
