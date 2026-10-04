from pathlib import Path
import os,stat,json,hashlib,io,gzip,tarfile,time
H=Path(__file__).resolve().parent;B=H.parent;A=B/'financial-wrapper-compatibility-composed-recovery-preparation01-2026-10-04';D=B/'financial-wrapper-compatibility-composed-recovery-root01-2026-10-04';checks=[];cache={};pins={};start=time.monotonic();total=0
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
measurement=j(D/'ROOT_MEASUREMENT01.json','9e449c822313c833b77e8f1d2a85d3a535c210aecd66975809d51b9f5fa980b2');actual=j(D/'MEASURED01.stdout','180b37682d24160a0dad8c2f9e8008e3fa64380a779c4eb86d252ce5a2961861');ok(read(D/'MEASURED01.stderr')==b'' and measurement['actual_root_observed_child_exit']==0 and not Path('/proc',str(measurement['child_pid'])).exists(),'actual measurement terminal/absence');read(A/'verify01.py',measurement['source_sha256'])
# Complete author typed scope, no opening FIFO/symlink/hardlinks.
manifest=j(A/'MANIFEST01.json',measurement['source_author_manifest_sha256']);special=[]
for z in manifest['members']:
 p=A/z['path'];s=p.lstat();ok(stat.S_IMODE(s.st_mode)==z['mode'],'author literal mode '+z['path'])
 if z['kind']=='file':
  ok(stat.S_ISREG(s.st_mode) and s.st_size==z['bytes'],'author file extent')
  if s.st_nlink==1:read(p,z['sha256'])
  else:special.append({'path':z['path'],'type':'hardlinked regular','inode':s.st_ino,'nlink':s.st_nlink,'content_not_opened':True})
 elif z['kind']=='directory':ok(stat.S_ISDIR(s.st_mode),'author directory')
 elif z['kind']=='fifo':ok(stat.S_ISFIFO(s.st_mode),'retained FIFO notopened');special.append({'path':z['path'],'type':'fifo','content_not_opened':True})
 elif z['kind']=='symlink':ok(stat.S_ISLNK(s.st_mode) and os.readlink(p)==z['target'],'literal link notfollowed');special.append({'path':z['path'],'type':'symlink','target':z['target'],'content_not_opened':True})
 else:raise AssertionError(z)
for p,x in cfg['fixed'].items():ok(len(read(Path(p),x['sha256']))==x['bytes'],'fixed genuine input extent')
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
policy=j(P['policy']/'POLICY01.json','ae8fbdc9d13e75fc453b70b5ee633c89fb4577e9b68a35b4147cf1bbd58c6887');basis=json.loads(newbody['delta']['COMPOSITION_BASIS01.json']);current={x['path']:x for x in basis['current589_manifest']['members']};changes={x['path']:x for x in basis['new_source_changes']};protected=j(P['adoption_review']/'PROTECTED_NON_TARGET585.json');protected={x['path']:x for x in protected['members']};ok(len(current)==589 and len(changes)==4 and set(protected)==set(current)-set(changes),'589/585/fourbody delta')
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');seen=set();pending=[CAP]
while pending:
 p=pending.pop()
 with os.scandir(p) as it:
  for e in it:
   if p==CAP and e.name=='.git':continue
   n=str(Path(e.path).relative_to(CAP));s=e.stat(follow_symlinks=False);ok(stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode),'current no special');seen.add(n)
   if stat.S_ISDIR(s.st_mode):pending.append(Path(e.path))
ok(seen==set(current),'actual full589 path equality');composed={}
for n,z in current.items():
 s=(CAP/n).lstat();mode=z['mode'] if type(z['mode']) is int else int(z['mode'],8);ok(stat.S_IMODE(s.st_mode)==mode,'current literal mode')
 if n in protected:ok(protected[n]==z==oldrows[n],'exact585 preserved metadata')
 if z['kind']=='directory':continue
 b=read(CAP/n,z['sha256']);original=newbody['delta']['current-source/'+n] if n in changes else old[n];ok(b==original,'completecurrent body originalbasis');composed[n]=b
oldmap=policy['historical']['installed'];newmap=policy['target']['installed'];canonical=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
ok(sha(canonical(oldmap))=='ebb1727ccb55678aead9f0d5b5ee43ec81a46019c7fbb13c4b4f76144507bbca' and sha(canonical(newmap))=='2e281f7ca64a12be316424d8e93b0eab28ba0d121214e79ada7249c96930b040','exactmaphashes')
for n,h in oldmap.items():ok(sha(old[n])==h,'all194historicalpathhashes')
for n,h in newmap.items():ok(sha(composed[n])==h,'all195targetpathhashes')
ok(len(oldmap)==194 and len(newmap)==195 and sum(oldmap.get(n)==v for n,v in newmap.items())==191,'exact pathmapdenominators')
# Independent complete logical object framing and recursive typed ancestry, no Git executable.
idx=json.loads(newbody['delta']['SOURCE_GIT394_METADATA01.json']);graph={}
for x in idx['objects']:
 b=objects[x['oid']] if x['body_basis']=='actual-old385-recovery' else newbody['delta'][x['body_basis']];ok(len(b)==x['bytes'] and sha(b)==x['sha256'] and hashlib.sha1(x['type'].encode()+b' '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['oid'],'complete object oid/type/extent');graph[x['oid']]=(x['type'],b)
seen=set();todo=[('commit','7b056a574e3e7b3c7ba209a39ee6a615e649d60c')];trees={}
while todo:
 typ,oid=todo.pop();ok(oid in graph and graph[oid][0]==typ,'all ancestral typed edge')
 if oid in seen:continue
 seen.add(oid);body=graph[oid][1]
 if typ=='commit':
  lines=body.split(b'\n\n',1)[0].splitlines();roots=[x[5:].decode() for x in lines if x.startswith(b'tree ')];ok(len(roots)==1,'onecommittree');todo.extend([('tree',roots[0])]+[('commit',x[7:].decode()) for x in lines if x.startswith(b'parent ')])
 elif typ=='tree':
  rows=[];i=0
  while i<len(body):
   z=body.index(b'\0',i);mode,name=body[i:z].split(b' ',1);oid2=body[z+1:z+21].hex();ok(mode in [b'40000',b'100644',b'100755'] and name and b'/' not in name and name not in [b'.',b'..'] and len(oid2)==40,'canonicaltreeentry');rows.append((mode,name,oid2));todo.append(('tree' if mode==b'40000' else 'blob',oid2));i=z+21
  keys=[n+(b'/' if m==b'40000' else b'') for m,n,o in rows];ok(keys==sorted(keys) and len(set(n for m,n,o in rows))==len(rows),'canonicalGitdirectoryslashorder');trees[oid]=rows
ok(len(graph)==394 and seen==set(graph),'all385plus9reachable394');headtree=[x[5:].decode() for x in graph['7b056a574e3e7b3c7ba209a39ee6a615e649d60c'][1].splitlines() if x.startswith(b'tree ')][0];todo=[('',headtree)];tracked={}
while todo:
 prefix,oid=todo.pop()
 for m,n,ch in trees[oid]:
  path=prefix+n.decode()
  if m==b'40000':todo.append((path+'/',ch))
  else:ok(composed[path]==graph[ch][1] and bool(stat.S_IMODE((CAP/path).lstat().st_mode)&0o111)==(m==b'100755'),'340currenttreebodymode');tracked[path]=ch
ok(len(tracked)==340,'actual340tracked')
claims=[]
for n,b in composed.items():
 if n.startswith('research_runs/') and n.endswith('/claim.json'):
  c=json.loads(b);fail=n[:-10]+'failed.json';ok(fail in composed and n[:-10]+'complete.json' not in composed,'actualFAILEDretained');claims.append({'claim_sha256':sha(b),'failed_sha256':sha(composed[fail]),'budget':c.get('effective_attempt_budget',c['family']['attempt_budget'])})
ok(len(claims)==3 and max(c['budget'] for c in claims)==19,'actualthreespenthighest19')
for p,sig in pins.items():s=p.lstat();ok((s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==sig,'final full read fingerprint')
report={'decision':'INDEPENDENT_COMPOSITION_BYTES_RECONSTRUCTED_SOURCE_PROOF_WITHHELD_CR1_CR2','assertions':len(checks),'distinct_regular_files_read':len(cache),'bytes_read':total,'actual_root_measurement_files':actual['files_read'],'actual_root_measurement_bytes':actual['bytes_read'],'all_scope_details':scopes,'complete_original_CAP_bodies':len(old),'current_typed':589,'protected_typed':585,'oldmap_paths':194,'newmap_paths':195,'unchanged_paths':191,'all_reachable_objects':len(graph),'tracked':len(tracked),'claims':claims,'author_special_controls_not_opened':special,'accepted_proof':None,'numerical_authority':False,'actual_restoration_or_network':False,'checks':checks}
(H/'RECONSTRUCTION01.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['checks','claims','author_special_controls_not_opened','all_scope_details']}))
