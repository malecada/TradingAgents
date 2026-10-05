from pathlib import Path
import hashlib, importlib.util, json, tempfile
from unittest.mock import patch
D=Path(__file__).resolve().parent
A=D.parent/'real-data-pilot-incremental-graph-retention01-2026-10-05'
B=D.parent/'real-data-pilot-incremental-graph-retention02-2026-10-05'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(B/'MANIFEST01.json')=='bc083a9347f69227f124aaed526bd11c1a3dbcb08cfcf893b6b0140b0f62fbfc'
m=json.loads((B/'MANIFEST01.json').read_text())
for n,r in m['files'].items():assert sha(B/n)==r['sha256'] and (B/n).stat().st_size==r['bytes']
old=(A/'select01.py').read_text();new=(B/'select01.py').read_text()
changes=[('def active_reference(root,rows,inputs):','def active_reference(root,rows,inputs,producer):'),('require(not any(p==q or p.is_relative_to(q) or p.parent==q.parent for p in rows)', 'require(not q.is_relative_to(producer) and not any(p==q or p.is_relative_to(q) or p.parent==q.parent for p in rows)'),("active_reference(root,[p.resolve()],a['experiment']['inputs'])", "active_reference(root,[p.resolve()],a['experiment']['inputs'],(root/base).resolve())")]
expected=old
for a,b in changes:
 assert expected.count(a)==1;expected=expected.replace(a,b)
assert expected==new

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
f=load('fixture02',A/'test_select01.py');v=load('selector02',B/'select01.py')
refusals=[]
with tempfile.TemporaryDirectory(dir=D) as t,patch.object(v.subprocess,'check_output',return_value=b''):
 root=Path(t);put,run,base=f.fixture(root)
 assert v.select(root,f.ID)['status']=='DRAFT'
 for ref in (base+'result.json',base+'graph-2022-05-02/manifest.json',base+'source-coverage.json',base.rstrip('/'),str(Path(base).parent),base+'aggregation'):
  put('research_runs/active-consumer/claim.json',{'experiment':{'inputs':{'input':{'path':ref}}}})
  try:v.select(root,f.ID)
  except ValueError as e:
   assert str(e)=='active consumer references ledger/producer directory';refusals.append(ref)
  else:raise AssertionError('active producer input accepted: '+ref)
 put('research_runs/active-consumer/claim.json',{'experiment':{'inputs':{'input':{'path':str(Path(base).with_name('unrelated-producer'))+'/result.json'}}}})
 assert v.select(root,f.ID)['status']=='DRAFT'
record={'schema_version':1,'decision':'accepted-corrected-draft-selector-source-only','source_sha256':sha(B/'select01.py'),'manifest_sha256':sha(B/'MANIFEST01.json'),'members_authenticated':len(m['files']),'exact_three_edit_inverse':True,'active_producer_inputs_refused':refusals,'unrelated_producer_allowed':True,'prior_actual_unproduced_refusal_reused':sha(D/'CHECK01.json'),'array_ledger_body_reads':0,'native_network_actions':False,'launch_or_retirement_authority':False}
(D/'CHECK02.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(json.dumps(record,sort_keys=True))
