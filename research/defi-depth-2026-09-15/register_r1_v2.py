"""Assemble exact source-repair certificate; no source/financial execution."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from tradingagents.research_defi_repair import runtime_hashes
from tradingagents.research_defi_repair.amendment import canonical,MUTABLE
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
base='research/defi-depth-2026-09-15/'
s=importlib.util.spec_from_file_location('register_r1_source',HERE/'r1_source_v2.py');r1=importlib.util.module_from_spec(s);s.loader.exec_module(r1)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def digest(path):return sha((ROOT/path).read_bytes())
def reference(path):return {'path':path,'sha256':digest(path) if (ROOT/path).exists() else '0'*64}
def write(path,obj):(ROOT/path).write_text(json.dumps(obj,indent=2)+'\n')
gate=json.loads((HERE/'gates-q2.json').read_text());parent=gate['experiments']['defi-depth-q2-20260915']
exp=copy.deepcopy(parent);exp['parent']='defi-depth-q2-20260915';exp['question']='Can the exact failed Q2 source panel be collected with valid at-most10-member batches without changing any field/date/clock or financial assumption?'
exp['charter']=reference(base+'r1-charter-v2.md');exp['runtime_hashes']=runtime_hashes()
exp['source_files'].pop(base+'q2_source.py');exp['source_files'][base+'r1_source_v2.py']=digest(base+'r1_source_v2.py')
exp['outputs']=r1.outputs_for(json.loads((HERE/'q2-spec.json').read_text()))
manifest={'schema_version':1,'baseline_experiment':'defi-depth-q2-20260915',
'economic_source_files':{p:h for p,h in parent['source_files'].items() if p!=base+'q2_source.py'},
'baseline_harness_source_files':{base+'q2_source.py':parent['source_files'][base+'q2_source.py']},
 'target_harness_source_files':{base+'r1_source_v2.py':exp['source_files'][base+'r1_source_v2.py']},
'experiment_invariants':{k:v for k,v in parent.items() if k not in MUTABLE}}
write(base+'r1-preservation-manifest-v2.json',manifest)
contract_sha=sha(canonical(exp));manifest_sha=digest(base+'r1-preservation-manifest-v2.json')
if (HERE/'reviews/r1-synthetic-preflight-v2.json').exists():
    write(base+'reviews/r1-repair-preflight-v2.json',{'status':'pass','target_experiment':r1.EXPERIMENT,
    'economic_manifest_sha256':manifest_sha,'reports':[reference(base+'reviews/r1-synthetic-preflight-v2.json')]})
claims={}
for name,terminal in [('defi-depth-q1-20260915','complete.json'),('defi-depth-q2-20260915','failed.json')]:
    p='research_runs/'+name+'/'
    claims[name]={'claim_sha256':digest(p+'claim.json'),'terminal':terminal,'terminal_sha256':digest(p+terminal)}
family=gate['families']['protocol-state-source']
cert={'schema_version':1,'amendment_id':'defi-depth-source-batch-repair-20260915','program_id':gate['program_id'],
'family_id':'protocol-state-source','mechanism_id':family['mechanism_id'],'family_sha256':sha(canonical(family)),
'increment':1,'target_experiment':r1.EXPERIMENT,'parent_experiment':exp['parent'],'target_contract_sha256':contract_sha,
'prior_claims':claims,'review':reference(base+'reviews/r1-amendment-approval-v2.json'),
'repair_preflight':reference(base+'reviews/r1-repair-preflight-v2.json'),
'economic_manifest':reference(base+'r1-preservation-manifest-v2.json')}
write(base+'r1-budget-amendment-v2.json',cert)
exp['budget_amendment']=reference(base+'r1-budget-amendment-v2.json')
gate['experiments'][r1.EXPERIMENT]=exp
write(base+'gates-r1-v2.json',gate)
print({'target_contract_sha256':contract_sha,'economic_manifest_sha256':manifest_sha,'approval_pending':cert['review']['sha256']=='0'*64,'preflight_pending':cert['repair_preflight']['sha256']=='0'*64})
