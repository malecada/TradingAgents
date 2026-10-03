"""Stdlib prospective input pack. Does not register, launch, import numerics or claim.

Root supplies genuine installed capsule, immutable numerical Git anchor JSON,
reviewed future native resource JSON and actual runtime inventory JSON. Outputs
are exclusive drafts for registration review, never authority by themselves.
"""
import argparse,hashlib,json,os
from pathlib import Path
HERE=Path(__file__).resolve().parent

def digest(b):return hashlib.sha256(b).hexdigest()
def raw(v):return (json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
def build(root,destination,anchor_file,resources_file,environment_file):
 root=Path(root).resolve();destination=Path(destination).resolve()
 if not destination.is_relative_to(root) or destination.exists():raise ValueError('new owned destination inside genuine capsule required')
 for f in (anchor_file,resources_file,environment_file):
  if not Path(f).is_file() or Path(f).suffix!='.json':raise ValueError('explicit JSON input required')
 destination.mkdir(parents=False)
 def put(name,value):
  b=raw(value);p=destination/(name+'.json')
  with p.open('xb') as s:s.write(b);s.flush();os.fsync(s.fileno())
  return {'path':str(p.relative_to(root)),'sha256':digest(b),'dataset':'synthetic-cold'}
 source={}
 for rel in ('tradingagents/research','research/onchain-paper-replication-2026-09-24/full_sources'):
  for f in sorted((root/rel).rglob('*.py')):
   if '__pycache__' in f.parts:continue
   source[str(f.relative_to(root))]=digest(f.read_bytes())
 source['tradingagents/__init__.py']=digest((root/'tradingagents/__init__.py').read_bytes())
 for name in ('compact_cold_proof.py','compact_cold_proof_inputs.py','compact_cold_proof_native.py','job.py','compact_cold_features.py','compact_native_producer.py','cold_files.py','compact_terminal.py','compact_publication.py','compact_closure.py','job_payload.py'):
  target=root/'tradingagents/research/onchain_replication'/name
  if target.read_bytes()!=(HERE/name).read_bytes():raise ValueError('selected source body not installed: '+name)
 resources=json.loads(Path(resources_file).read_bytes())
 if resources.get('native_unit_limits')!={'file_size_bytes':4194304}:raise ValueError('native unit hard file cap missing')
 if resources['memory_high_bytes']!=resources['memory_max_bytes'] or resources['memory_max_bytes']!=3*1024**3 or resources['reserve_bytes']<3*1024**3 or resources['disk_floor_bytes']!=10*1024**3 or resources['wall_seconds']!=1800:raise ValueError('finite proposed native bounds differ')
 watch=resources['storage_budget'];wp=Path(watch['root'])
 if not wp.is_absolute() or wp.resolve()!=wp or not (root/'research_artifacts/compact-cold-engineering-20261003').is_relative_to(wp):raise ValueError('whole owned tree watch missing')
 anchor=json.loads(Path(anchor_file).read_bytes());environment=json.loads(Path(environment_file).read_bytes())
 if set(anchor)!={'commit','files'} or len(anchor['commit'])!=40 or not anchor['files']:raise ValueError('actual numerical source anchor missing')
 inputs={}
 for name,file in (('recipe','recipe01.json'),('configs','configs01.json'),('model','model01.json'),('training','training01.json')):inputs[name]=put(name,json.loads((HERE/file).read_bytes()))
 for name,value in (('anchor',anchor),('future_resources',resources),('environment',environment)):inputs[name]=put(name,value)
 policy={'schema_version':1,'kind':'genuine-compact-cold-engineering-proof-v1','phase':'materialize','experiment':'compact-cold-inputs-20261003-01','output':'proof-materialize.json',
  'inputs':{n:n for n in ('recipe','configs','model','training','anchor','future_resources')},'source_files':source,'watch':watch,'max_file_bytes':4194304,'max_total_bytes':268435456}
 inputs['cold_proof']=put('cold_proof',policy)
 execution={'schema_version':1,'kind':'fit','environment_input':'environment','resources':resources,'payload':{'cold_proof_input':'cold_proof','representation_jobs':{}}}
 inputs['execution_job']=put('execution_job',execution)
 draft={'schema_version':1,'kind':'unregistered-engineering-input-draft','program_id':'compact-cold-engineering-20261003','separate_family_required':True,'maximum_attempts':2,
  'identities':['compact-cold-inputs-20261003-01','compact-cold-comparison-20261003-01'],'first_experiment':{'inputs':inputs,'source_files':source,'cells':['cold-input-materialization'],'outputs':['proof-materialize.json']},
  'pending':['root source/Git/runtime verification','charter/gate and distinct family/ledger registration','cumulative budget review for this engineering program','native profile readback: swap0/two CPUs/4MiB file cap/whole-tree watch','independent exact release before numerical imports','materialize guarded; then freeze emitted population/batches/policies and register second exact identity'],
  'launch_authorized_by_this_file':False}
 put('registration-draft',draft)
 fd=os.open(destination,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
 return draft
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--destination',required=True);p.add_argument('--anchor-json',required=True);p.add_argument('--resources-json',required=True);p.add_argument('--environment-json',required=True);a=p.parse_args()
 build(a.root,a.destination,a.anchor_json,a.resources_json,a.environment_json)
