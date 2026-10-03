import ast,hashlib,json,os,stat,subprocess,sys
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;repo=Path.cwd();A=F/'financial-genuine-wrapper-preparation02-2026-10-03';I=F/'financial-genuine-wrapper-root-admission-investigation01-2026-10-03';S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-native-20261003-01/source');checks=[];sha=lambda b:hashlib.sha256(b).hexdigest()
def ck(v,m):
 assert v,m
 checks.append(m)
def read(p):
 s=p.lstat();ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2,'regular bounded '+str(p));fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  b=os.read(fd,4*1024**2+1);ck(os.fstat(fd)==s and p.lstat()==s and len(b)==s.st_size,'stable read '+str(p));return b
 finally:os.close(fd)
def doc(p,pin=None):
 b=read(p);ck(pin is None or sha(b)==pin,'pin '+p.name);return json.loads(b)
def git(args,data=None):
 r=subprocess.run(['git','--no-replace-objects','-C',str(S),*args],input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,env={'PATH':'/usr/bin:/bin','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_NO_REPLACE_OBJECTS':'1','GIT_OPTIONAL_LOCKS':'0'});ck(r.returncode==0 and len(r.stdout)<=8*1024**2 and len(r.stderr)<=65536,'bounded readonly Git '+args[0]);return r.stdout
c=doc(F/'financial-genuine-wrapper-root-source-composition01-2026-10-03/COMPOSITION01.json');delta=doc(I/'FILE_DELTA01.json','b9b88782ff5314fa200b40558df831fab98ddb2c430716cdecfecabb96c9acfc');closure=doc(A/'SOURCE_CLOSURE01.json');installation=doc(A/'INSTALLATION01.json');head=git(['rev-parse','HEAD']).decode().strip();ck(head==c['source_commit']=='390c82a9958e135c24bcca80f3a636313ca27932','actual fixed committed HEAD');rows=delta['rows'];targets={r['target'] for r in rows};ck(len(rows)==len(targets)==194 and set(closure['installed'])==targets==set(installation['sources']),'complete recipe/acceptedclosure')
actual=set();dirs=[]
for root,ds,fs in os.walk(S,followlinks=False):
 if Path(root)==S:ds.remove('.git')
 for n in ds:ck(stat.S_ISDIR((Path(root)/n).lstat().st_mode),'no symlink directory');dirs.append(str((Path(root)/n).relative_to(S)))
 for n in fs:actual.add(str((Path(root)/n).relative_to(S)))
ck(actual==targets,'exact actual194 members excluding Git metadata');ck(sum(n.startswith('tradingagents/') for n in actual)==149,'exact149package');ck('tradingagents/research/onchain_replication/held_score_consumer.py' not in actual,'no heldextra')
entries={}
for item in git(['ls-tree','-r','-z',head]).split(b'\0'):
 if not item:continue
 meta,path=item.split(b'\t');mode,typ,oid=meta.decode().split();ck(typ=='blob','committed regular blob');entries[path.decode()]={'git_mode':mode,'oid':oid}
ck(set(entries)==targets,'complete exact committed194')
objects=git(['cat-file','--batch'],(''.join(entries[n]['oid']+'\n' for n in sorted(targets))).encode());offset=0;joined=[]
for n in sorted(targets):
 e=entries[n];end=objects.index(b'\n',offset);oid,typ,size=objects[offset:end].decode().split();size=int(size);body=objects[end+1:end+1+size];offset=end+size+2;ck(oid==e['oid'] and typ=='blob' and objects[offset-1:offset]==b'\n','exact batch framing');ck(hashlib.sha1(b'blob '+str(size).encode()+b'\0'+body).hexdigest()==oid,'actual Git object content OID');r=next(r for r in rows if r['target']==n);b=read(S/n);origin=read(repo/r['origin']);s=(S/n).lstat();ck(b==body==origin and len(b)==r['candidate_bytes'] and sha(b)==r['candidate_sha256']==closure['installed'][n]==installation['sources'][n]['sha256'],'actual committed/source/origin/hash '+n);ck(stat.S_IMODE(s.st_mode)==r['candidate_mode'] and e['git_mode']==('100755' if r['candidate_mode']&0o111 else '100644'),'original filesystem and Gitmode '+n);ck(installation['sources'][n]['source']==r['origin'],'exact accepted origin');ast.parse(b,filename=n);joined.append({'path':n,'origin':r['origin'],'mode':stat.S_IMODE(s.st_mode),'bytes':len(b),'sha256':sha(b),**e})
ck(offset==len(objects),'no extra batch bytes');ck(sum(r['bytes'] for r in joined)==1999747,'exact totalbytes');ck(c['installed_source_rows']==[{k:r[k] for k in ('bytes','mode','origin','path','sha256')} for r in joined],'exact rootreceipt rows')
for name,baseline in [('job.py','job.baseline.py'),('replay.py','candidate02/replay.py')]:
 text=read(S/'tradingagents/research/onchain_replication'/name).decode();adapt=doc(A/'adaptations.json')[name]
 for item in reversed(adapt):
  ck(text.count(item['after'])==item.get('count',1),'exact inverse hunk '+name);text=text.replace(item['after'],item['before'])
 ck(text.encode()==read(A/baseline),'full installed conditional inverse '+name)
configs={}
for name,pin in [('model.json','20f451c08143dd81491b5c9fa0a90243ee6a9363df1fbbfcbd9c45b32f9b054d'),('training.json','d5276b75491e130bd03d43de28120f72dd792e42af4446382a6c127d387b8ec0')]:
 b=read(A/name);ck(sha(b)==pin and b==read(repo/'research/onchain-paper-replication-2026-09-24/config'/name),'unchanged actual method configuration');configs[name]=pin
ck(git(['rev-parse','HEAD']).decode().strip()==head,'unchanged sourceHEAD');ck(git(['status','--porcelain','--untracked-files=all'])==b'','clean installedsource');ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'no numerical imports')
output={'decision':'ACCEPTED_SOURCE_INSTALLED194_ONLY_NOT_ADMITTED','checks':len(checks),'source_root':str(S),'source_commit':head,'composition_sha256':sha(read(F/'financial-genuine-wrapper-root-source-composition01-2026-10-03/COMPOSITION01.json')),'delta_sha256':sha(read(I/'FILE_DELTA01.json')),'sources':194,'package':149,'nonpackage':45,'logical_bytes':1999747,'python_asts':194,'configs':configs,'joined':joined,'financial_slots_unreserved':18,'native_runtime_input_registration_caller_recovery_authority':False};(O/'READBACK01.json').write_text(json.dumps(output,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in output.items() if k!='joined'},indent=2))
