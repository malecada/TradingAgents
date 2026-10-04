from pathlib import Path
import os,stat,json,hashlib,io,gzip,tarfile,time
H=Path(__file__).resolve().parent;B=H.parent;A=B/'financial-wrapper-compatibility-composed-recovery-correction02-2026-10-04';D=B/'financial-wrapper-compatibility-composed-recovery-root02-2026-10-04';checks=[];cache={};pins={};start=time.monotonic();total=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def read(p,pin=None):
 global total
 p=Path(p);s=p.lstat();ok(time.monotonic()-start<180 and p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304,'finite regular '+str(p))
 sig=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
 if p not in cache:
  b=p.read_bytes();ok(sig(s)==sig(p.lstat()),'actual stable read '+str(p));cache[p]=b;pins[p]=sig(s);total+=len(b);ok(total<=256*1024**2,'total bound')
 else:ok(pins[p]==sig(s),'retained signature '+str(p));b=cache[p]
 ok(pin is None or sha(b)==pin,'hash '+str(p));return b
def j(p,pin=None):return json.loads(read(p,pin))
cfg=j(A/'INPUTS01.json','f992329f1e0baf29bff17eaa1ba82d0f0fe73edf5f8845b9d30a7386f630f4af');P={k:Path(v) for k,v in cfg['paths'].items()}
def flat(dest,rec,manifest,archive):
 md=j(dest/rec['metadata_file'],rec['metadata_sha256']);ok(md['manifest']==manifest,'full actual flatmanifest');files={x['path']:x for x in manifest['members'] if x['kind']=='file'};mp=md['flat_members'];ok(set(mp)==set(files) and len(set(mp.values()))==len(files),'allflatbijective');ok(set(x.name for x in dest.iterdir())==set(mp.values())|{rec['metadata_file']},'exactflatnames');bodies={};buf=io.BytesIO()
 with gzip.GzipFile(filename='',mode='wb',fileobj=buf,mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tar:
   for z in manifest['members']:
    ti=tarfile.TarInfo(z['path']);ti.uid=ti.gid=ti.mtime=0;ti.uname=ti.gname='';ti.mode=z['mode'] if type(z['mode']) is int else int(z['mode'],8)
    if z['kind']=='directory':ti.type=tarfile.DIRTYPE;tar.addfile(ti);continue
    leaf=mp[z['path']];ok('/' not in leaf,'flatleaf');body=read(dest/leaf,z['sha256']);ok(len(body)==z['bytes'] and stat.S_IMODE((dest/leaf).lstat().st_mode)==0o600,'actualprivatebody');bodies[z['path']]=body;ti.size=len(body);tar.addfile(ti,io.BytesIO(body))
 ok(buf.getvalue()==archive,'fullcanonical reencoding '+str(dest));return bodies,{z['path']:z for z in manifest['members']}
oldreceipt=j(P['old_root']/'FLAT_RECOVERY01.json');old={};oldrows={};scopes=[]
for role,rec in oldreceipt['scopes'].items():
 manifest=j(P['old_capture']/(role.upper()+'_MANIFEST01.json'),rec['manifest_sha256']);ar=read(P['old_capture']/('complete-'+role+'01.tar.gz'),rec['archive_sha256']);b,rows=flat(P['old_root']/('flat-'+role+'01'),rec,manifest,ar);scopes.append({'family':'oldfailed','scope':role,'files':len(b)})
 if role.startswith('capsule'):
  ok(not set(b)&set(old),'disjointoldfiles');old.update(b)
  for n,z in rows.items():ok(n not in oldrows or oldrows[n]==z,'consistent shared dirs');oldrows[n]=z
ok(len(old)==475 and len(oldrows)==588,'complete originalCAP475/588')
base=j(P['baseline_root']/'FLAT_RECOVERY01.json');objects={}
for role in ['git1','git2','git3']:
 rec=base['scopes'][role];man=j(P['baseline_capture']/(role.upper()+'_MANIFEST01.json'),rec['manifest_sha256']);ar=read(P['baseline_capture']/('complete-'+role+'01.tar.gz'),rec['archive_sha256']);b,_=flat(P['baseline_root']/('flat-'+role+'01'),rec,man,ar);ok(not set(objects)&set(b),'disjointoldobjects');objects.update(b);scopes.append({'family':'baseline','scope':role,'files':len(b)})
ok(len(objects)==385,'genuine385original recovered objects')
newreceipt=j(P['receiver']/'FLAT_RECOVERY01.json');newbody={}
for role,root,key,manname,arname,out in [('delta',P['delta'],'restored','PAYLOAD_MANIFEST01.json','operational-delta01.tar.gz','flat-operational-delta01'),('failed',P['failed_delta'],'failed_restored','FAILED_PAYLOAD_MANIFEST01.json','failed-remote02.tar.gz','flat-failed-remote02-01')]:
 rec=newreceipt[key];man=j(root/manname,rec['manifest_sha256']);ar=read(root/arname,rec['archive_sha256']);b,_=flat(P['receiver']/out,rec,man,ar);newbody[role]=b;scopes.append({'family':'newflat','scope':role,'files':len(b)})
# New review independently extends previously reconstructed immutable BYTE basis.
import ast,difflib,subprocess
C=B/'heartbeat-root-checkpoint10-2026-10-04'
D=B/'financial-wrapper-compatibility-current-source-parent-capture04-2026-10-04';S=D/'snapshot'
F=B/'financial-wrapper-compatibility-current-source-parent-capture03-2026-10-04'
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
PARENT=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01')
CURRENT='32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41'
oldsrc=read(C/'root_source_parent_capture03.py','368d77b3c2bf5e6850d1de6d22f9ced8c51f3521309d87e7021da712f6d510c8')
newsrc=read(C/'root_source_parent_capture04.py','f55ce818ef7999195c88d872c983a568861d5d45d2970af61b539979faf27cdf')
inv=j(C/'CAPTURE04_SOURCE_INVERSE01.json');rev=newsrc.decode()
for e in reversed(inv['edits']):ok(rev.count(e['new'])==1,'unique inverse segment');rev=rev.replace(e['new'],e['old'])
ok(rev.encode()==oldsrc and ast.dump(ast.parse(rev))==ast.dump(ast.parse(oldsrc)),'full three-edit byte/AST inverse')
oldnodes={n.name:ast.dump(n) for n in ast.parse(oldsrc).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};newnodes={n.name:ast.dump(n) for n in ast.parse(newsrc).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
ok(set(oldnodes)==set(newnodes) and all(oldnodes[n]==newnodes[n] for n in oldnodes if n not in ('put','main')),'all other function/class AST identical')
cap=j(D/'CAPTURE01.json','5a44a5f98f70c23fa059054c24014d7921f86a992671700801ea857a95813b66')
man=j(D/'MANIFEST01.json','49df5d5e80f307948b32bb6a3eb1a2234f8bbd8ffb2c5592700b69828caaa913')
ar=read(D/'source-parent-delta04.tar.gz','d90353cb0d72df5fca6ed2479f2ea6b28400a9dcdc6bc1143a8973665ca1d8b1')
terminal=j(D/'ACTUAL_ROOT_EXIT01.json','115c0a7eed1057c940788835031a750c31c0bb86e62b2b5a4f5696ed9110967a')
ok(terminal['capture_sha256']==sha(read(D/'CAPTURE01.json')) and terminal['source_sha256']==sha(newsrc) and terminal['actual_tool_exit']==0 and terminal['tool_chunk']=='5b7011' and terminal['original_process_pid_unrecorded'] is None,'separate observed actual tool exit; PID unknown')
rows={x['path']:x for x in man['members']};ok(len(rows)==len(man['members']) and list(rows)==sorted(rows),'sorted unique archive entries')
payload={};seen=set();pending=[S]
while pending:
 p=pending.pop()
 with os.scandir(p) as it:
  for e in it:
   n=str(Path(e.path).relative_to(S));ss=e.stat(follow_symlinks=False);seen.add(n);ok(n in rows and stat.S_IMODE(ss.st_mode)==rows[n]['mode'],'physical private namespace mode')
   if stat.S_ISDIR(ss.st_mode):ok(rows[n]['kind']=='directory','directory kind');pending.append(Path(e.path))
   else:ok(stat.S_ISREG(ss.st_mode) and rows[n]['kind']=='file','regular snapshot');body=read(Path(e.path),rows[n]['sha256']);ok(len(body)==rows[n]['bytes'],'snapshot extent');payload[n]=body
ok(seen==set(rows) and len(payload)==47 and sum(map(len,payload.values()))==2119573,'complete47payload exact typed scope')
buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w',format=tarfile.USTAR_FORMAT) as t:
 for x in man['members']:
  ti=tarfile.TarInfo(x['path']+('/' if x['kind']=='directory' else ''));ti.mode=x['mode'];ti.mtime=ti.uid=ti.gid=0;ti.uname=ti.gname=''
  if x['kind']=='directory':ti.type=tarfile.DIRTYPE;t.addfile(ti)
  else:ti.size=x['bytes'];t.addfile(ti,io.BytesIO(payload[x['path']]))
ok(gzip.compress(buf.getvalue(),mtime=0)==ar,'full canonical USTAR header/body/padding/footer/gzip reproduction')
with tarfile.open(fileobj=io.BytesIO(ar),mode='r:gz') as tar:
 for ti,x in zip(tar.getmembers(),man['members'],strict=True):
  ok(ti.name==x['path'] and ti.mode==x['mode'] and ti.uid==ti.gid==ti.mtime==0 and not ti.pax_headers and ti.uname==ti.gname=='','independent archive header')
  ok(ti.isdir() if x['kind']=='directory' else ti.isfile() and tar.extractfile(ti).read()==payload[x['path']],'independent archive body')
orig=json.loads(payload['ORIGINAL_ORIGINS01.json']);ok(len(orig)==31,'31 original input/Parent/review origin mappings')
for n,z in orig.items():
 p=Path(z['origin']);ok(read(p,z['sha256'])==payload[n] and len(payload[n])==z['bytes'] and stat.S_IMODE(p.lstat().st_mode)==z['original_mode'],'literal original byte and mode '+n)
master=json.loads(payload['CAPSULE_MASTER605.json']);current={x['path']:x for x in master['members']};ok(len(current)==605,'605 unique rows')
basis=json.loads(newbody['delta']['COMPOSITION_BASIS01.json']);oldcurrent={x['path']:x for x in basis['current589_manifest']['members']};changes={x['path']:x for x in basis['new_source_changes']}
newnames=set(current)-set(oldcurrent);ok(len(newnames)==16 and set(oldcurrent)<=set(current),'589 plus15bodies anddirectory605')
preview=j(B/'financial-wrapper-compatibility-gate-preview02-2026-10-04/PREVIEW01.json','b725fa4f1f6b071cf910eeb24edab11aaa20c9e50475fcda54dc5e1dcc15c0d2')
ok({n for n in newnames if current[n]['kind']=='file'}==set(preview['new_file_pins']) and len(preview['new_file_pins'])==15,'all15 source inputs exact preview set')
seen=set();pending=[CAP]
while pending:
 p=pending.pop()
 with os.scandir(p) as it:
  for e in it:
   if p==CAP and e.name=='.git':continue
   n=str(Path(e.path).relative_to(CAP));ss=e.stat(follow_symlinks=False);ok(stat.S_ISDIR(ss.st_mode) or stat.S_ISREG(ss.st_mode),'wholeCAP type');seen.add(n)
   if stat.S_ISDIR(ss.st_mode):pending.append(Path(e.path))
ok(seen==set(current) and stat.S_IMODE(CAP.lstat().st_mode)==master['root_mode'],'full current605 canonical namespace/rootmode')
composed={}
for n,z in current.items():
 ss=(CAP/n).lstat();ok(stat.S_IMODE(ss.st_mode)==z['mode'],'wholeCAP literal mode')
 if n in oldcurrent:ok(z==oldcurrent[n],'all589 historical metadata retained')
 if z['kind']=='directory':continue
 body=read(CAP/n,z['sha256']);ok(len(body)==z['bytes'],'wholeCAP bodyextent')
 basisbody=payload['source-inputs/'+n] if n in newnames else (newbody['delta']['current-source/'+n] if n in changes else old[n])
 ok(body==basisbody,'wholeCAP oldrecovered plusactualnewbody');composed[n]=body
policy=json.loads(composed['fixture_inputs/financial_wrapper_compatibility01/policy.json']);canonical=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode();oldmap=policy['historical']['installed'];newmap=policy['target']['installed']
ok(sha(canonical(oldmap))=='ebb1727ccb55678aead9f0d5b5ee43ec81a46019c7fbb13c4b4f76144507bbca' and sha(canonical(newmap))=='2e281f7ca64a12be316424d8e93b0eab28ba0d121214e79ada7249c96930b040','full exact194/195 source maps')
for n,pin in newmap.items():ok(sha(composed[n])==pin,'target source body '+n)
for n,pin in oldmap.items():ok(sha(old[n])==pin,'historical source body '+n)
ok(len(oldmap)==194 and len(newmap)==195 and sum(oldmap.get(n)==h for n,h in newmap.items())==191,'full194195191 denominators')
for n,pin in [('model.json','20f451c08143dd81491b5c9fa0a90243ee6a9363df1fbbfcbd9c45b32f9b054d'),('training.json','d5276b75491e130bd03d43de28120f72dd792e42af4446382a6c127d387b8ec0'),('synthetic_recipe.json','f8b1ec1eed902f3cca76bd7e06d2435accda699173b9a7942d10c37c64f01040')]:ok(sha(composed['fixture_inputs/financial_wrapper_compatibility01/'+n])==pin,'unchanged scientific config '+n)
# Logical objects reconstructed entirely from literal already recovered bodies + captured13.
idxold=json.loads(newbody['delta']['SOURCE_GIT394_METADATA01.json']);idx=json.loads(payload['SOURCE_GIT407_METADATA01.json']);graph={};oldoids={x['oid'] for x in idxold['objects']}
for x in idxold['objects']:
 body=objects[x['oid']] if x['body_basis']=='actual-old385-recovery' else newbody['delta'][x['body_basis']];graph[x['oid']]=(x['type'],body)
for x in idx['objects']:
 if x['oid'] in oldoids:ok(x['body_basis']=='accepted-original394-composition','original394 explicit historicalbasis');body=graph[x['oid']][1]
 else:body=payload[x['body_basis']];graph[x['oid']]=(x['type'],body)
 ok(len(body)==x['bytes'] and sha(body)==x['sha256'] and hashlib.sha1(x['type'].encode()+b' '+str(len(body)).encode()+b'\0'+body).hexdigest()==x['oid'],'all407 authentictype framingOID extenthash')
ok(len(graph)==407 and len(set(graph)-oldoids)==13,'old394 retained13new407')
seen=set();todo=[('commit',CURRENT)];trees={}
while todo:
 typ,oid=todo.pop();ok(oid in graph and graph[oid][0]==typ,'all typed ancestry edges')
 if oid in seen:continue
 seen.add(oid);body=graph[oid][1]
 if typ=='commit':
  ls=body.split(b'\n\n',1)[0].splitlines();roots=[x[5:].decode() for x in ls if x.startswith(b'tree ')];ok(len(roots)==1,'one root tree');todo.extend([('tree',roots[0])]+[('commit',x[7:].decode()) for x in ls if x.startswith(b'parent ')])
 elif typ=='tree':
  rr=[];i=0
  while i<len(body):
   z=body.index(b'\0',i);mode,name=body[i:z].split(b' ',1);child=body[z+1:z+21].hex();ok(mode in (b'40000',b'100644',b'100755') and name not in (b'',b'.',b'..') and b'/' not in name and len(child)==40,'canonical tree entry');rr.append((mode,name,child));todo.append(('tree' if mode==b'40000' else 'blob',child));i=z+21
  keys=[n+(b'/' if m==b'40000' else b'') for m,n,o in rr];ok(keys==sorted(keys) and len({n for m,n,o in rr})==len(rr),'canonical slash sort unique names');trees[oid]=rr
ok(seen==set(graph),'complete407 reachable no missing or foreign objects')
lines=graph[CURRENT][1].splitlines();ok([x[7:].decode() for x in lines if x.startswith(b'parent ')]==['7b056a574e3e7b3c7ba209a39ee6a615e649d60c'],'direct original source parent')
todo=[('',[x[5:].decode() for x in lines if x.startswith(b'tree ')][0])];tracked={}
while todo:
 prefix,oid=todo.pop()
 for m,n,ch in trees[oid]:
  path=prefix+n.decode()
  if m==b'40000':todo.append((path+'/',ch))
  else:ok(composed[path]==graph[ch][1] and bool(current[path]['mode']&0o111)==(m==b'100755'),'full355 tracked body/mode');tracked[path]=ch
ok(len(tracked)==355,'current tracked355')
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_NO_REPLACE_OBJECTS='1',GIT_ALLOW_PROTOCOL='')
actualhead=subprocess.run(['git','rev-parse','HEAD'],cwd=CAP,env=env,check=True,capture_output=True,timeout=10).stdout.decode().strip();ok(actualhead==CURRENT,'actual currentHEAD read-only join')
gate=json.loads(composed['fixture_inputs/financial_wrapper_compatibility01/gates.json']);q=json.loads(payload['parent/REQUEST_DRAFT01.json'])
ok(set(p.name for p in PARENT.iterdir())=={n[7:] for n in payload if n.startswith('parent/')},'complete10 Parent current files')
ok(sha(payload['parent/parent01.py'])=='424f13b653d970efc4994e76e27f4ff5e8cf732133daab6a956cb1a034299ea0' and sha(payload['parent/REQUEST_DRAFT01.json'])=='e7579251741a865a2955917a3a9dc346ed6710ffc08388f1907c727e95d0a721','exact accepted Parent draft')
ok(q['source_commit']==CURRENT if 'source_commit' in q else CURRENT in str(q),'actual Q source context')
# Preserve actual failed03 payload: valid bytes/archive do not repair its physical mismatch.
failed=j(F/'FAILED_LOCAL_CAPTURE01.json');ok(failed['actual_exit']==1 and not (F/'CAPTURE01.json').exists(),'03 remains failed no program success receipt')
ok(read(F/'MANIFEST01.json')==read(D/'MANIFEST01.json') and read(F/'source-parent-delta03.tar.gz')==ar,'original03 declaredmanifest/archive byte-identical preserved')
mode_failures=[]
for n,x in rows.items():
 ss=(F/'snapshot'/n).lstat()
 if stat.S_IMODE(ss.st_mode)!=x['mode']:mode_failures.append({'path':n,'declared':x['mode'],'actual':stat.S_IMODE(ss.st_mode)})
 if x['kind']=='file':ok(read(F/'snapshot'/n)==payload[n],'all03 payload bytes preserved')
ok(mode_failures and all(x['actual']==0o775 and x['declared']==0o700 for x in mode_failures),'original explicit775/700 mismatch preserved')
claims=[]
for n,body in composed.items():
 if n.startswith('research_runs/') and n.endswith('/claim.json'):
  c=json.loads(body);f=n[:-10]+'failed.json';ok(f in composed and n[:-10]+'complete.json' not in composed,'alloriginalFAILED retained');claims.append({'claim':sha(body),'failed':sha(composed[f]),'budget':c.get('effective_attempt_budget',c['family']['attempt_budget'])})
ok(len(claims)==3 and max(c['budget'] for c in claims)==19,'three spent/highest19 no newclaim')
for p,signature in pins.items():ss=p.lstat();ok((ss.st_dev,ss.st_ino,ss.st_mode,ss.st_nlink,ss.st_size,ss.st_mtime_ns,ss.st_ctime_ns)==signature,'final all-read stable signature')
result={'decision':'ACTUAL_LOCAL_CAPTURE_BYTES_VERIFIED_NOT_EXTERNAL_RECOVERY','assertions':len(checks),'distinct_files_read':len(cache),'bytes_read':total,'elapsed_seconds':time.monotonic()-start,'capture_sha256':sha(read(D/'CAPTURE01.json')),'archive_sha256':sha(ar),'archive_bytes':len(ar),'snapshot_files':len(payload),'snapshot_typed':len(rows),'snapshot_bytes':sum(map(len,payload.values())),'current_typed':605,'current_files':len(composed),'old_typed':589,'new_input_files':15,'old_reachable_git':394,'new_git_objects':13,'reachable_git':407,'tracked':355,'source':CURRENT,'source_map_paths':195,'old_map_paths':194,'unchanged_scientific_paths':191,'parent_files':10,'literal_origin_rows':31,'old03_mode_failures':mode_failures,'old03_still_failed':True,'actual_root_exit':terminal,'claims':claims,'assertion_scope':'all15 prior canonical archives and actual flat bodies reconstructed; current47 capture bodies and full605 namespace/hash/mode and407Git ancestry checked','actual_external_recovery':None,'numerical_authority':False}
(H/'READBACK01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
(H/'CHECKS01.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
