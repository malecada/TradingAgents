"""Bounded concrete binding/capacity source checks; no launch or admission."""
import ast, copy, datetime, difflib, hashlib, json, os, pathlib, stat, subprocess
ROOT=pathlib.Path(__file__).resolve().parents[4];F=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'
OUT=pathlib.Path(__file__).resolve().parent;E=F/'real-data-pilot-full36-entry-preparation01-2026-10-11';OLD=F/'real-data-pilot-full35-entry-preparation01-2026-10-11';B=F/'real-data-pilot-full36-binding-preparation01-2026-10-11'
ANCHOR='f450f11cc44f5287d0daf1bcfcaea469d9347613';GATE_COMMIT='6165f6ff855e2b7f73c574f98e68e23942824c24';NAME='eth-paper-real-data-end-to-end-resource-20261011-36'
sha=lambda b:hashlib.sha256(b).hexdigest();load=lambda p:json.loads(p.read_bytes())
def ref(p):
    b=p.read_bytes();return dict(path=str(p.relative_to(ROOT)),sha256=sha(b),bytes=len(b))
def bound(r):
    p=ROOT/r['path'];assert p.resolve()==p and not p.is_symlink();b=p.read_bytes();assert sha(b)==r['sha256'];return b
def save(n,v):
    with (OUT/n).open('x') as h:json.dump(v,h,indent=2,sort_keys=True);h.write('\n')
source_map=load(E/'CAPACITY_SOURCE_MAP01.json');pins=source_map['source_files'];assert len(pins)==428
original=load(OLD/'CAPACITY_SOURCE_MAP01.json')['source_files']
assert sorted(set(pins)-set(original))==source_map['added_sources'] and len(source_map['added_sources'])==5
assert [{'path':p,'old':original[p],'new':pins[p]} for p in sorted(original) if original[p]!=pins[p]]==source_map['changed_source'] and len(source_map['changed_source'])==17
queries=''.join(ANCHOR+':'+p+'\n' for p in pins);result=subprocess.check_output(['git','cat-file','--batch'],input=queries.encode(),cwd=ROOT);offset=0
for p,digest in pins.items():
    end=result.index(b'\n',offset);oid,kind,size=result[offset:end].split();offset=end+1;b=result[offset:offset+int(size)];offset+=int(size)
    assert kind==b'blob' and result[offset:offset+1]==b'\n' and sha(b)==digest and b==(ROOT/p).read_bytes();offset+=1
assert offset==len(result)
gate_bytes=subprocess.check_output(['git','show',GATE_COMMIT+':'+str((E/'gate01.json').relative_to(ROOT))],cwd=ROOT);gate=json.loads(gate_bytes);previous=load(OLD/'gate01.json')
assert set(gate['experiments'])==set(previous['experiments'])|{NAME}
assert all(gate['experiments'][k]==v for k,v in previous['experiments'].items())
experiment=gate['experiments'][NAME];assert experiment['parent']==NAME[:-2]+'35' and len(experiment['inputs'])==73 and len(set(experiment['outputs']))==9
assert all(experiment['source_files'][p]==digest for p,digest in pins.items())
binding=load(E/'BINDING_DRAFT01.json');actual={k:{f:v[f] for f in ('path','sha256')} for k,v in experiment['inputs'].items()};assert actual==binding['input_refs']
original_bound=load(B/'ALL_INPUT_REFS01.json');changed=[k for k in actual if any(actual[k][f]!=original_bound[k][f] for f in ('path','sha256'))];assert changed==['matching_ordered_edge_scratch']
for role,r in actual.items():
    if role!='archive_transport':bound(r)
for r in load(E/'CORE_MANIFEST01.json')['inputs'].values():bound(r)
for k,h in experiment['runtime_hashes'].items():assert sha((ROOT/'tradingagents/research'/k).read_bytes())==h
scratch=json.loads(bound(actual['matching_ordered_edge_scratch']));assert scratch['installed_source']['sha256']==pins[scratch['installed_source']['path']]
assert scratch['experiment']==NAME and scratch['incremental_explicit_numeric_scratch_bytes']==262144

# Compile only selected existing pure helpers; no imported job/runtime/transport modules.
pre=(OUT/'PRE_FIX_PREFLIGHT01.py').read_text();tree=ast.parse(pre)
names={'need','reference','read_path','read','validate_opaque','inverse_binding','projected','check'}
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
ns=dict(Path=pathlib.Path,ROOT=ROOT,HERE=E,NAME=NAME,GATE=str((E/'gate01.json').relative_to(ROOT)),json=json,copy=copy,hashlib=hashlib,os=os,stat=stat,OPAQUE_ROLE='archive_transport')
exec(compile(ast.Module(body=nodes,type_ignores=[]),'independent_selected_preflight_helpers','exec'),ns)
private=binding['transport'];assert actual['archive_transport']=={k:private[k] for k in ('path','sha256')}
ns['validate_opaque'](private)  # Descriptor/hash/mode only; never decode or print body.
prepared=json.loads(bound(binding['preparation']));unbound=json.loads(bound(binding['unbound_archive']));published=json.loads(bound(binding['transport_binding']))
canonical=lambda x:(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n').encode()
ns['inverse_binding'](prepared,unbound,published,private,canonical,sha)
for role,v in published['inputs'].items():assert json.loads(bound(actual[role]))==v
capacity=load(E/'CAPACITY_DECLARATION_ROOT01.json');prior_capacity=load(OLD/'CAPACITY_DECLARATION_ROOT01.json')
terms=('new_allocated_growth_bytes','new_entries','new_logical_growth_bytes','non_directory_new_allocated_growth_bytes','directory_allocated_bound_bytes','other_writer_reserved_bytes','additional_current_metadata_headroom')
assert all(capacity[k]==prior_capacity[k] for k in terms)
assert capacity['source_body_pins']==pins==load(E/'PUBLIC_MANIFEST01.json')['source_pins']
mcm=json.loads(bound(actual['mcm_policy']));assert capacity['entry_qualification_only']==mcm['entry_qualification'] and capacity['full_pilot_capacity_admitted'] is False
assert capacity['new_allocated_growth_bytes']==capacity['non_directory_new_allocated_growth_bytes']+capacity['directory_allocated_bound_bytes']+capacity['other_writer_reserved_bytes']
observation=load(E/'BASELINE_STORAGE_OBSERVATION01.json');join=load(E/'PREPARATION_ONLY_CAPACITY_JOIN01.json');limits=join['fixed_limits']
projection=ns['projected'](capacity,observation,limits)
assert join['projection']==dict(logical_file_bytes=projection['projected_logical_bytes'],allocated_bytes=projection['projected_allocated_bytes'],entries=projection['projected_entries'])
refused=[]
for metric,growth,limit in [('logical_file_bytes','new_logical_growth_bytes','max_logical_bytes'),('allocated_bytes','new_allocated_growth_bytes','max_allocated_bytes'),('entries','new_entries','max_entries')]:
    changed=copy.deepcopy(observation);changed[metric]=limits[limit]-capacity[growth]+1
    try:ns['projected'](capacity,changed,limits)
    except ValueError as error:assert limit in str(error);refused.append(limit)
    else:raise AssertionError('one-over capacity accepted')
# Existing absence and null binding-review controls stop without subprocess/admission.
assert not (E/'BINDING01.json').exists() and not (E/'RELEASE_REVIEW01.json').exists()
try:ns['check']()
except FileNotFoundError:pass
else:raise AssertionError('missing final binding accepted')
ns['read_path']=lambda p:json.dumps(binding).encode()
try:ns['check']()
except ValueError as error:assert str(error)=='actual bound reference required'
else:raise AssertionError('draft null final evidence accepted')
# Exact finite literal patch joins; changed lines are reviewed explicitly in the report.
before=(OLD/'preflight35_01.py').read_text();diff=''.join(difflib.unified_diff(before.splitlines(True),pre.splitlines(True),fromfile='full35/preflight35_01.py',tofile='full36/preflight36_01.py'))
assert diff==(E/'PREFLIGHT_LITERAL_PATCH01.diff').read_text()
rio=(E/'root_io36_01.py').read_text();oldrio=(OLD/'root_io35_01.py').read_text();assert rio==oldrio.replace('from preflight35_01 import check','from preflight36_01 import check')
assert ast.dump(ast.parse(rio.replace('from preflight36_01 import check','from preflight35_01 import check')))==ast.dump(ast.parse(oldrio))
save('CHECK01.json',dict(status='PASS_METADATA_WITH_P2_RECOVERY_GUARD_PENDING_FIX',source_anchor=ANCHOR,initial_gate_commit=GATE_COMMIT,initial_gate_sha256=sha(gate_bytes),source_bodies=428,changed_bodies=17,added_bodies=5,roles=73,outputs=9,old_gate_entries_unchanged=True,opaque_dispatch_hash_mode_stability_only=True,binder_inverse=True,core_runtime_scratch_joins=True,capacity_terms_unchanged=True,projection=projection,one_over_limits_refused=refused,missing_binding_refused=True,null_binding_review_refused=True,new_recovery_guard_defect_retained=True,final_source_release=False,capacity_only_for_36=True,full37_capacity=False))
print(json.dumps(dict(status='PASS_METADATA_EXCEPT_RETAINED_P2',sources=428,roles=73,projection=join['projection'],claim=False,native=False)))
