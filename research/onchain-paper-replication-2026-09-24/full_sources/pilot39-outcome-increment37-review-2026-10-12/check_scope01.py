from pathlib import Path
import ast,json,hashlib,stat,os
F=Path('research/onchain-paper-replication-2026-09-24/full_sources');D=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/full39outcome37';S=json.loads((D/'TOOL_SCOPE01.json').read_text());h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();e={}
assert len(S['selected_pins'])==305 and len(S['baseline_pins'])==4 and len(S['closed_directory_roster'])==21
names=set();total=0
for row in S['selected_pins']+S['baseline_pins']:
 p=Path(row['path']);assert not set(p.parts)&{'.git','.venv','node_modules','keys','apis'} and p.name not in {'.env','hf_token.txt','connection.json'}
 st=p.lstat();assert stat.S_ISREG(st.st_mode) and not p.is_symlink() and p.parent.resolve()==Path.cwd()/p.parent and st.st_size==row['bytes']<=4*1024**2 and format(stat.S_IMODE(st.st_mode),'04o')==row['mode'] and h(p)==row['sha256'],str(p)
 e[str(p)]=row['sha256']
 if row in S['selected_pins']:assert str(p) not in names;names.add(str(p));total+=st.st_size
assert total==9864283
roster={r['path']:r for r in S['closed_directory_roster']}
for path,row in roster.items():
 p=Path(path);st=p.lstat();assert stat.S_ISDIR(st.st_mode) and not p.is_symlink() and p.resolve()==Path.cwd()/p and format(stat.S_IMODE(st.st_mode),'04o')==row['mode'] and sorted(x.name for x in p.iterdir())==row['children']
 for name in row['children']:assert str(p/name) in names|set(roster),str(p/name)
assert len(S['closed_scopes'])==6 and all(x in roster for x in S['closed_scopes'])
for root in S['closed_scopes']:
 assert any(p.startswith(root+'/') for p in names)
prior=json.loads(Path(S['baseline_pins'][0]['path']).read_bytes());capture=json.loads(Path(S['baseline_pins'][2]['path']).read_bytes());review=json.loads(Path(S['baseline_pins'][1]['path']).read_bytes())
assert prior['capture']['sha256']==S['baseline_pins'][2]['sha256'] and capture['selection']['sha256']==S['baseline_pins'][3]['sha256'];assert review['decision'].startswith('accepted')
t=ast.parse((D/'select37.py').read_text());data={n.targets[0].id:ast.literal_eval(n.value) for n in t.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ['selected_pins','baseline_pins','closed_directory_roster','helper_names','reused_pins']}
assert data['selected_pins']==S['selected_pins'] and data['baseline_pins']==S['baseline_pins'] and data['closed_directory_roster']==S['closed_directory_roster'] and data['reused_pins']==[] and len(data['helper_names'])==9
assert not (D/'SELECTION37.json').exists() and not (D/'CAPTURE37.json').exists() and not (D/'FRESH_GIT_RECOVERY37.json').exists()
print(json.dumps({'status':'PASS','selected_files':len(names),'selected_bytes':total,'max_bytes':max(x['bytes'] for x in S['selected_pins']),'closed_directories':len(roster),'closed_scopes':S['closed_scopes'],'baseline_joins':'PASS','source_pins':e,'qualification':'Read-only finite hashes/modes/child names; opaque bodies hashed only; no helpers executed or scientific authority.'},indent=2))
