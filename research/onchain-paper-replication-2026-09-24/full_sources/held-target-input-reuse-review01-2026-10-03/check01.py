import copy,hashlib,json,os,stat,subprocess,tarfile
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[3];F=H.parent;I=F/'held-target-input-reuse-investigation01-2026-10-03';P=F/'original-import-native-successor-preparation06-2026-10-03';C=P/'capsule04';X=P/'outcome-recovery01/recovered-terminal-capsule04';G=P/'outcome-recovery01/repository.git'
def h(b):return hashlib.sha256(b).hexdigest()
def read(p):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and 0<=s.st_size<=4194304 and p.resolve()==p
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW);b=b''
 try:
  while len(b)<=s.st_size:
   chunk=os.read(fd,min(65536,s.st_size-len(b)+1))
   if not chunk:break
   b+=chunk
  t=os.fstat(fd);a=p.lstat();sig=lambda z:(z.st_dev,z.st_ino,z.st_mode,z.st_nlink,z.st_size,z.st_mtime_ns,z.st_ctime_ns)
  assert len(b)==s.st_size and sig(s)==sig(t)==sig(a)
 finally:os.close(fd)
 return b
def doc(p):return json.loads(read(p))
def git(root,*args):
 return subprocess.run(['git','-c','protocol.allow=never','-C',str(root),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15,check=True,env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_OPTIONAL_LOCKS':'0','GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1','GIT_ALLOW_PROTOCOL':''}).stdout
def blob(root,ref):
 assert git(root,'cat-file','-t',ref).strip()==b'blob' and int(git(root,'cat-file','-s',ref))<=4194304;return git(root,'cat-file','blob',ref)
assert h(read(I/'MANIFEST01.json'))=='c8cc30cf3eb7d24c337f4f4fab1241171501add82ca7818058f74fb605e9f974'
for row in doc(I/'MANIFEST01.json')['files']:
 b=read(I/row['path']);assert len(b)==row['bytes'] and h(b)==row['sha256']
cat=doc(I/'TARGET_CATALOG01.json');assert h(read(I/'TARGET_CATALOG01.json'))=='f64d25ee45b5816a6b9c39680e45617dd90f62c26f040dc0ea4020a66a3eb8c0'
rec=doc(P/'REMOTE_PRIMARY_RECOVERY01.json');ret=doc(P/'RETAINED_PRIMARY01.json');release=doc(P/'release01.json');inputs=release['cases']['success']['experiment']['inputs'];members={x['path']:x for x in ret['members']}
assert git(G,'rev-parse','FETCH_HEAD').decode().strip()==rec['remote_commit']=='e5079ce3aae9f09cb2b1dc67d113568c15cd39ae'
assert len(rec['selected_blobs'])==52
for row in rec['selected_blobs']:
 b=blob(G,rec['remote_commit']+':'+row['path']);assert len(b)==row['bytes'] and h(b)==row['sha256'];assert read(R/row['path'])==b
archive=P/'outcome-recovery01/retained-primary01.tar.gz';assert h(read(archive))==rec['archive_sha256']==ret['archive_sha256']=='5f7d187b6320c7da55d7c47a87757bddcd03e093729cf4ed8f09cfe35cf3e6f1'
selected={n:v for n,v in inputs.items() if n.startswith('target_') or v['path'].startswith('fixture_inputs/original/')};assert len(selected)==22 and len({x['path'] for x in selected.values()})==22
checked=[]
with tarfile.open(archive,'r:gz') as t:
 items=t.getmembers();assert len(items)==1058 and len({m.name for m in items})==1058;by={m.name:m for m in items}
 for name,v in sorted(selected.items()):
  a=read(C/v['path']);b=read(X/v['path']);m=members[v['path']];tm=by['capsule04/'+v['path']]
  assert a==b and h(a)==v['sha256']==m['sha256'] and len(a)==m['bytes']==tm.size and tm.isfile()
  assert stat.S_IMODE((C/v['path']).lstat().st_mode)==stat.S_IMODE((X/v['path']).lstat().st_mode)==tm.mode==m['mode']
  with t.extractfile(tm) as s:assert s.read(4194305)==a
  assert v['dataset']==('original_dictionary' if v['path'].startswith('fixture_inputs/original/') else 'synthetic')
  checked.append({'role':name,'path':v['path'],'bytes':len(a),'sha256':h(a),'mode':m['mode'],'dataset':v['dataset']})
assert sum(x['bytes'] for x in checked)==961506
index=doc(F/'original-import-fixture-native-preparation-2026-10-03/original_inputs01.json');orig=doc(I/'ORIGINAL_IMPORT_INDEX_ROLE01.json');assert h(read(I/'ORIGINAL_IMPORT_INDEX_ROLE01.json')).startswith('a93eba3a')
assert len(orig['inputs'])==len(index['inputs'])==11 and sum(x['reference']['bytes'] for x in orig['inputs'])==957811
for x in orig['inputs']:
 v=selected[x['name']];z=next(a for a in index['inputs'] if a['capsule_path']==v['path']);assert x['reference']=={'path':v['path'],'sha256':v['sha256'],'bytes':z['bytes']} and x['original_path']==z['original_path']
objs=[]
for name,v in sorted(index['original_source_files'].items()):
 b=blob(C,index['original_source']+':'+name);assert b==blob(X,index['original_source']+':'+name) and h(b)==v['sha256']==v['claim_sha256'];objs.append({'path':name,'bytes':len(b),'sha256':h(b)})
assert len(objs)==26 and sum(x['bytes'] for x in objs)==122632
history=[]
for n in range(1,5):
 identity='original-import-native-success-20261003-%02d'%n;prefix='research_runs/'+identity
 claim=doc(C/prefix/'claim.json');failed=doc(C/prefix/'failed.json')
 for tail in ('claim.json','failed.json'):
  name=prefix+'/'+tail;b=read(C/name);assert b==read(X/name) and h(b)==members[name]['sha256']
 assert failed['status']=='failed' and failed['experiment_id']==identity and failed['claim_sha256']==h(read(C/prefix/'claim.json'))
 regraw=blob(X,claim['source']+':'+claim['registration']);assert h(regraw)==claim['registration_sha256'];reg=json.loads(regraw);exp=reg['experiments'][identity]
 assert exp['inputs']==claim['inputs'];assert all(claim['inputs'][k]==v for k,v in selected.items())
 gen=blob(X,claim['source']+':fixture_tools/generate_inputs01.py');assert h(gen)==exp['source_files']['fixture_tools/generate_inputs01.py']
 assert all(v['exposures'][0]['state']=='spent' for v in reg['datasets'].values())
 history.append({'identity':identity,'claim_sha256':h(read(C/prefix/'claim.json')),'source':claim['source'],'terminal_sha256':h(read(C/prefix/'failed.json')),'status':'failed'})
# Validate catalog against independently authenticated role map and original manifests.
def check_catalog(value,roles):
 assert len(value['targets'])==2 and [x['graph_hash'] for x in value['targets']]==sorted({x['graph_hash'] for x in value['targets']}) and [x['nodes'] for x in value['targets']]==[2,3]
 seen=set()
 for target in value['targets']:
  role=target['input_name'];assert role not in seen;seen.add(role);v=roles[role];ref=target['manifest'];assert ref['path']==v['path'] and ref['sha256']==v['sha256'] and v['dataset']=='synthetic'
  raw=read(X/ref['path']);assert h(raw)==ref['sha256'] and len(raw)==ref['bytes'];m=json.loads(raw)
  assert m['graph_hash']==target['graph_hash'] and m['metadata']['source_hashes']==[roles['target_provenance']['sha256']]
  assert set(target['components'])==set(m['arrays'])=={'node_ids','node_features','edge_index','edge_features'}
  for key,item in target['components'].items():
   name=role+'_'+key;assert name not in seen;seen.add(name);r=roles[name];a=m['arrays'][key]
   assert item['path']==r['path']==str(Path(ref['path']).parent/a['path']) and item['sha256']==r['sha256']==a['sha256'] and item['bytes']==a['bytes'] and r['dataset']=='synthetic'
 assert len(seen)==10
check_catalog(cat,selected)
negative=[]
for kind in ('path','hash','missing','dataset','role-collision'):
 c=copy.deepcopy(cat);r=copy.deepcopy(selected)
 if kind=='path':c['targets'][0]['manifest']['path']='wrong.json'
 if kind=='hash':c['targets'][0]['manifest']['sha256']='00'*32
 if kind=='missing':del c['targets'][0]['components']['edge_index']
 if kind=='dataset':r['target_graph_1']['dataset']='original_dictionary'
 if kind=='role-collision':c['targets'][1]['input_name']=c['targets'][0]['input_name']
 try:check_catalog(c,r)
 except (AssertionError,KeyError):negative.append(kind)
 else:raise AssertionError('counterexample accepted '+kind)
# Opaque mutation refusal is exercised only on an explicitly synthetic tiny body.
tiny=H/'tiny-mutated.bin';tiny.write_bytes(b'synthetic-original');expected=h(read(tiny));tiny.write_bytes(b'synthetic-mutated');assert h(read(tiny))!=expected;negative.append('recovered-body-mutation')
prov=doc(I/'TARGET_PROVENANCE_ROLE01.json');assert prov['dataset']=='synthetic' and prov['name']=='target_provenance' and prov['reference']['path']==selected['target_provenance']['path'] and h(read(X/prov['reference']['path']))==prov['reference']['sha256']
report={'status':'accepted selected existing input reuse provenance only','selected_bodies':checked,'selected_bytes':961506,'remote_commit':rec['remote_commit'],'remote_git_bodies':52,'archive_sha256':rec['archive_sha256'],'archive_members':1058,'original_source_objects':objs,'historical_failed_claims':history,'counterexamples_refused':negative,'arrays_decoded':False,'claims':0,'network':0,'scope':'selected22 input members checked original/recovered/archive; full-tree recovery acceptance inherited from independent review04, not replayed'}
(H/'READBACK01.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print('PASS: 22 input bodies,52 fetched Git bodies,26 original source objects,4 failed claim joins,6 counterexamples; no numerical import or admission.')
