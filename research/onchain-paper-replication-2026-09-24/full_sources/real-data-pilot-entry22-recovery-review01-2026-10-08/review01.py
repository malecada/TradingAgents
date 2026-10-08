import hashlib,json,os,subprocess,tarfile
from pathlib import Path
H=Path(__file__).resolve().parent;R=Path.cwd();D=H.parent/'real-data-pilot-entry22-increment01-2026-10-08';f=D/'FRESH_GIT_RECOVERY01.json';r=json.loads(f.read_text());checks=[]
def ck(n,v):
 assert v,n
 checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0');env.pop('GIT_ALTERNATE_OBJECT_DIRECTORIES',None)
def git(repo,*args):return subprocess.run(['git','-C',str(repo),*args],env=env,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout
bare=Path(r['fresh_bare']);source=r['source'];ck('exact_source',source=='2dd66342827ddc5bb6ebb04933224735ebe230cc'==r['actual_remote_head']==r['actual_fetch_head']);ck('no_alternates',not (bare/'objects/info/alternates').exists())
ops=json.loads((D/'GIT_OPERATIONS01.json').read_text());ck('all13actualexits',len(ops)==13 and ops==r['operations'] and all(x['exit_code']==0 for x in ops))
for o in ops:
 for kind in ('stdout','stderr'):
  raw=(D/(o['operation']+'.'+kind)).read_bytes();ck(o['operation']+'_'+kind,len(raw)==o[kind+'_bytes'] and sha(raw)==o[kind+'_sha256'])
ck('recorded_remote_head',(D/'remote_actual_branch_readback.stdout').read_text().split()[0]==source)
ck('external_remote_config',git(bare,'remote','get-url','origin').decode().strip()==r['actual_external_source'])
ck('fetch_head',git(bare,'rev-parse','FETCH_HEAD').decode().strip()==source)
commit=git(bare,'cat-file','commit',source);ck('commit_body',sha(commit)==r['commit_body_sha256'] and commit==(D/'actual_external_commit_body.stdout').read_bytes() and commit==git(R,'cat-file','commit',source))
blob=r['archive_git_blob_oid'];returned=R/r['returned_archive']['path'];body=returned.read_bytes();ck('returned_archive',len(body)==1669120==r['returned_archive']['bytes'] and sha(body)==r['returned_archive']['sha256']=='950307478390fecf06a922232e161f4f4817697a63166f74d6e36ea9976cc31b')
ck('actual_fetched_blob',git(bare,'cat-file','blob',blob)==body);ck('blob_oid',hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==blob)
capraw=(R/r['capture']['path']).read_bytes();ck('capture_pin',sha(capraw)==r['capture']['sha256']);cap=json.loads(capraw)
ck('local_committed_tree_binding',git(R,'ls-tree',source,'--',cap['archive']['path']).decode().strip()==r['local_commit_tree_join'].replace('\\t','\t'))
sraw=(R/cap['selection']['path']).read_bytes();ck('original_selection_pin',sha(sraw)==cap['selection']['sha256']);s=json.loads(sraw);rows={x['path']:x for x in s['rows']+s['directories']}
with tarfile.open(returned,'r:') as tar:
 members=tar.getmembers();ck('exact52members',len(members)==52 and len({x.name for x in members})==52 and {x.name for x in members}==set(rows))
 for m in members:
  x=rows[m.name];assert m.mode==int(x['mode'],8)
  if x['type']=='directory':assert m.isdir()
  else:
   assert m.isfile();raw=tar.extractfile(m).read();assert len(raw)==m.size==x['bytes'] and sha(raw)==x['sha256']
checks.append('all52opaque_regular_bodies_exact_modes')

N=H.parent/'real-data-pilot-final22-2026-10-08';release=json.loads((N/'RELEASE_REVIEW01.json').read_text());scope=json.loads((D/'SELECTION_DRAFT01.json').read_text());old=json.loads((R/scope['prior_release']['path']).read_text());binding=json.loads((N/'BINDING01.json').read_text());gate=json.loads((N/'gate01.json').read_text());exp=gate['experiments'][release['identity']]
ck('release_pin',sha((N/'RELEASE_REVIEW01.json').read_bytes())==scope['current_release']['sha256']=='c5e3f19d505797b8d1e68cf0f43b467bdb7b7fbf5e7645e14f282e91ceba06a1')
ck('prior_release_pin',sha((R/scope['prior_release']['path']).read_bytes())==scope['prior_release']['sha256'])
ck('selection_scope_exact',{k:v['sha256'] for k,v in rows.items()}==scope['selection'])
for name,pin in scope['inherited'].items():ck('inherited_'+name,old['evidence'].get(name)==release['evidence'].get(name)==pin)
for name,pin in exp['source_files'].items():ck('source_'+name,release['evidence'][name]==pin and (rows.get(name,{}).get('sha256')==pin or old['evidence'].get(name)==pin))
for role,ref in exp['inputs'].items():
 name=ref['path'];pin=ref['sha256'];ck('input_'+role,release['evidence'][name]==pin)
 if role!='archive_transport':ck('public_input_'+role,rows.get(name,{}).get('sha256')==pin or old['evidence'].get(name)==pin)
 else:ck('sole_private_hash_only',scope['private_excluded']=={'path':name,'sha256':pin} and name not in rows)
ck('counts345_60',len(exp['source_files'])==345 and len(exp['inputs'])==60)
for name in ('gate01.json','preflight01.py','root_io.py','BINDING01.json','RELEASE_REVIEW01.json'):ck('entry_'+name,str((N/name).relative_to(R)) in rows)
ck('binding_exact',sha((N/'BINDING01.json').read_bytes())==release['final_binding_sha256'])
for v in binding.values():
 if isinstance(v,dict) and set(v)>={'path','sha256'}:ck('binding_ref_'+v['path'],release['evidence'].get(v['path'])==v['sha256'])
ck('no_private_runtime_return',not any(k.startswith('research_artifacts/real_pilot_runtime/') for k in rows))
x={'decision':'accepted','status':'EXACT_ENTRY22_PUBLIC_INCREMENT_RECOVERED','identity':release['identity'],'source':source,'source_count':345,'input_count':60,'files':52,'regular_bytes':1574907,'inherited_identical_refs':469,'returned_archive':r['returned_archive'],'checks':checks,'receipt_sha256':sha(f.read_bytes()),'release_sha256':scope['current_release']['sha256'],'offline_git_no_lazy_fetch':True,'scope_review_sha256':sha((H/'SCOPE_REVIEW01.json').read_bytes()),'qualification':'Actual13operation receipts and offline freshbare commit/blob/tree binding verified; exact52returned typed/mode/body members.345sources/60inputs covered by newly returned bodies or exact accepted21 inherited hashes; sole private reference remains hash-only. No whole-tree/private/runtime/scientific-store/POSIX/deletion/capacity or numerical proof; no source/release suite repeated.'}
(H/'RECOVERY_REVIEW01.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps({'decision':x['decision'],'checks':len(checks),'sha256':sha((H/'RECOVERY_REVIEW01.json').read_bytes())}))
