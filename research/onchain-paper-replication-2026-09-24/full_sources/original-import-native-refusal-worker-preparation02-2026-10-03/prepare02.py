"""Source-only successor composition and sentinel templates, no admission."""
import ast,copy,difflib,hashlib,importlib.util,json,pathlib,sys
D=pathlib.Path(__file__).resolve().parent;ROOT=D.parents[3];OLD=D.parent/'original-import-native-refusal-worker-preparation01-2026-10-03'
def ref(p):
 raw=p.read_bytes();return {'path':str(p.relative_to(ROOT)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(name,value):(D/name).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
old=json.loads((OLD/'source_inventory01.json').read_text());rows={r['target']:copy.deepcopy(r) for r in old['source_inventory']};oldrow=copy.deepcopy(rows['fixture_tools/refusal_outer01.py']);v=ref(D/'refusal_outer01.py');rows['fixture_tools/refusal_outer01.py'].update(origin=v['path'],bytes=v['bytes'],sha256=v['sha256'],git_commit=None,git_path=None)
for row in rows.values():
 v=ref(ROOT/row['origin']);assert v['sha256']==row['sha256'] and v['bytes']==row['bytes']
inv=copy.deepcopy(old);inv.update(source_inventory=sorted(rows.values(),key=lambda r:r['target']),source_logical_bytes=sum(r['bytes'] for r in rows.values()),base_inventory=ref(OLD/'source_inventory01.json'),status='source-only-R1-correction-unreviewed-not-admitted',final_overlay_git_commit=None)
write('source_inventory02.json',inv);write('install-delta02.json',{'base_inventory':ref(OLD/'source_inventory01.json'),'changed_targets':[{'before':oldrow,'after':rows['fixture_tools/refusal_outer01.py']}],'unchanged_targets':168,'package_count':144,'source_count':169,'copied_unchanged_snapshots':{n:ref(D/n) for n in ('resource_refusal.py','refusal_preclaim01.py','refusal_native01.py','refusal_oracle_evidence01.py','templates01.py')}})
(D/'refusal_outer01.py.patch').write_text(''.join(difflib.unified_diff((OLD/'refusal_outer01.py').read_text().splitlines(True),(D/'refusal_outer01.py').read_text().splitlines(True),fromfile=str((OLD/'refusal_outer01.py').relative_to(ROOT)),tofile=str((D/'refusal_outer01.py').relative_to(ROOT)))))
sys.path.insert(0,str(D));import test_adapter01
base=D.parent/'original-import-native-refusal-candidate05-2026-10-03';spec=importlib.util.spec_from_file_location('source_only_templates02',base/'test_inputs05.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);basic,_,_,_=mod.render();sources={k:r['sha256'] for k,r in rows.items()};primary,_=mod.generator.registration(rendered={'success':basic,'second_target_publication_failure':basic},source_files=sources,runtime_hashes={'qualified_only':'a'*64})
import templates01
value=templates01.prepare(basic,primary,source_files=sources,runtime_hashes={'qualified_only':'a'*64},imported_identity_source=(ROOT/rows['tradingagents/research/onchain_replication/imported_mcm_identity.py']['origin']).read_bytes(),runtime={'qualified_only':True},native_environment={'qualified_only':True},capsule='/qualified-unregistered-synthetic',source_commit='a'*40)
assert value['protocol']==json.loads((OLD/'PROTOCOL01.json').read_text())
write('PROTOCOL02.json',value['protocol']);write('qualified-release-draft02.json',value['release']);write('qualified-registration-draft02.json',value['registration']);write('generated-input-index02.json',{'qualification':'Sentinel a*40 / qualified non-runtime environment. Unregistered source-only template metadata; no body files or actual capsule.','cases':{n:{'identity':v['identity'],'inputs':v['inputs'],'generated_body_hashes':{k:hashlib.sha256(b).hexdigest() for k,b in v['files'].items()}} for n,v in value['rendered'].items()}})
assert len(rows)==169 and sum(k.startswith('tradingagents/') for k in rows)==144
assert not any(n.split('.')[0] in ('numpy','torch','scipy','tradingagents') for n in sys.modules)
print('169 source entries;144 package;one changed outer body;27 exact sentinel templates;protocol unchanged;no numeric/package imports/jobs/claims.')
