from pathlib import Path
import json,hashlib,ast
D=Path(__file__).parent;ROOT=D.resolve().parents[3];records=json.loads((D/'DELTA_INVERSE01.json').read_text())
for name,pairs in [('evaluation.py',[('continuation=None,completed_fit=None):','continuation=None,completed_fit=None,treatment_reference=None):'),('    registered_id=lifecycle_cell_id(cell[\'id\'])',"    from .treatment_admission import preflight_treatment\n    preflight_treatment(run, {} if treatment_reference is None else treatment_reference, cell, examples)\n    registered_id=lifecycle_cell_id(cell['id'])")]),('run.py',[("feature_binding_output=feature_reference.get('output'), **recovery_args)","feature_binding_output=feature_reference.get('output'), treatment_reference=reference, **recovery_args)")])]:
 p=D/'overlay/tradingagents/research/onchain_replication'/name
 if not p.exists():
  raw=(ROOT/'tradingagents/research/onchain_replication'/name).read_bytes();(D/'origins'/name).write_bytes(raw);p.write_bytes(raw)
 s=p.read_text()
 for old,new in pairs:assert s.count(old)==1;s=s.replace(old,new)
 p.write_text(s);ast.parse(s)
 row=next((r for r in records if r['path'].endswith('/'+name)),None)
 if row is None:
  row={'path':'tradingagents/research/onchain_replication/'+name,'original_sha256':hashlib.sha256((D/'origins'/name).read_bytes()).hexdigest(),'edits':[]};records.append(row)
 row['edits'].extend({'old':old,'new':new} for old,new in pairs);row['candidate_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
 inv=s
 for e in reversed(row['edits']):assert inv.count(e['new'])==1;inv=inv.replace(e['new'],e['old'])
 assert inv.encode()==(D/'origins'/name).read_bytes();row['exact_inverse']=True
(D/'DELTA_INVERSE01.json').write_text(json.dumps(records,indent=2)+'\n')
