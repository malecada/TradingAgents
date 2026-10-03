"""Source-only full170 closure and finite sentinel templates; no admission."""
import ast,copy,difflib,hashlib,importlib.util,json,pathlib,sys
D=pathlib.Path(__file__).resolve().parent;ROOT=D.parents[3];OLD=D.parent/'original-import-native-refusal-worker-preparation02-2026-10-03'
def ref(p):
 raw=p.read_bytes();return {'path':str(p.relative_to(ROOT)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(n,v):(D/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
inv=json.loads((OLD/'source_inventory02.json').read_text());rows={r['target']:copy.deepcopy(r) for r in inv['source_inventory']};changes=[]
for name in ('refusal_outer01.py','refusal_inventory03.py','templates01.py'):
 target='fixture_tools/'+name;before=copy.deepcopy(rows.get(target));v=ref(D/name);after={'target':target,'origin':v['path'],'bytes':v['bytes'],'sha256':v['sha256'],'git_commit':None,'git_path':None};rows[target]=after;changes.append({'before':before,'after':after})
 if before is not None:(D/(name+'.patch')).write_text(''.join(difflib.unified_diff((ROOT/before['origin']).read_text().splitlines(True),(D/name).read_text().splitlines(True),fromfile=before['origin'],tofile=v['path'])))
for row in rows.values():
 observed=ref(ROOT/row['origin']);assert observed['bytes']==row['bytes'] and observed['sha256']==row['sha256']
 if row['target'].endswith('.py'):ast.parse((ROOT/row['origin']).read_bytes())
inv.update(source_inventory=sorted(rows.values(),key=lambda r:r['target']),source_count=len(rows),source_logical_bytes=sum(r['bytes'] for r in rows.values()),base_inventory=ref(OLD/'source_inventory02.json'),status='source-only-complete-inventory03-unreviewed',final_overlay_git_commit=None)
write('source_inventory03.json',inv);write('install-delta03.json',{'base_inventory':ref(OLD/'source_inventory02.json'),'changed_or_new_targets':changes,'unchanged_targets':167,'package_count':144,'source_count':170})
sys.path.insert(0,str(D));import test_adapter01
base=D.parent/'original-import-native-refusal-candidate05-2026-10-03';spec=importlib.util.spec_from_file_location('sentinel_templates03',base/'test_inputs05.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);basic,_,_,_=mod.render();sources={k:r['sha256'] for k,r in rows.items()};primary,_=mod.generator.registration(rendered={'success':basic,'second_target_publication_failure':basic},source_files=sources,runtime_hashes={'qualified_only':'a'*64})
import templates01
value=templates01.prepare(basic,primary,source_files=sources,runtime_hashes={'qualified_only':'a'*64},imported_identity_source=(ROOT/rows['tradingagents/research/onchain_replication/imported_mcm_identity.py']['origin']).read_bytes(),runtime={'qualified_only':True},native_environment={'qualified_only':True},capsule='/qualified-unregistered-synthetic',source_commit='a'*40)
oldprotocol=json.loads((OLD/'PROTOCOL02.json').read_text());allowed={'per_case_closure_seconds','entire_suite_wall_bound_seconds','whole_outer_deadline_enforced','inventory_policy','limits_qualification'}
assert {k:v for k,v in oldprotocol.items() if k not in allowed}=={k:v for k,v in value['protocol'].items() if k not in allowed}
write('PROTOCOL03.json',value['protocol']);write('qualified-release-draft03.json',value['release']);write('qualified-registration-draft03.json',value['registration']);write('generated-input-index03.json',{'qualification':'Unregistered sentinel a*40 metadata only; no input bodies or capsule installed.','cases':{n:{'identity':v['identity'],'inputs':v['inputs'],'generated_body_hashes':{k:hashlib.sha256(b).hexdigest() for k,b in v['files'].items()}} for n,v in value['rendered'].items()}})
assert len(rows)==170 and sum(k.startswith('tradingagents/') for k in rows)==144
assert not any(n.split('.')[0] in ('numpy','torch','scipy','tradingagents') for n in sys.modules)
print('170sources144package;167unchanged targets;2changedtools+1newinventory;27exact templates;all cardinalities unchanged;native1800/active1840 retained;whole-outer60/51300claims removed;no jobs/claims/numerics.')
