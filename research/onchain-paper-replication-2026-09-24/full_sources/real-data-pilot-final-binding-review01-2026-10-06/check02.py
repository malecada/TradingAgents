"""Four-source-pin gate delta only. Prior metadata check and all bodies retained."""
from pathlib import Path
import json,hashlib,copy
F=Path('research/onchain-paper-replication-2026-09-24/full_sources');H=F/'real-data-pilot-final-binding-review01-2026-10-06';D=F/'real-data-pilot-final01-2026-10-06';N='eth-paper-real-data-end-to-end-resource-20261005-01'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=read(D/'gate_PREDECESSOR03.json');new=read(D/'gate01.json');assert sha(D/'gate_PREDECESSOR03.json')=='85a60fd9659cae88afab9d143cfcd4b61319f359b54faab2c72645f28b71e544';assert sha(D/'gate01.json')=='629db998922868d386b4bdaabf118c9c7070519f3f921ca3aa3febab5ff2af07'
e=new['experiments'][N];sources=e['source_files'];oe=old['experiments'][N];added=set(sources)-set(oe['source_files']);extension=e['cumulative_budget_extension'];allocation=read(extension['extension']['path'])['allocation'];expected={v['path']:v['sha256'] for v in [*extension.values(),allocation]};expected[str(F/'real-data-pilot-resource-buffer-allocation01-2026-10-06/allocation01.py')]='3912e68c232553f1fab5e39a92c0741c2c0ddab49316321c1189781d19611dfd'
assert len(added)==4 and added==set(expected) and len(sources)==198
for p,h in expected.items():assert sources[p]==h==sha(p)
inverse=copy.deepcopy(new)
for p in added:del inverse['experiments'][N]['source_files'][p]
assert inverse==old
b=read(D/'BINDING_DRAFT04.json');ob=read(D/'BINDING_DRAFT03.json');bi=copy.deepcopy(b);bi['gate']=ob['gate'];assert bi==ob and b['gate']['sha256']==sha(D/'gate01.json')
ad=read(D/'ACTUAL_READONLY_ADMISSION02.json');assert ad=={'Owner_or_Binding_born':False,'ResearchRun_start':False,'decision':'passed','effective_attempt_budget':72,'input_roles':59,'kind':'compact_resource','ready':True,'source':'04d6e5b588f1d3202d68b7f4d472cb87c9b53a91','source_pins':198}
result={'schema_version':1,'decision':'passed','scope':'four source pins plus changed gate ref only; all public/private/graph/science/limits inverse unchanged','old_gate_sha256':sha(D/'gate_PREDECESSOR03.json'),'gate_sha256':sha(D/'gate01.json'),'new_source_pins':expected,'source_pins':198,'input_roles':59,'actual_root_admission':{'path':str(D/'ACTUAL_READONLY_ADMISSION02.json'),'sha256':sha(D/'ACTUAL_READONLY_ADMISSION02.json')},'actual_root_admission_ready':True,'actual_root_budget':72,'reviewer_reexecuted_admission':False,'no_private_payload_numerical_Git_network_native_reads_or_calls':True}
(H/'CHECKS02.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
