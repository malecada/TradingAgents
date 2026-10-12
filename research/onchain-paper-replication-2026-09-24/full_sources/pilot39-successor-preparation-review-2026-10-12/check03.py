"""Independent finite static/metadata/scalar checks of unregistered39 candidates."""
import ast,copy,difflib,hashlib,json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;F=HERE.parent
PUB=F/'pilot39-public-preparation-candidate-2026-10-12';CAP=F/'pilot39-whole-capacity-candidate-2026-10-12';P38=F/'real-data-pilot-full38-binding-preparation01-2026-10-12'
NAME='eth-paper-real-data-end-to-end-resource-20261012-39';CELL='real-eth-whole-seven-graph-joint-pilot-resource39'
def load(p):return json.loads(p.read_bytes())
def pin(p):
 b=p.read_bytes();return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def auth(r):assert pin(ROOT/r['path'])==r
manifest=load(PUB/'SOURCE_MANIFEST01.json')
for r in manifest['baselines']+[manifest['builder'],manifest['entry_join_helper'],manifest['accepted38_numerical_source_declaration']]:auth(r)
assert manifest['builder']['sha256']=='ebf6692da7b38dfaf22b1c155f661ec5d3c99e798fa2ca6a24f1f342e6127204'
assert manifest['entry_join_helper']['sha256']=='5afc6ca4b753cf555c7e8740c846b9e5f5474a6b50b2dbd37ba43d2d72207943'
for p,d in manifest['accepted_six_source_bodies'].items():assert pin(ROOT/p)['sha256']==d
for name,d in load(CAP/'MANIFEST01.json').items():assert pin(CAP/name)['sha256']==d
assert pin(CAP/'capacity.py')['sha256']=='c1d391d2b9d1decc734a4719a57c8e809b0b2ec68622383066c6dfb39cef1586'
candidate=(PUB/'build_public01.py').read_text()
def legacy_dump(body):
 tree=ast.parse(body)
 for node in ast.walk(tree):
  if hasattr(node,'type_params'):
   assert not node.type_params
   del node.type_params
 return ast.dump(tree,indent=2,show_empty=True)+'\n'
for number,r in zip((37,38),manifest['baselines']):
 before=(ROOT/r['path']).read_text()
 assert (PUB/f'BUILDER_FROM{number}_PATCH01.diff').read_text()==''.join(difflib.unified_diff(before.splitlines(True),candidate.splitlines(True),fromfile=r['path'],tofile='full39/build_public01.py'))
 assert (PUB/f'BUILDER_FROM{number}_INVERSE01.diff').read_text()==''.join(difflib.unified_diff(candidate.splitlines(True),before.splitlines(True),fromfile='full39/build_public01.py',tofile=r['path']))
 a=legacy_dump(before);b=legacy_dump(candidate)
 assert (PUB/f'BUILDER_AST_FROM{number}_PATCH01.diff').read_text().rstrip('\n')==''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=f'baseline{number}.ast',tofile='candidate39.ast')).rstrip('\n')
 assert (PUB/f'BUILDER_AST_FROM{number}_INVERSE01.diff').read_text().rstrip('\n')==''.join(difflib.unified_diff(b.splitlines(True),a.splitlines(True),fromfile='candidate39.ast',tofile=f'baseline{number}.ast')).rstrip('\n')
mcm38=load(P38/'public01/mcm_policy.json');full=copy.deepcopy(mcm38);removed=full.pop('entry_qualification')
assert full==load(F/'pilot-efficiency-integration-2026-10-11/SUCCESSOR_MCM_DRAFT01.json')==load(F/'real-data-pilot-full37-binding-preparation01-2026-10-11/public01/mcm_policy.json')
assert full['batched']['continuation']['manifest_input'] is None and full['batched']['continuation']['graph_manifest_inputs']=={}
typed=load(P38/'public01/typed_payload.json');assert len(typed['graphs'])==7 and sum(v['rows']*32 for v in typed['graphs'].values())==415968128
assert len(load(P38/'public01/pair_policy.json')['numerical_source']['files'])==205
tree=ast.parse(candidate);constants={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('ACCEPTED38_PINS','NAME','BINDER_SHA')}
assert constants['NAME']==NAME and constants['BINDER_SHA']=='bcca66a6c7daba762a629dff84b9f16e48e7b9c2ffe51f77511942816ee444cb'
for path,digest in constants['ACCEPTED38_PINS'].items():assert pin(P38/path)['sha256']==digest
# Candidate helper is pure metadata; use synthetic documents inside this owned directory.
helper=runpy.run_path(str(PUB/'join_entry_draft01.py'))['joined_draft']
fixture=HERE/'synthetic_inputs';fixture.mkdir()
inputs=copy.deepcopy(load(P38/'ALL_INPUT_REFS01.json'))
docs={role:load(ROOT/inputs[role]['path']) for role in ('execution_job','pilot','mcm_policy','typed_payload','compact_policy','mcm_output_policy')}
docs['mcm_policy']=full;docs['pilot']['cell_id']=CELL
docs['execution_job']['resources']['storage_budget']['experiment']=NAME
docs['execution_job']['resources']['storage_budget']['roots'][1]=str(ROOT/'research_runs'/NAME)
def save(role,value,suffix=''):
 p=fixture/(role+suffix+'.json');p.write_text(json.dumps(value,sort_keys=True)+'\n');return pin(p)
for role,doc in docs.items():inputs[role]={'dataset':'eth',**save(role,doc)}
inherited=load(F/'real-data-pilot-full36-entry-preparation01-2026-10-11/CORE_MANIFEST01.json')
draft=helper(ROOT,inputs,inherited,PUB/'build_public01.py')
assert draft['experiment_cells']==[CELL] and draft['core_manifest']['builder_sha256']==manifest['builder']['sha256']
assert all(draft[k] is None for k in ('prior38_outcome','prior38_recovery','prior38_component_qualification','current_whole39_capacity','final_release'))
assert not draft['claim'] and not draft['execution']
for role,r in draft['core_manifest']['inputs'].items():assert r=={k:inputs[role][k] for k in ('path','sha256','bytes')}
rejected=[]
for role,key,value in [('pilot','cell_id','real-eth-first-graph-entry-preparation-resource38'),('mcm_policy','entry_qualification',removed)]:
 doc=copy.deepcopy(docs[role]);doc[key]=value;bad=copy.deepcopy(inputs);bad[role]={'dataset':'eth',**save(role,doc,'_rejected_'+key)}
 try:helper(ROOT,bad,inherited,PUB/'build_public01.py')
 except AssertionError:rejected.append(key)
 else:raise AssertionError('bad metadata accepted')
ns=runpy.run_path(str(CAP/'capacity.py'));project=ns['project'];metadata=load(CAP/'WHOLE_METADATA01.json');obs=load(CAP/'DATED_OBSERVATION01.json');terms=load(CAP/'CONDITIONAL_TERMS01.json')
actual=project(metadata,obs,terms,conditional=True);assert actual==load(CAP/'CONDITIONAL_PROJECTION01.json')
counts=[];total_transport=0
def padded(n,unit):return -(-n//unit)*unit
def group_extent(lengths):return padded(sum(512+padded(n,512) for n in lengths)+1024,10240)
for graph,v in sorted(metadata['graphs'].items()):
 cells=32*v['nodes'];batches=-(-cells//4096);groups=-(-batches//16);before_groups=(batches-1)//16
 expected={}
 for cap in (1024,4096):
  one=group_extent([cap,92+53*4096,cap]*16)
  last_n=batches-before_groups*16;last_cells=cells-(batches-1)*4096
  final=group_extent([cap,92+53*4096,cap]*(last_n-1)+[cap,92+53*last_cells,cap])
  expected[cap]=before_groups*one+final
 assert expected[4096]==v['bundle_preserved_bytes'] and 2*expected[4096]==v['bundle_recovered_bytes']
 total_transport+=4*(expected[4096]-expected[1024]);counts.append({'graph':graph,'cells':cells,'batches':batches,'groups':groups})
assert [sum(x[k] for x in counts) for k in ('cells','batches','groups')]==[415968128,101559,6352]
assert total_transport==actual['cumulative_transport_addition_not_retained']==2599854080
assert actual['continuation_addition']=={'logical_file_bytes':416083968,'allocated_bytes':416083968,'entries':101559}
assert actual['projection']=={'logical_file_bytes':16987939107,'allocated_bytes':19130094173,'entries':871315}
assert actual['storage_caps_and_floor_pass'] is False and actual['memory_fit_proven'] is False and actual['physical_reservation'] is False
try:project(metadata,obs,terms)
except ValueError as e:dated_refusal=str(e)
else:raise AssertionError('dated observation accepted')
# A synthetic final scalar observation proves only arithmetic/refusal behavior.
final=copy.deepcopy(obs);final.update(kind='final-post38-whole39-writable-union',post38_closed_and_recovered=True,source_and_scope_current=True,filesystem_block_bytes=4096,filesystem_identity='synthetic-only',free_inodes=2000000,observation_sha256='synthetic-only')
finalterms=copy.deepcopy(terms);finalterms.update(review_status='root-current-full-growth',observation_sha256='synthetic-only')
base=project(metadata,final,finalterms)
for domain in ('runtime_temp_cache','training_and_lifecycle'):
 changed=copy.deepcopy(final);changed['storage_observation']['logical_file_bytes']+=1234;changed['storage_observation']['allocated_bytes']+=4096
 changed['storage_observation']['residual_domains'][domain]['logical_file_bytes']+=1234;changed['storage_observation']['residual_domains'][domain]['allocated_bytes']+=4096
 assert project(metadata,changed,finalterms)['projection']==base['projection']
for key,value in [('free_inodes',None),('filesystem_block_bytes',None),('post38_closed_and_recovered',False),('source_and_scope_current',False)]:
 changed=copy.deepcopy(final);changed[key]=value
 try:project(metadata,changed,finalterms)
 except ValueError:rejected.append(key)
 else:raise AssertionError('missing final term accepted')
low=copy.deepcopy(final);low['free_inodes']=base['growth']['entries']-1
assert project(metadata,low,finalterms)['storage_caps_and_floor_pass'] is False
assert all(value is None for key,value in load(CAP/'FINAL_TERMS_TEMPLATE.json').items() if key in ('review_status','observation_sha256','directory_allocated_bytes','other_new_entries'))
result={'decision':'accepted-source-and-scalar-controls-only','builder_not_executed':True,'binder_not_executed':True,'public_source_count':205,'whole_cardinality':counts,'accepted38_removed_only_mcm_field':'entry_qualification','fresh_prefix':True,'helper_actual_core_and_cell_join':True,'negative_controls':rejected,'dated_final_mode_refusal':dated_refusal,'dated_projection':actual['projection'],'dated_margins':actual['margins'],'continuation_retained_addition':actual['continuation_addition'],'cumulative_transport_addition_not_retained':total_transport,'residual_subset_rebase_invariant':True,'memory_or_physical_reservation_proven':False,'snapshot':[pin(p) for directory in (PUB,CAP) for p in sorted(directory.iterdir()) if p.is_file()]}
print(json.dumps(result,indent=2,sort_keys=True))
