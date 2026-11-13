import csv
import io
from types import SimpleNamespace
from frontend.components.lab_experience import notebook_csv,evidence_count
from backend.application.dto import CycleRecordDTO,VariableDTO


def test_notebook_only_exports_completed_cycles_and_neutralizes_formulas():
    snapshot=SimpleNamespace(history=[CycleRecordDTO(1,12,5)])
    notes={'1':{'hypothesis':' =1+1','price':150},'2':{'hypothesis':'unfinished','price':200}}
    rows=list(csv.reader(io.StringIO(notebook_csv(snapshot,notes))))
    assert len(rows)==2
    assert rows[1][3]=="' =1+1"
    assert rows[1][4]=='150'


def test_evidence_coverage_requires_current_value():
    snapshot=SimpleNamespace(variables=[VariableDTO('Nc','Input',7,'',''),VariableDTO('Alfa','Input',.2,'','')],model_payload={'calibration':{'Nc':{'value':8},'Alfa':{'value':.2}}})
    assert evidence_count(snapshot)==1
