from pathlib import Path
import json,hashlib,subprocess,platform,sys,importlib.metadata,stat
R=Path.cwd();F=Path('research/onchain-paper-replication-2026-09-24/full_sources');D=F/'original-import-fixture-native-preparation-2026-10-03';IO=F/'original-import-fixture-io-candidate05-2026-10-03';H=lambda b:hashlib.sha256(b).hexdigest();h=lambda p:H(p.read_bytes());base='3a56c4b28c1d05595c765cd93046496104c7ecb2'
paths=sorted(['tradingagents/__init__.py']+[str(p) for p in Path('tradingagents/research').glob('*.py')]+[str(p) for p in Path('tradingagents/research/onchain_replication').glob('*.py')]);assert len(paths)==134
rows={}
for name in paths+['uv.lock','pyproject.toml','.python-version']:
 raw=Path(name).read_bytes();old=subprocess.check_output(['git','show',base+':'+name]);assert raw==old,name
 rows[name]={'target':name,'origin':name,'sha256':H(raw),'bytes':len(raw),'git_commit':base,'git_path':name}
m=json.loads((IO/'manifest01.json').read_text())
for row in m['install_map']:
 p=Path(row['candidate']);assert h(p)==row['sha256'];name=row['target'];rows[name]={'target':name,'origin':str(p),'sha256':h(p),'bytes':p.stat().st_size,'git_commit':None,'git_path':None}
external=json.loads((F/'original-import-fixture-io-candidate04-2026-10-02/manifest01.json').read_text())['external_unchanged_source'];p=Path(external['path']);assert h(p)==external['sha256'];rows[str(p)]={'target':str(p),'origin':str(p),'sha256':h(p),'bytes':p.stat().st_size,'git_commit':base,'git_path':str(p)}
for name in ('resources','job','resource_fixture'):
 p=D/(name+'.py');target='tradingagents/research/onchain_replication/'+p.name;rows[target]={'target':target,'origin':str(p),'sha256':h(p),'bytes':p.stat().st_size,'git_commit':None,'git_path':None}
required=sorted(x for x in rows if x=='tradingagents/__init__.py' or x.startswith('tradingagents/research/') and x.endswith('.py'));assert len(required)==142
(D/'source_inventory01.json').write_text(json.dumps({'baseline_commit':base,'original_package_count':134,'composed_package_count':142,'source_inventory':list(rows.values()),'required_package_sources':required,'source_logical_bytes':sum(r['bytes'] for r in rows.values()),'conditional_io_manifest':{'path':str(IO/'manifest01.json'),'sha256':h(IO/'manifest01.json')},'new_native_overlay_review':'pending','final_overlay_git_commit':None},indent=2,sort_keys=True)+'\n')
e=json.loads((F/'original-dictionary-bridge-investigation-2026-10-02/evidence01.json').read_text());join=json.loads((F/'original-dictionary-bridge-investigation-2026-10-02/graph-join01.json').read_text());refs={p:v for p,v in e['refs'].items() if not p.startswith('tradingagents/')};refs[join['intent_path']]={'sha256':join['intent_sha256'],'bytes':Path(join['intent_path']).stat().st_size};assert len(refs)==11
original=[]
for name,info in refs.items():
 p=Path(name);st=p.lstat();assert stat.S_ISREG(st.st_mode) and st.st_size==info['bytes'] and st.st_size<2*1024**2 and h(p)==info['sha256'];original.append({'original_path':str(R/p),'origin':name,**info,'capsule_path':'fixture_inputs/original/'+str(len(original)).zfill(2)+'-'+p.name})
(D/'original_inputs01.json').write_text(json.dumps({'original_claim':'eth-paper-resource-pilot-20260924-02','original_source':'c6b568d4b1c177ab94ac37fbad462c2decc721c0','parent_terminal':'failed','dictionary_component':'complete','dictionary_identity':'48832eeb9774ef6ca13915364c17d1ac89f5c67165636de5811ebf82ad6ad726','inputs':original,'bytes':sum(x['bytes'] for x in original),'original_source_files':e['original_sources'],'body_array_reads':False},indent=2,sort_keys=True)+'\n')
commit='c6b568d4b1c177ab94ac37fbad462c2decc721c0';objects={commit:'commit'}
for name in e['original_sources']:
 components=Path(name).parts
 for k in range(len(components)+1):
  ref=commit+(':'+('/'.join(components[:k])) if k else '^{tree}')
  oid=subprocess.check_output(['git','rev-parse',ref],text=True).strip();objects[oid]='blob' if k==len(components) else 'tree'
objectsrows=[]
for oid,kind in sorted(objects.items()):
 size=int(subprocess.check_output(['git','cat-file','-s',oid]));assert size<=4*1024**2
 raw=subprocess.check_output(['git','cat-file',kind,oid]);assert len(raw)==size
 objectsrows.append({'oid':oid,'type':kind,'bytes':size,'body_sha256':H(raw)})
(D/'original_git_objects01.json').write_text(json.dumps({'original_commit':commit,'objects':objectsrows,'bytes':sum(x['bytes'] for x in objectsrows),'materialized':False,'future_import':'git hash-object -w -t TYPE --stdin for each validated body; exact returned oid required; root commits only new executing source separately','missing_parent_history':'not needed for exact original commit:path body lookup; no history completeness claim'},indent=2,sort_keys=True)+'\n')
dists=[]
for dist in importlib.metadata.distributions():
 files=dist.files or [];record=next((dist.locate_file(p) for p in files if str(p).endswith('.dist-info/RECORD')),None)
 dists.append({'name':dist.metadata['Name'],'version':dist.version,'record':None if record is None else str(record),'record_sha256':None if record is None else h(record)})
exe=Path(sys.executable).resolve();assert exe.stat().st_size<32*1024**2
(D/'runtime01.json').write_text(json.dumps({'python':platform.python_version(),'executable':sys.executable,'resolved_executable':str(exe),'executable_bytes':exe.stat().st_size,'executable_sha256':h(exe),'prefix':sys.prefix,'lock_sha256':h(Path('uv.lock')),'distribution_records':sorted(dists,key=lambda x:x['name'] or ''),'selection':'shared locked runtime, capsule cwd/PYTHONPATH; no symlink venv or wrong-root research_runtime.py check','required_origin_check':'all loaded tradingagents module __file__ must fall under capsule; numerical dependencies must remain under pinned shared .venv; capture sys.path and verify before actual Binding','numerical_imports':False,'environment_input':'Root must bind exact inventory(include_torch=True) from accepted runtime receipt, reverified inside guard before materialization'},indent=2,sort_keys=True)+'\n')
print('source files',len(rows),'package',len(required),'logicalbytes',sum(r['bytes'] for r in rows.values()),'originalinputbytes',sum(x['bytes'] for x in original),'originalobjects',len(objectsrows),sum(x['bytes'] for x in objectsrows))
