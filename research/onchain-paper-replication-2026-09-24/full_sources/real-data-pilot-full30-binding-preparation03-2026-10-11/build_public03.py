"""Source/public metadata only: exact numerical roster and genuine namespace."""
import ast,difflib,hashlib,json,os,datetime
from pathlib import Path
ROOT=Path.cwd().resolve();H=Path(__file__).resolve().parent;F=H.parent;O=F/'real-data-pilot-full30-binding-preparation02-2026-10-11';ENTRY=F/'real-data-pilot-full30-entry-preparation01-2026-10-11'
NAME='eth-paper-real-data-end-to-end-resource-20261011-30';ANCHOR='f63cf196ea5e9d344c365b04cfeb16df6f1ffb0d'
def raw(v):return (json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
def load(p):return json.loads(p.read_bytes())
def pin(p):
 b=p.read_bytes();return {'path':str(p.relative_to(ROOT)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def save(p,v):
 with p.open('xb') as f:f.write(raw(v))
def main():
 jobsource=ROOT/'tradingagents/research/onchain_replication/job.py';tree=ast.parse(jobsource.read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='required_sources');scope={'Path':Path,'__file__':str(jobsource)};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(jobsource),'exec'),scope)
 required=scope['required_sources']();assert len(required)==198
 files={p:pin(ROOT/p)['sha256'] for p in sorted(required)}
 docs={p.stem:load(p) for p in (O/'public01').glob('*.json')};old=docs['pair_policy']['numerical_source'];added=sorted(set(files)-set(old['files']));changed=sorted(p for p in set(files)&set(old['files']) if files[p]!=old['files'][p]);assert len(added)==2 and len(changed)==8
 docs['pair_policy']['numerical_source']={'commit':ANCHOR,'files':files}
 docs['archive_transport']['namespace']='ethpilot-20261011-30';docs['archive_policy']['remote_namespace']='ethpilot-20261011-30'
 assert docs['archive_transport']['connection'] is None and docs['archive_policy']['transport_identity'] is None
 for item in (docs['execution_job']['payload']['representation_jobs']['original32'],docs['producer_plan']['producers']['original32']):
  for role,key in [('pair_policy','pair_execution'),('archive_policy','compact_archive_execution')]:item['descriptor'][key]['policy_sha256']=hashlib.sha256(raw(docs[role])).hexdigest()
 gate=load(ENTRY/'gate02.json');ex=gate['experiments'][NAME];assert ex['cells']==[docs['pilot']['cell_id']]
 assert all(ex['source_files'].get(k)==v for k,v in files.items())
 (H/'public01').mkdir()
 for role,value in docs.items():save(H/'public01'/(role+'.json'),value)
 (H/'MATCHING_SCRATCH_RESERVATION01.json').write_bytes((O/'MATCHING_SCRATCH_RESERVATION01.json').read_bytes())
 prepared=load(O/'PREPARED01.json');prepared['builder03_result']['inputs']={k:v for k,v in docs.items() if k!='archive_policy'};prepared['builder03_spec']['references']['archive_policy']=pin(H/'public01/archive_policy.json');save(H/'PREPARED01.json',prepared)
 request=load(O/'REQUEST01.json');request.update(prepared=pin(H/'PREPARED01.json'),archive_policy=pin(H/'public01/archive_policy.json'),private_parent='research_artifacts/real_pilot_runtime/pilot-transport-20261011-30-03');save(H/'REQUEST01.json',request)
 refs=load(O/'PUBLIC_INPUT_REFS_DRAFT01.json')
 for role in docs:
  if role=='archive_transport':continue
  p=pin(H/'public01'/(role+'.json'));refs[role].update(path=p['path'],sha256=p['sha256'])
 p=pin(H/'MATCHING_SCRATCH_RESERVATION01.json');refs['matching_ordered_edge_scratch'].update(path=p['path'],sha256=p['sha256']);assert len(refs)==66;save(H/'PUBLIC_INPUT_REFS_DRAFT01.json',refs)
 wrapper=(O/'bind_actual01.py').read_text().replace('pilot-transport-20261011-30-02','pilot-transport-20261011-30-03').replace('archive-dispatch-ethpilot-20261011-30v2','archive-dispatch-ethpilot-20261011-30');(H/'bind_actual01.py').write_text(wrapper)
 absent={str(p.relative_to(ROOT)):not os.path.lexists(p) for p in [ROOT/'research_runs'/NAME,ROOT/'research_artifacts/archive-dispatch-ethpilot-20261011-30',ROOT/request['private_parent']]};assert all(absent.values())
 save(H/'NAMESPACE_OBSERVATION01.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'absent':absent,'qualification':'Local lstat-style namespace absence only, no remote availability or reservation. Original offline publications remain immutable. Root must repeat freshness at genuine entry.'})
 save(H/'SOURCE_JOIN01.json',{'anchor':ANCHOR,'anchor_basis':'Root-provided committed integration anchor; no Git executed here; genuine matching_owner._source must authenticate all anchor blobs.','required_sources_function':pin(jobsource),'source_files':files,'added':added,'changed':changed,'current_gate_metadata':pin(ENTRY/'gate02.json'),'original_prefight_failure':pin(ENTRY/'ROOT_PREFLIGHT_OPERATION01.json'),'caller':pin(ROOT/'tradingagents/research/onchain_replication/real_pilot_import_caller.py')})
 patches=[]
 for p in sorted((H/'public01').glob('*.json')):
  q=O/'public01'/p.name;patches.extend(difflib.unified_diff(q.read_text().splitlines(True),p.read_text().splitlines(True),fromfile=str(q),tofile=str(p)))
 for name in ('bind_actual01.py','PREPARED01.json','REQUEST01.json','PUBLIC_INPUT_REFS_DRAFT01.json'):
  p=H/name;q=O/name;patches.extend(difflib.unified_diff(q.read_text().splitlines(True),p.read_text().splitlines(True),fromfile=str(q),tofile=str(p)))
 (H/'LITERAL_PATCH01.diff').write_text(''.join(patches))
if __name__=='__main__':main()
