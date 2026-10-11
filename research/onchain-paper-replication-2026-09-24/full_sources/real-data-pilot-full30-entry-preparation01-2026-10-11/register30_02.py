"""Root-only fresh30 registration materialization; no admission, claim or launch.

Requires actual bound inputs and public Root evidence refs; leaves final binding
and release to independent review. Never reads the opaque transport body.
"""
import copy, hashlib, json
from pathlib import Path
ROOT=Path.cwd().resolve();HERE=Path(__file__).resolve().parent;F=HERE.parent
DRAFT=F/'real-data-pilot-full30-preparation01-2026-10-11'
T=F/'real-data-pilot-full30-binding-preparation01-2026-10-11'
OLD='eth-paper-real-data-end-to-end-resource-20261009-29'
NAME='eth-paper-real-data-end-to-end-resource-20261011-30'
REQUIRED=('budget_review','capacity_observation','prior_outcome_review','prior_preservation_complete','prior_recovery_review','prior_root_closure_review','integration_review')
def need(ok,message):
 if not ok:raise ValueError(message)
def load(p):return json.loads(p.read_bytes())
def ref(p):
 need(p.resolve(strict=True)==p and p.is_file() and p.stat().st_nlink==1 and p.stat().st_size<=4194304,'bounded canonical public file required')
 b=p.read_bytes();return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(p,x):
 with p.open('xb') as f:f.write((json.dumps(x,sort_keys=True,indent=2)+'\n').encode())
def main():
 need(not (ROOT/'research_runs'/NAME).exists(),'fresh claim identity spent')
 evidence=load(HERE/'ROOT_EVIDENCE_REFS01.json')
 need(set(evidence)==set(REQUIRED),'exact real Root evidence roster required')
 for role,pin in evidence.items():
  path=Path(pin['path']);need(not path.is_absolute() and '..' not in path.parts and str(path).startswith('research/onchain-paper-replication-2026-09-24/full_sources/'),'public evidence path required')
  actual=ref(ROOT/path);need(all(actual[k]==pin[k] for k in ('path','sha256')),'Root evidence changed: '+role)
 refs=load(T/'ALL_INPUT_REFS01.json');bound=load(T/'BOUND01.json')
 need(len(refs)==67 and set(bound['private_input'])=={'archive_transport'},'genuine full30 bound67 required')
 private=bound['private_input']['archive_transport']
 need(private['path']=='research_artifacts/real_pilot_runtime/pilot-transport-20261011-30-01/archive_transport01.json','fresh opaque publication route required')
 need(all(refs['archive_transport'][k]==private[k] for k in ('path','sha256')),'opaque public reference differs')
 for role,doc in bound['inputs'].items():
  p=ROOT/refs[role]['path'];need(ref(p)['sha256']==refs[role]['sha256'] and load(p)==doc,'actual bound public input differs')
 gate=load(DRAFT/'gate.draft01.json');experiment=gate['experiments'][NAME]
 need(experiment['parent']==OLD and len(experiment['inputs'])==67,'full30 parent/roster differs')
 experiment['cells']=['real-eth-seven-graph-joint-update-resource30']
 experiment['inputs']=refs;experiment['charter']=ref(DRAFT/'CHARTER01.md')
 experiment['cumulative_budget_extension']={'extension':ref(DRAFT/'EXTENSION_PROPOSED101_01.json'),'review':evidence['budget_review']}
 pins=experiment['source_files'];pins.update(load(HERE/'INSTALLED_SOURCE_PINS01.json'))
 for name in ('preflight30_02.py','root_io30_02.py','register30_02.py','CORE_MANIFEST01.json','INSTALLED_SOURCE_PINS01.json','CAPACITY_SOURCE_MAP01.json'):
  p=HERE/name;pins[str(p.relative_to(ROOT))]=ref(p)['sha256']
 public_pins=load(HERE/'CAPACITY_SOURCE_MAP01.json')['source_files']
 need(all(pins.get(path)==digest for path,digest in public_pins.items()),'capacity ancestry map differs from admission sources')
 for pin in evidence.values():pins[pin['path']]=pin['sha256']
 for name in ('MANIFEST01.json','bind_actual01.py','PREPARED01.json','REQUEST01.json','BOUND01.json','ALL_INPUT_REFS01.json','BINDING_CHECK01.json','PUBLIC_INPUT_REFS_DRAFT01.json'):
  p=T/name;pins[str(p.relative_to(ROOT))]=ref(p)['sha256']
 for path,digest in pins.items():
  need(not path.startswith('research_artifacts/real_pilot_runtime/'),'private body cannot be source')
  need(ref(ROOT/path)['sha256']==digest,'current source differs: '+path)
 public={'experiment':NAME,'all_input_roles':67,'source_pins':public_pins,'status':'DRAFT_NOT_RELEASED'}
 capacity=load(ROOT/evidence['capacity_observation']['path'])
 need(capacity['identity']==NAME and capacity['source_body_pins']==public['source_pins'],'Root capacity must join exact prospective source roster')
 save(HERE/'PUBLIC_MANIFEST01.json',public);save(HERE/'gate01.json',gate)
 binding={'schema_version':1,'identity':NAME,'status':'DRAFT_NOT_RELEASED','gate':ref(HERE/'gate01.json'),'core_manifest':ref(HERE/'CORE_MANIFEST01.json'),'public_manifest':ref(HERE/'PUBLIC_MANIFEST01.json'),'public_refs':ref(T/'PUBLIC_INPUT_REFS_DRAFT01.json'),'transport':private,'transport_binding':ref(T/'BOUND01.json'),'preparation':ref(T/'PREPARED01.json'),'unbound_archive':ref(T/'public01/archive_policy.json'),'public_preparation':ref(T/'MANIFEST01.json'),'binding_readback':ref(T/'BINDING_CHECK01.json'),'input_refs':{role:{k:v[k] for k in ('path','sha256')} for role,v in refs.items()},'binding_review':None,**evidence}
 save(HERE/'BINDING_DRAFT01.json',binding)
 save(HERE/'REGISTRATION_DRAFT01.json',{'status':'DRAFT_NOT_RELEASED','identity':NAME,'parent':OLD,'gate':ref(HERE/'gate01.json'),'source_pins':len(pins),'input_roles':67,'binding_review_missing':True,'qualification':'Root must create BINDING01 with actual binding review and RELEASE_REVIEW01, commit exact sources and authenticate actual recovery before genuine preflight. No admission or claim.'})
if __name__=='__main__':main()
