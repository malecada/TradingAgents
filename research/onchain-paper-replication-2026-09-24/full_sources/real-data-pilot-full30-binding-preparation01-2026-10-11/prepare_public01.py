"""Public metadata only; no binder execution, opaque-input access or authority."""
import copy, hashlib, json
from pathlib import Path
ROOT=Path.cwd().resolve()
HERE=Path(__file__).resolve().parent
F=HERE.parent
OLD=F/'real-data-pilot-full29-input-draft01-2026-10-09'
DRAFT=F/'real-data-pilot-full30-preparation01-2026-10-11'
NAME='eth-paper-real-data-end-to-end-resource-20261011-30'
def raw(x): return (json.dumps(x,sort_keys=True,separators=(',',':'))+'\n').encode()
def sha(b): return hashlib.sha256(b).hexdigest()
def load(p): return json.loads(p.read_bytes())
def ref(p):
 b=p.read_bytes(); return dict(path=str(p.relative_to(ROOT)),sha256=sha(b),bytes=len(b))
def save(p,x):
 with p.open('xb') as f: f.write(raw(x))
def main():
 manifest=load(OLD/'PREPARATION01.json'); docs={}; origins={}
 for role,pin in manifest['public_inputs'].items():
  p=ROOT/pin['path']; assert p.parent==OLD/'public01'
  b=p.read_bytes(); assert sha(b)==pin['sha256'] and len(b)<4194304
  docs[role]=json.loads(b); origins[role]=ref(p)
 docs['execution_job']=load(DRAFT/'execution_job.json'); docs['mcm_policy']=load(DRAFT/'mcm_policy.json')
 docs['pilot']['resource_policy']=copy.deepcopy(docs['execution_job']['resources'])
 docs['archive_transport']['namespace']='ethpilot-20261011-30'; assert docs['archive_transport']['connection'] is None
 docs['archive_policy']['remote_namespace']='ethpilot-20261011-30'; docs['archive_policy']['transport_identity']=None
 selected=docs['execution_job']['payload']['representation_jobs']['original32']
 producer=docs['producer_plan']['producers']['original32']
 for k,v in selected.items(): producer[k]=copy.deepcopy(v)
 for item in (selected,producer):
  for key,role in [('compact_archive_execution','archive_policy'),('compact_execution','compact_policy'),('pair_execution','pair_policy')]:
   item['descriptor'][key]['policy_sha256']=sha(raw(docs[role]))
 public=HERE/'public01'; public.mkdir()
 for role,doc in docs.items(): save(public/(role+'.json'),doc)
 archive=docs.pop('archive_policy'); archive_ref=ref(public/'archive_policy.json')
 prepared={'status':'DRAFT_NOT_REGISTERED_NOT_ADMITTED','independent_approval':False,'builder03_spec':{'template_roles':{'job':'execution_job','producer_plan':'producer_plan','archive':'archive_policy'},'references':{'archive_policy':archive_ref}},'builder03_result':{'status':'DRAFT_NOT_REGISTERED_NOT_ADMITTED','inputs':docs}}
 save(HERE/'PREPARED01.json',prepared)
 # Pinned connection extent is copied from PUBLIC REQUEST02 metadata only.
 old_request=load(F/'real-data-pilot-full29-transport-binding01-2026-10-09/REQUEST02.json')
 assert old_request['connection']['bytes']==485
 save(HERE/'REQUEST01.json',{'prepared':ref(HERE/'PREPARED01.json'),'archive_policy':archive_ref,'connection':old_request['connection'],'private_parent':'research_artifacts/real_pilot_runtime/pilot-transport-20261011-30-01','private_leaf':'archive_transport01.json'})
 old_scratch=F/'real-data-pilot-full29-entry01-2026-10-09/MATCHING_SCRATCH_RESERVATION02.json'
 scratch=load(old_scratch); scratch['experiment']=NAME
 source=ROOT/scratch['installed_source']['path']; scratch['installed_source']['sha256']=sha(source.read_bytes())
 assert scratch['installed_source']['sha256']=='eb509ecf5c9ed7d28783b1a4230013ddcba8036a0fb5174d3aaa60307fc63b43'
 # Historical integration review remains historical, never relabelled current30.
 scratch['historical_integration_review']=scratch.pop('current_integration_review')
 scratch['qualification']=scratch['qualification'].replace('Successor29','Successor30')+' Current30 integration/admission remains pending. Compiled normalization qualification is separate; no native memory or scratch increase.'
 save(HERE/'MATCHING_SCRATCH_RESERVATION01.json',scratch)
 gate=load(DRAFT/'gate.draft01.json'); refs=copy.deepcopy(gate['experiments'][NAME]['inputs']); assert len(refs)==67
 refs.pop('archive_transport') # Never open/hash/stat the historical opaque path.
 for role in (*docs,'archive_policy'):
  if role=='archive_transport': continue
  pin=ref(public/(role+'.json')); refs[role]={'path':pin['path'],'sha256':pin['sha256'],'dataset':'eth'}
 pin=ref(HERE/'MATCHING_SCRATCH_RESERVATION01.json'); refs['matching_ordered_edge_scratch']={'path':pin['path'],'sha256':pin['sha256'],'dataset':'eth'}
 assert len(refs)==66
 save(HERE/'PUBLIC_INPUT_REFS_DRAFT01.json',refs)
 save(HERE/'ORIGINS01.json',{'public_templates':origins,'root_job':ref(DRAFT/'execution_job.json'),'root_mcm':ref(DRAFT/'mcm_policy.json'),'root_gate':ref(DRAFT/'gate.draft01.json'),'scratch':ref(old_scratch),'connection_metadata_only':ref(F/'real-data-pilot-full29-transport-binding01-2026-10-09/REQUEST02.json')})
if __name__=='__main__': main()
