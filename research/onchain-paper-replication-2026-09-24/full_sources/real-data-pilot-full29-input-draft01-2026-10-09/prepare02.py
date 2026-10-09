"""Public metadata/header-only draft. Never reads private transport or array payloads."""
import ast,copy,hashlib,json,subprocess,types,difflib
from pathlib import Path
ROOT=Path.cwd().resolve(); HERE=Path(__file__).resolve().parent; F=HERE.parent
OLD='eth-paper-real-data-end-to-end-resource-20261009-28'; NEW=OLD[:-2]+'29'
raw=lambda v:(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def ref(p):return {'path':str(p.relative_to(ROOT)),'sha256':sha(p)}
def save(n,v):
 p=HERE/n
 with p.open('xb') as s:s.write(raw(v))
 return ref(p)
def authenticated(r):
 p=ROOT/r['path'];assert sha(p)==r['sha256'];return load(p)
def move(v):
 if type(v)is dict:return {k:move(x) for k,x in v.items()}
 if type(v)is list:return [move(x) for x in v]
 if type(v)is str:return v.replace(OLD,NEW).replace('ethpilot-20261009-28','ethpilot-20261009-29').replace('real-eth-seven-graph-joint-update-resource28','real-eth-seven-graph-joint-update-resource29')
 return v
binding_path=F/'real-data-pilot-full28-entry01-2026-10-09/BINDING01.json';binding=load(binding_path)
entry=authenticated(binding['gate'])['experiments'][OLD]
refs=load(F/'real-data-pilot-full28-transport-binding01-2026-10-09/ALL_INPUT_REFS01.json');assert refs==entry['inputs']
roles=['archive_policy','compact_policy','execution_job','mcm_output_policy','mcm_policy','original_import','pair_policy','pilot','producer_plan','resource_population_plan','typed_payload']
original={role:authenticated(refs[role]) for role in roles}
public_transport=F/'real-data-pilot-full28-input-draft01-2026-10-09/public02/archive_transport.json'
original['archive_transport']=load(public_transport);assert original['archive_transport']['connection'] is None
docs=move(copy.deepcopy(original));docs['archive_policy']['transport_identity']=None
package=ROOT/'tradingagents/research/onchain_replication'
# Execute ONLY the exact pure roster function, not job or numerical runtime imports.
tree=ast.parse((package/'job.py').read_text()); fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='required_sources')
ns={'Path':Path,'__file__':str(package/'job.py')};exec(compile(ast.Module(body=[fn],type_ignores=[]),'job.required_sources AST','exec'),ns)
names=ns['required_sources']();current={n:sha(ROOT/n) for n in sorted(names)}
commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
# Each source body must actually exist at this commit with the same digest.
p=subprocess.Popen(['git','cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
try:
 for n,digest in current.items():
  p.stdin.write((commit+':'+n+'\n').encode());p.stdin.flush(); header=p.stdout.readline().split();assert len(header)==3 and header[1]==b'blob'
  body=p.stdout.read(int(header[2]));assert p.stdout.read(1)==b'\n' and hashlib.sha256(body).hexdigest()==digest
finally:p.stdin.close();assert p.wait()==0
integration=F/'pilot-full28-to-successor-integration-review01-2026-10-09/INTEGRATION_REVIEW01.json'
assert sha(integration)=='5ad8ec47a7c02033514e3d5fe7eb292079f068f04310cc551aeb77215e42f8d3'
for row in load(integration)['installed_sources']:assert current[row['path']]==row['after_sha256']
docs['pair_policy']['numerical_source']={'commit':commit,'files':current}
e=docs['mcm_policy']['batched']['execution'];e.update(edge_cache_policy={'format':'adaptive-lazy-edge-cache-v1','max_edge_products':16384,'chunk_entries':256,'max_scratch_bytes':262144},geometry={'format':'provisional-pair-geometry-v1','max_body_bytes':1536},binding_timing={'format':'binding-lease-phases-v1','max_body_bytes':640})
# Header-only cardinality. No ndarray loader and no payload reads.
rows=[]
for role in sorted(r for r in refs if r.startswith('graph_')):
 manifest=authenticated(refs[role]);mp=ROOT/refs[role]['path'];headers={}
 for key in ('node_features','edge_index'):
  a=manifest['arrays'][key];path=mp.parent/a['path'];assert path.stat().st_size==a['bytes']
  with path.open('rb') as stream:
   lead=stream.read(8);assert lead[:6]==b'\x93NUMPY';width=2 if lead[6]==1 else 4;lengthraw=stream.read(width);length=int.from_bytes(lengthraw,'little');assert 0<length<=65536
   body=stream.read(length);assert len(body)==length;meta=ast.literal_eval(body.decode('latin1'))
  headers[key]={'shape':meta['shape'],'descr':meta['descr'],'header_bytes':8+width+length,'header_sha256':hashlib.sha256(lead+lengthraw+body).hexdigest(),'path':str(path.relative_to(ROOT))}
 n=headers['node_features']['shape'][0];cells=n*32;batches=(cells+4095)//4096
 rows.append({'role':role,'nodes':n,'cells':cells,'batches':batches,'groups':(batches+15)//16,'summary_bytes':batches*8192,'headers':headers})
assert sum(r['cells'] for r in rows)==415968128 and sum(r['batches'] for r in rows)==101559
assert sum(r['summary_bytes'] for r in rows)==831971328
assert max(r['summary_bytes'] for r in rows)<=e['max_summary_bytes']
# Actual scalar metadata validator with only its explicit policy dependencies, no module imports.
def require(ok,message):
 if not ok:raise ValueError(message)
def function(path,name,scope):
 t=ast.parse(path.read_text());n=next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name==name);exec(compile(ast.Module(body=[n],type_ignores=[]),str(path)+' AST','exec'),scope);return scope[name]
adaptive=types.SimpleNamespace(freeze=function(package/'adaptive_edge_policy.py','freeze',{}))
gs={'POLICY':e['geometry'],'require':require};geometry=types.SimpleNamespace(policy=function(package/'geometry_publication.py','policy',gs))
ms={'require':require,'BINDING_TIMING_POLICY':e['binding_timing']};timing=types.SimpleNamespace(binding_timing_policy=function(package/'matching_owner.py','binding_timing_policy',ms))
scope={'require':require,'FORMAT':'ordered-mcm-batch-closure-v2','adaptive_edge_policy':adaptive,'geometry_publication':geometry,'matching_owner':timing}
function(package/'compact_mcm_batched.py','selected',scope);validate=function(package/'compact_mcm_batched.py','validate',scope)
for row in rows:validate(docs['mcm_policy'],row['cells'])
selected=docs['execution_job']['payload']['representation_jobs']['original32'];producer=docs['producer_plan']['producers']['original32']
for role,key in [('pair_policy','pair_execution'),('compact_policy','compact_execution'),('archive_policy','compact_archive_execution')]:
 for v in (selected,producer):v['descriptor'][key]['policy_sha256']=hashlib.sha256(raw(docs[role])).hexdigest()
assert selected['descriptor']==producer['descriptor']
assert selected['descriptor']['configs']==original['execution_job']['payload']['representation_jobs']['original32']['descriptor']['configs']
assert docs['execution_job']['resources']==move(original['execution_job']['resources'])
assert docs['mcm_policy']['batched']['execution']['max_summary_bytes']==original['mcm_policy']['batched']['execution']['max_summary_bytes']
(HERE/'public01').mkdir();out={};patch=[]
for role in sorted(docs):
 out[role]=save('public01/'+role+'.json',docs[role]);refs[role]={**out[role],'dataset':refs[role]['dataset']}
 patch+=list(difflib.unified_diff(json.dumps(original[role],indent=2,sort_keys=True).splitlines(True),json.dumps(docs[role],indent=2,sort_keys=True).splitlines(True),fromfile='public28/'+role,tofile='draft29/'+role))
refs['matching_ordered_edge_scratch']={**save('MATCHING_SCRATCH_RESERVATION01.json',move(authenticated(refs['matching_ordered_edge_scratch']))),'dataset':refs['matching_ordered_edge_scratch']['dataset']}
fullnames=set(entry['source_files'])|names;full={n:sha(ROOT/n) for n in sorted(fullnames)}
save('SOURCE_MAP01.json',{'status':'DRAFT_NOT_RELEASED','source_anchor':commit,'numerical_sources':current,'source_files':full,'baseline_source_count':len(entry['source_files']),'new_numerical_sources':sorted(names-set(original['pair_policy']['numerical_source']['files'])),'integration_review':ref(integration),'qualification':'Numerical bodies authenticated at anchor; full source union is current metadata, requires Root final gate closure and final commit authentication.'})
save('PUBLIC_INPUT_REFS01.json',refs)
save('CARDINALITY01.json',{'graphs':rows,'cells':sum(x['cells'] for x in rows),'batches':101559,'summary_bytes':831971328,'per_stage_max_summary_bytes':e['max_summary_bytes'],'qualification':'Only manifest and NPY headers read; full payload hashes are historical declared references, not revalidated here.'})
save('PREPARATION01.json',{'status':'DRAFT_NOT_RELEASED','identity':NEW,'baseline_binding':ref(binding_path),'baseline_gate':binding['gate'],'sanitized_transport_source':ref(public_transport),'public_inputs':out,'integration_review':ref(integration),'source_anchor':commit,'unresolved':{'archive_transport_connection':None,'archive_policy_transport_identity':None},'remaining_root_work':['Reserve fresh29 identity and cumulative allowance; no reservation made by this draft.','Bind genuine private transport and actual transport_identity, cascade archive descriptor digests.','Authenticate final union source closure/runtime, gate64 roles plus new review evidence, source commit and genuine input binder.','Fresh namespace/currentness/capacity/physical remote checks, external recovery and final admission/claim remain Root-owned.'],'qualification':'Existing immutable original samples/science/model/training retained. Geometry and binding timing are local provisional summary metadata; grouped archive format unchanged.'})
save('CHECK01.json',{'decision':'PASS_DRAFT_METADATA_ONLY','public_documents':len(docs),'input_roles':len(refs),'numerical_sources':len(current),'source_union':len(full),'graphs':len(rows),'actual_scalar_policy_validator_cases':len(rows),'native_resource_body_unchanged_except_identity':True,'scientific_descriptor_configs_unchanged':True,'summary_reservation_unchanged':True,'private_transport_read':False,'array_payloads_read':False})
(HERE/'public-diff.patch').write_text(''.join(patch))
print(json.dumps({'decision':'PASS_DRAFT_METADATA_ONLY','numerical_sources':len(current),'source_union':len(full),'max_graph_cells':max(r['cells'] for r in rows),'max_summary_bytes':e['max_summary_bytes'],'anchor':commit}))
