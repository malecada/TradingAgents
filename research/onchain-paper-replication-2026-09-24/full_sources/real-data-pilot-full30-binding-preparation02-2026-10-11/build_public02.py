"""Mechanical public-only successor; never execute binder or read private input."""
import copy,difflib,hashlib,json
from pathlib import Path
ROOT=Path.cwd().resolve();HERE=Path(__file__).resolve().parent;F=HERE.parent
OLD=F/'real-data-pilot-full30-binding-preparation01-2026-10-11'
R=F/'matching-compiled-runtime-input02-2026-10-11';R0=F/'matching-compiled-runtime-input01-2026-10-10'
def raw(x):return (json.dumps(x,sort_keys=True,separators=(',',':'))+'\n').encode()
def load(p):return json.loads(p.read_bytes())
def pin(p):
 b=p.read_bytes();return {'path':str(p.relative_to(ROOT)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def save(p,x):
 with p.open('xb') as f:f.write(raw(x))
def main():
 inv=load(R0/'INVENTORY01.json');reference=load(R0/'RUNTIME_REFERENCE01.json')
 assert reference['runtime_inventory_sha256']==pin(R0/'INVENTORY01.json')['sha256']
 env=next(v for v in inv['references'] if v['path'].endswith('/draft07/templates/environment.json'))
 environment=Path(env['path']);actual=pin(environment)
 assert actual['sha256']==env['sha256']=='3a97a20ba8058cac81c8c62a7ba3596aac2fe4deb17627d0aa57bf53a93b86dc' and actual['bytes']==env['bytes']
 reference['runtime_inventory_sha256']=actual['sha256'];save(R/'RUNTIME_REFERENCE01.json',reference)
 policy=load(R0/'POLICY01.json');runtime=pin(R/'RUNTIME_REFERENCE01.json')
 policy.update(runtime_path=str(R/'RUNTIME_REFERENCE01.json'),runtime_sha256=runtime['sha256'],runtime_bytes=runtime['bytes']);save(R/'POLICY01.json',policy)
 save(R/'LINEAGE01.json',{'original_inventory':pin(R0/'INVENTORY01.json'),'original_runtime':pin(R0/'RUNTIME_REFERENCE01.json'),'environment':actual,'caller':pin(ROOT/'tradingagents/research/onchain_replication/compact_mcm_batched.py'),'parser':pin(ROOT/'tradingagents/research/onchain_replication/compiled_normalization_policy.py'),'qualification':'Only runtime_inventory_sha256 semantics corrected to genuine environment body; existing metadata observation retained, no new runtime measurement.'})
 docs={p.stem:load(p) for p in (OLD/'public01').glob('*.json')}
 docs['mcm_policy']['batched']['execution']['compiled_normalization_policy']=policy
 docs['archive_transport']['namespace']='ethpilot-20261011-30v2';docs['archive_policy']['remote_namespace']='ethpilot-20261011-30v2'
 assert docs['archive_transport']['connection'] is None and docs['archive_policy']['transport_identity'] is None
 for item in (docs['execution_job']['payload']['representation_jobs']['original32'],docs['producer_plan']['producers']['original32']):item['descriptor']['compact_archive_execution']['policy_sha256']=hashlib.sha256(raw(docs['archive_policy'])).hexdigest()
 (HERE/'public01').mkdir()
 for role,value in docs.items():save(HERE/'public01'/(role+'.json'),value)
 (HERE/'MATCHING_SCRATCH_RESERVATION01.json').write_bytes((OLD/'MATCHING_SCRATCH_RESERVATION01.json').read_bytes())
 prepared=load(OLD/'PREPARED01.json');prepared['builder03_result']['inputs']={k:v for k,v in docs.items() if k!='archive_policy'};prepared['builder03_spec']['references']['archive_policy']=pin(HERE/'public01/archive_policy.json');save(HERE/'PREPARED01.json',prepared)
 request=load(OLD/'REQUEST01.json');request.update(prepared=pin(HERE/'PREPARED01.json'),archive_policy=pin(HERE/'public01/archive_policy.json'),private_parent='research_artifacts/real_pilot_runtime/pilot-transport-20261011-30-02');save(HERE/'REQUEST01.json',request)
 refs=load(OLD/'PUBLIC_INPUT_REFS_DRAFT01.json')
 for role in docs:
  if role=='archive_transport':continue
  p=pin(HERE/'public01'/(role+'.json'));refs[role].update(path=p['path'],sha256=p['sha256'])
 p=pin(HERE/'MATCHING_SCRATCH_RESERVATION01.json');refs['matching_ordered_edge_scratch'].update(path=p['path'],sha256=p['sha256'])
 refs['compiled_normalization_runtime'].update(path=runtime['path'],sha256=runtime['sha256']);assert len(refs)==66;save(HERE/'PUBLIC_INPUT_REFS_DRAFT01.json',refs)
 wrapper=(OLD/'bind_actual01.py').read_text().replace('pilot-transport-20261011-30-01','pilot-transport-20261011-30-02').replace('archive-dispatch-ethpilot-20261011-30','archive-dispatch-ethpilot-20261011-30v2');(HERE/'bind_actual01.py').write_text(wrapper)
 patches=[]
 for p in sorted((HERE/'public01').glob('*.json')):
  q=OLD/'public01'/p.name;patches.extend(difflib.unified_diff(q.read_text().splitlines(True),p.read_text().splitlines(True),fromfile=str(q),tofile=str(p)))
 for name in ('bind_actual01.py','PREPARED01.json','REQUEST01.json','PUBLIC_INPUT_REFS_DRAFT01.json'):
  q=OLD/name;p=HERE/name;patches.extend(difflib.unified_diff(q.read_text().splitlines(True),p.read_text().splitlines(True),fromfile=str(q),tofile=str(p)))
 (HERE/'LITERAL_PATCH01.diff').write_text(''.join(patches))
 (R/'LITERAL_PATCH01.diff').write_text(''.join(difflib.unified_diff((R0/'RUNTIME_REFERENCE01.json').read_text().splitlines(True),(R/'RUNTIME_REFERENCE01.json').read_text().splitlines(True),fromfile=str(R0/'RUNTIME_REFERENCE01.json'),tofile=str(R/'RUNTIME_REFERENCE01.json'))))
if __name__=='__main__':main()
