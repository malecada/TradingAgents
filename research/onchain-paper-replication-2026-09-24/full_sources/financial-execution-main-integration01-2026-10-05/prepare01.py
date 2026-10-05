"""Prepare copied fitting source; never import numerical code or edit live sources."""
import ast,difflib,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
ROOT=H.parents[3];REL=Path('tradingagents/research/onchain_replication')
MAIN=ROOT/REL
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')/REL
NAMES=['financial_execution.py','model_registry.py','checkpoints.py','training.py','replay.py','run.py']
def replace(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def node(s,n):return next(x for x in ast.parse(s).body if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and x.name==n)
def segment(s,n):return ast.get_source_segment(s,node(s,n))
def write(p,b):
 with p.open('xb') as f:f.write(b if isinstance(b,bytes) else b.encode())
origins={};candidates={}
for n in NAMES:
 cap=(CAP/n).read_bytes();write(H/'origins/CAP'/n,cap)
 if (MAIN/n).exists():
  raw=(MAIN/n).read_bytes();write(H/'origins/Main'/n,raw)
  origins[n]=raw.decode()
 else:origins[n]=''
 if n in ('financial_execution.py','model_registry.py','checkpoints.py','replay.py'):candidates[n]=cap.decode()
 elif n=='training.py':
  s=cap.decode();s=replace(s,segment(s,'_reserve'),segment(origins[n],'_reserve'));candidates[n]=s
 elif n=='run.py':
  s=origins[n]
  s=replace(s,'from .metrics import classification_metrics','from . import financial_execution as financial\nfrom .metrics import classification_metrics')
  s=replace(s,"    if set(plan) != {'schema_version', 'cells', 'populations', 'representations', 'model', 'training', 'ledger_output', 'controls_output'} or plan['schema_version'] != 1:\n        raise ValueError('batch plan schema differs')","    selections=financial.plan_selection(plan)\n    for execution in selections.values():financial.for_run(run,execution)")
  s=replace(s,"            row['attempts'].append(run.admission.experiment_id)","            execution=financial.plan_selection(plan).get(cell['arm'])\n            execution=financial.for_run(run,execution)\n            if execution is not None:provenance.update(model_execution=execution)\n            row['attempts'].append(run.admission.experiment_id)")
  s=replace(s,"expected_test_mask=reference['binding']['test_mask_hash'], feature_binding=binding,","expected_test_mask=reference['binding']['test_mask_hash'], feature_binding=binding, execution=execution,")
  candidates[n]=s
for n,s in candidates.items():ast.parse(s);write(H/'candidate'/n,s)
print(json.dumps({'prepared':list(candidates),'execution_entry_evaluation_still_requires_narrow_candidate':True},sort_keys=True))
