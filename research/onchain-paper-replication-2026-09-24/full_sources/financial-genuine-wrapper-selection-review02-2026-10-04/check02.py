import ast,hashlib,json,os,shutil,stat,subprocess,sys
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;ROOT=Path.cwd();P=F/'financial-genuine-wrapper-root-remote-recovery02-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,m):
 assert v,m
 checks.append(m)
def read(p):
 s=p.lstat();ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2 and p.resolve()==p,'regular canonical bounded input');fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  ck(os.fstat(fd)==s,'actual opened identity');out=[];total=0
  while True:
   b=os.read(fd,65536)
   if not b:break
   total+=len(b);ck(total<=s.st_size,'bounded extent');out.append(b)
  ck(os.fstat(fd)==s==p.lstat() and total==s.st_size,'stable body identity');return b''.join(out)
 finally:os.close(fd)
def git(args,data=None):
 r=subprocess.run(['git','--no-replace-objects','-c','protocol.allow=never',*args],input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,env={'PATH':'/usr/bin:/bin','GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1','GIT_OPTIONAL_LOCKS':'0','GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_TERMINAL_PROMPT':'0'});ck(r.returncode==0 and len(r.stdout)<=8*1024**2 and len(r.stderr)<=65536,'bounded local Git only');return r.stdout
raw=read(P/'SELECTED_BODIES01.json');ck(sha(raw)=='5b336b0f0642ec0b521d8dde5820889d395cadbda65fa826e6cc377a6f3fcfa0','exact selection pin');v=json.loads(raw);ck((json.dumps(v,sort_keys=True,indent=2)+'\n').encode()==raw,'canonical selection');H='8ac18965d66fec5e2569b71a82003fa3791005e6';ck(v['remote_commit']==H,'explicit committed selection');rows=v['rows'];names=[r['path'] for r in rows];ck(names==sorted(set(names)) and len(rows)==116 and sum(r['bytes'] for r in rows)==3924686,'exact unique102 extent3924686');ck(11+2*len(rows)==243 and len(rows)<=506 and 243<=1024 and sum(r['bytes'] for r in rows)<=64*1024**2,'effective row and operation budgets');ck(git(['rev-parse','HEAD']).decode().strip()==H,'actual MainHEAD selectedcommit')
committed={}
for ent in git(['ls-tree','-r','-z',H,'--',*names]).split(b'\0'):
 if not ent:continue
 meta,path=ent.split(b'\t');mode,typ,oid=meta.decode().split();committed[path.decode()]={'git_mode':mode,'kind':typ,'git_object':oid}
ck(set(committed)==set(names),'exact committed selected tree');reply=git(['cat-file','--batch'],(''.join(committed[n]['git_object']+'\n' for n in names)).encode());offset=0;joined=[]
for row in rows:
 n=row['path'];p=ROOT/n;meta=committed[n];ck(n.startswith('research/') and Path(n).as_posix()==n and '..' not in Path(n).parts and not any(x in ('.env','keys','apis') for x in Path(n).parts),'safe exact path');ck(type(row['bytes']) is int and 0<=row['bytes']<=4*1024**2 and meta['kind']=='blob' and meta['git_mode'] in ('100644','100755'),'regular selected mode extent');end=reply.index(b'\n',offset);oid,typ,size=reply[offset:end].decode().split();size=int(size);b=reply[end+1:end+1+size];offset=end+size+2
 ck(oid==meta['git_object'] and typ=='blob' and reply[offset-1:offset]==b'\n' and hashlib.sha1(b'blob '+str(size).encode()+b'\0'+b).hexdigest()==oid,'actual Git blob body OID');ck(read(p)==b and sha(b)==row['sha256'] and len(b)==row['bytes'],'complete selected byte joins');mode=stat.S_IMODE(p.lstat().st_mode);ck(meta['git_mode']==('100755' if mode&0o111 else '100644'),'actual executable-mode Git join');joined.append(dict(row,git_mode=meta['git_mode'],git_object=oid,original_filesystem_mode=mode))
ck(offset==len(reply),'complete no trailingGitframe');selected=set(names);review_closures=[]
for row in rows:
 if not row['path'].endswith('/MANIFEST01.json'):continue
 p=ROOT/row['path'];m=json.loads(read(p));members=m.get('members',m.get('entries'));regular={str((p.parent/r['path']).relative_to(ROOT)) for r in members if r.get('kind',r.get('type'))=='file'};ck(regular<=selected,'all selected review manifest regular bodies included')
 for r in members:
  q=p.parent/r['path'];s=q.lstat();ck(stat.S_IMODE(s.st_mode)==r['mode'],'review metadata original mode')
  if r.get('kind',r.get('type'))=='file':ck(stat.S_ISREG(s.st_mode) and s.st_size==r.get('bytes',r.get('size')) and sha(read(q))==r['sha256'],'review actual full regular body')
  elif r.get('kind',r.get('type'))=='directory':ck(stat.S_ISDIR(s.st_mode),'review declared directory retained as metadata')
  else:raise AssertionError('unexpected review member kind')
 review_closures.append({'manifest':row['path'],'regular_members':len(regular),'typed_members':len(members)})

C=F/'financial-genuine-wrapper-root-preservation03-2026-10-04';ck({str(p.relative_to(ROOT)) for p in C.iterdir()}<=selected,'complete actualcapture support closure');cap=json.loads(read(C/'CAPTURE01.json'));request=json.loads(read(C/'REQUEST01.json'));ck(sha(read(C/'CAPTURE01.json'))=='3401a6d84e8e00439e921eaafa690e155f16022d742d9f77045742db15d42660' and sha(read(C/'REQUEST01.json'))=='17d92c05d58c3e4308097a945b3de3180e33629f92df1bfb83abcbaa6f67390f','actual exactcapture request');ck(cap['source']==request['source']=='d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0' and request['tracked']==290 and request['source_pins']==289 and request['implementation']==194 and request['package']==149,'actualsource290scope')
for role,count,pin in [('source',878,'4a483c2d9d1ed1c5f652e73bb818ca8bd11dbe79fa7acaae34b11248655a4e76'),('parent',15,'d620cea8113f365fb1c9a458f245031b1f04c063c861f0b08a9f1ba71f1e2c7f')]:
 mraw=read(C/(role.upper()+'_MANIFEST01.json'));m=json.loads(mraw);archive=read(C/('complete-'+role+'01.tar.gz'));ck(sha(mraw)==cap['archives'][role]['manifest_sha256']==request[role+'_manifest_sha256'] and len(m['members'])==cap[role+'_members']==count,'exact actual targetmanifest lineage');ck(sha(archive)==cap['archives'][role]['sha256']==pin and len(archive)==cap['archives'][role]['bytes'],'exact complete selectedarchive body')
# Explicit full capture acceptance binds the complete canonical/body audit, not only counts.
I=F/'financial-genuine-wrapper-full-scope-preservation-review03-2026-10-04';ck(sha(read(I/'MANIFEST01.json'))=='c6e9a4d2e626ab6943e1c3d8b513f849989df2683b5a7a1c879632c234736614' and sha(read(I/'REVIEW01.md'))=='b07002130503cf725b9269542bf4e98aded84fad1ebb332de1760028e5684485','exact acceptedcompletecapture/source review');prior=json.loads(read(I/'READBACK01.json'));ck(prior['capture_sha256']==sha(read(C/'CAPTURE01.json')) and all(prior['archives'][role]['archive']==cap['archives'][role] for role in ['source','parent']),'actual reviewedwholearchive exactjoins')
for dirname in ['financial-genuine-wrapper-root-parent-composition01-2026-10-04','financial-genuine-wrapper-root-readonly-admission01-2026-10-04']:
 d=F/dirname;ck({str(p.relative_to(ROOT)) for p in d.iterdir()}<=selected,'all actualcomposition/admission support includingfailedcollector')
inv=json.loads(read(P/'INVERSE01.json'));old=read(Path(inv['original_path']));new=read(P/'recover_financial02.py');ck(sha(old)=='20a37f3026233ffcd69c6424c38416a27baf01ccc34b1d410f18f5ec0cd59310' and sha(new)=='2d05df683ec6f12ce2e76be95cd5af0d602e40321939182a7b1fd283a9268e5f','actual acceptedtransport inversepins');reverse=new.decode()
for before,after in inv['exact_string_substitutions']:ck(reverse.count(after)==1,'exactliteralunique');reverse=reverse.replace(after,before)
ck(reverse.encode()==old and ast.dump(ast.parse(reverse),include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False),'wholebyte/AST inverse');ck('len(CALLS) < 1024' in new.decode() and 'START < 600' in new.decode() and 'begun < 60' in new.decode() and inv['effective_max_rows']==506,'finite unchangedbounds')
for n,pin in {'recovery04.py':'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a','owned_io.py':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','bounded_git01.py':'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}.items():
 p=F/'held-consumer-final-recovery-preparation04-2026-10-03'/n;ck(str(p.relative_to(ROOT)) in selected and sha(read(p))==pin,'all3exactselectedR4helpers')
ck(all(not os.path.lexists(P/n) for n in ['fresh-financial02.git','selected','REMOTE_RECOVERY01.json','FAILED01.json']),'freshremote02namespace absent');free=shutil.disk_usage(P).free;ck(free>=10*1024**3,'actualobserved10GiBfloor');ck(git(['rev-parse','HEAD']).decode().strip()==H,'finalMain unchanged');ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'no numericalimports');out={'schema_version':1,'decision':'ACCEPTED_EXACT_INTERMEDIATE_SOURCE_PARENT_LOCAL_SELECTION_PENDING_ACTUAL_REMOTE','checks':len(checks),'selection_sha256':sha(raw),'selected_commit':H,'selected_count':116,'selected_logical_bytes':3924686,'expected_git_operations':243,'effective_maximum_rows':506,'source':'d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0','capture_sha256':sha(read(C/'CAPTURE01.json')),'archives':cap['archives'],'complete_review_regular_closures':review_closures,'disk_free_bytes':free,'fresh_namespace_absent':True,'actual_remote_or_flat_recovery':False,'runtime_native_final_release_authority':False,'joined':joined};(O/'READBACK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['joined','complete_review_regular_closures']},indent=2))
