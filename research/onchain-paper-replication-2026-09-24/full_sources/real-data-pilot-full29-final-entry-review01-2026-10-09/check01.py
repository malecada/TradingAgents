import pathlib,json,hashlib,ast,copy,os,subprocess
ROOT=pathlib.Path.cwd();R=pathlib.Path(__file__).resolve().parent;F=R.parent;E=F/'real-data-pilot-full29-entry01-2026-10-09';O=F/'real-data-pilot-full28-entry01-2026-10-09';T=F/'real-data-pilot-full29-transport-binding01-2026-10-09';name='eth-paper-real-data-end-to-end-resource-20261009-29';oldname=name[:-2]+'28'
j=lambda p:json.loads(pathlib.Path(p).read_bytes());h=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest();norm=lambda x:{k:{q:v[q] for q in ('path','sha256')} for k,v in x.items()}
b=j(E/'BINDING_DRAFT01.json');g=j(E/'gate01.json');x=g['experiments'][name];ob=j(O/'BINDING01.json');og=j(O/'gate01.json');ox=og['experiments'][oldname];ev={};checks=[]
def pin(v):
 p=ROOT/v['path'];s=p.lstat();assert p.resolve()==p and p.is_file() and s.st_nlink==1;assert h(p)==v['sha256'],str(p)
 if 'bytes'in v:assert s.st_size==v['bytes']
 ev[v['path']]=v['sha256']
def add(p):pin({'path':str(p.relative_to(ROOT)),'sha256':h(p)})
def move(v):
 if type(v)is dict:return {move(k):move(a) for k,a in v.items()}
 if type(v)is list:return [move(a) for a in v]
 if type(v)is str:return v.replace('20261009-28','20261009-29').replace('resource28','resource29')
 return v
assert len(x['source_files'])==455
for p,v in x['source_files'].items():pin({'path':p,'sha256':v})
refs=norm(x['inputs']);assert len(refs)==64 and refs==b['input_refs']==norm(j(T/'ALL_INPUT_REFS02.json'))
for v in refs.values():pin(v)
for v in b.values():
 if type(v)is dict and {'path','sha256'}<=v.keys():pin(v)
assert {k:v['dataset'] for k,v in x['inputs'].items()}=={k:v['dataset'] for k,v in ox['inputs'].items()}
checks.append('455 local source and64 input hashes; all draft references and dataset labels')
p=j(ROOT/b['preparation']['path']);bound=j(ROOT/b['transport_binding']['path']);pub=j(ROOT/b['public_manifest']['path']);core=j(ROOT/b['core_manifest']['path']);cap=j(ROOT/b['capacity_observation']['path']);oldp=j(ROOT/ob['preparation']['path']);a=copy.deepcopy(p['builder03_result']['inputs']);old=move(oldp['builder03_result']['inputs']);pair=a['pair_policy'];numeric=pair['numerical_source'];assert len(numeric['files'])==196
assert all(x['source_files'].get(k)==v for k,v in numeric['files'].items())
assert len(set(numeric['files'])-set(old['pair_policy']['numerical_source']['files']))==3
assert {k:v for k,v in pair.items() if k!='numerical_source'}=={k:v for k,v in old['pair_policy'].items() if k!='numerical_source'}
a['pair_policy']=old['pair_policy'];controls=a['mcm_policy']['batched']['execution'];selected={k:controls.pop(k) for k in ('edge_cache_policy','geometry','binding_timing')}
assert selected=={'edge_cache_policy':{'format':'adaptive-lazy-edge-cache-v1','max_edge_products':16384,'chunk_entries':256,'max_scratch_bytes':262144},'geometry':{'format':'provisional-pair-geometry-v1','max_body_bytes':1536},'binding_timing':{'format':'binding-lease-phases-v1','max_body_bytes':640}}
assert controls['max_summary_bytes']==144998400
for v,ov in ((a['execution_job']['payload']['representation_jobs']['original32'],old['execution_job']['payload']['representation_jobs']['original32']),(a['producer_plan']['producers']['original32'],old['producer_plan']['producers']['original32'])):
 for k in ('pair_execution','compact_archive_execution'):v['descriptor'][k]['policy_sha256']=ov['descriptor'][k]['policy_sha256']
assert a==old,'unexpected prepared scientific/policy delta'
checks.append('Prepared inverse: identity,196 numerical pins and three fixed controls only; all original scientific/model/training/native policies preserved')
assert bound['source_request']['prepared']==b['preparation'] and bound['source_request']['archive_policy']==b['unbound_archive'] and p['builder03_spec']['references']['archive_policy']==b['unbound_archive']
assert len(bound['inputs'])==11
for role,body in bound['inputs'].items():assert j(ROOT/refs[role]['path'])==body
z=copy.deepcopy(bound['inputs']);archive=z.pop('archive_policy');archive['transport_identity']=None;assert archive==j(ROOT/b['unbound_archive']['path'])
for v in (z['execution_job']['payload']['representation_jobs']['original32'],z['producer_plan']['producers']['original32']):v['descriptor']['compact_archive_execution']['policy_sha256']=bound['binding']['prior_descriptor_policy_sha256']
z['archive_transport']=p['builder03_result']['inputs']['archive_transport'];assert z==p['builder03_result']['inputs'];assert bound['private_input']=={'archive_transport':b['transport']}
assert len(core['inputs'])==4
for role,v in core['inputs'].items():pin(v);assert j(ROOT/refs[role]['path'])==j(ROOT/v['path'])
for v in (bound['inputs']['execution_job']['payload']['representation_jobs']['original32'],bound['inputs']['producer_plan']['producers']['original32']):
 d=v['descriptor'];assert len(d['required_graphs'])==7 and d['configs']['dictionary']['size']==32 and d['configs']['dictionary']['sample_count']==512
 for k,role in [('pair_execution','pair_policy'),('compact_execution','compact_policy'),('compact_archive_execution','archive_policy')]:assert d[k]['policy_sha256']==refs[role]['sha256']
checks.append('Exact bound public inverse, four core bodies, seven full graphs/32 motifs/512 samples and descriptor hashes')
assert cap['source_body_pins']==pub['source_pins'] and len(pub['source_pins'])==419
assert cap['source_anchor']==numeric['commit'] and cap['source_anchor'].startswith('d6cf861d')
combined=dict(pub['source_pins']);combined.update(numeric['files']);assert all(x['source_files'].get(k)==v for k,v in combined.items())
env=dict(os.environ,GIT_NO_LAZY_FETCH='1');paths=list(combined);raw=subprocess.check_output(['git','cat-file','--batch'],input=('\n'.join(cap['source_anchor']+':'+s for s in paths)+'\n').encode(),env=env);pos=0
for path in paths:
 end=raw.index(b'\n',pos);hdr=raw[pos:end].split();assert hdr[1]==b'blob';n=int(hdr[2]);pos=end+1;assert hashlib.sha256(raw[pos:pos+n]).hexdigest()==combined[path];pos+=n+1
assert pos==len(raw)
for k in ('new_allocated_growth_bytes','new_logical_growth_bytes','new_entries','directory_allocated_bound_bytes','other_writer_reserved_bytes','non_directory_new_allocated_growth_bytes'):assert cap[k]==j(ROOT/ob['capacity_observation']['path'])[k]
checks.append('419 public source pins plus196 numerical pins authenticate committed d6 anchor; all capacity terms unchanged')
cor=j(T/'BINDER_DEPENDENCY_CORRECTION01.json');assert (ROOT/cor['original_binder']['path']).read_bytes()==(ROOT/cor['new_binder']['path']).read_bytes();pin(cor['new_binder']);assert {k for k in cor['current_dependencies'] if cor['current_dependencies'][k]!=cor['original_dependencies'][k]}=={'dispatch'}
for k,v in cor['current_dependencies'].items():pin(v)
def funcs(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(pathlib.Path(path).read_bytes()).body if isinstance(n,ast.FunctionDef)}
f1=funcs(ROOT/cor['before_source']['path']);f2=funcs(ROOT/cor['current_dependencies']['dispatch']['path']);assert all(f1[k]==f2[k] for k in ('require','_connection'))
for n in ('bind_actual01.py','bind_actual02.py','BIND_REFUSAL01.json','POST_BIND_REPORT_REFUSAL02.json','BINDING_READBACK02.json','binder02/DEPENDENCIES01.json'):
 if (T/n).exists():add(T/n)
checks.append('Binder exact body; dispatch-only dependency correction; require/_connection AST unchanged; both actual wrapper failures retained')
assert x['cumulative_budget_extension']['review']==b['budget_review'];br=j(ROOT/b['budget_review']['path']);assert br['decision']=='accepted';extref=x['cumulative_budget_extension']['extension'];pin(extref);ext=j(ROOT/extref['path']);pin(ext['allocation']);assert ext['cumulative_ceiling']==100 and ext['consumed_before']==68
for v in (extref,ext['allocation'],b['budget_review']):assert x['source_files'].get(v['path'])==v['sha256']
assert g['experiments'][oldname]==j(ROOT/'research_runs'/oldname/'claim.json')['experiment']
for k in ('families','datasets','program_id'):assert g[k]==og[k]
for role in set(refs)-set(bound['inputs'])-{'archive_transport','matching_ordered_edge_scratch'}:assert refs[role]==ob['input_refs'][role]
assert not (ROOT/'research_runs'/name).exists()
pre=(E/'preflight29_01.py').read_text();oldpre=(O/'preflight28_01.py').read_text();start=pre.index("    execution=mcm['batched']['execution']");end=pre.index("    schedule=",start);inverse=pre[:start]+pre[end:];inverse=inverse.replace('20261009-29','20261009-28').replace('!=100','!=99').replace("'effective_attempt_budget':100","'effective_attempt_budget':99").replace('real-data-pilot-full29-transport-binding01-2026-10-09/binder02/bind01.py','real-data-pilot-transport-binding-preparation01-2026-10-06/bind01.py');assert inverse==oldpre
assert (E/'root_io29_01.py').read_text().replace('preflight29_01','preflight28_01')==(O/'root_io28_01.py').read_text()
for q in (E/'preflight29_01.py',E/'root_io29_01.py',E/'BINDING_DRAFT01.json'):add(q)
checks.append('Preflight exact inverse except identity100/binder directory/strict controls; RootIO module-only; genuine100 budget and claimed28 parent joined')
defects=[]
if p['preparation_origin']['public_manifest']!=b['public_manifest']:defects.append({'predicate':'prepared[preparation_origin][public_manifest] == binding[public_manifest]','actual':p['preparation_origin']['public_manifest'],'expected':b['public_manifest'],'required_change':'Join immutable actual origin to binding.public_preparation separately; preserve public_manifest source/capacity join.'})
out={'decision':'withheld' if defects else 'accepted','identity':name,'input_refs':refs,'evidence':ev,'checks':checks,'defects':defects,'qualification':'Source and metadata review only. Sole current29 opaque input hash/stat only. Wrapper02 remains failed after outputs; no Run/Owner/numerical imports or network. Current eligibility and final declared public increment recovery remain required.'};(R/'CHECK01.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'decision':out['decision'],'checks':len(checks),'evidence':len(ev),'defects':defects}))
