import hashlib,json,os,stat,subprocess,sys
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;MAIN=Path.cwd();A=F/'financial-genuine-wrapper-root-auxiliary-adoption01-2026-10-03';G=F/'financial-genuine-wrapper-auxiliary-preparation01-2026-10-03/generated02';S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-native-20261003-01/source');H='868bfa6404a2c34d6e5b6e0932a2baf4b38eb370';BASE='44bf99d199acae5a043cf5b472a53e2fcf4caf1b';checks=[];sha=lambda b:hashlib.sha256(b).hexdigest()
def ck(v,m):
 assert v,m
 checks.append(m)
def read(p):
 s=p.lstat();ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2 and p.resolve()==p,'bounded immutable file');fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW);parts=[];total=0
 try:
  ck(os.fstat(fd)==s,'opened identity')
  while True:
   b=os.read(fd,65536)
   if not b:break
   total+=len(b);ck(total<=4*1024**2,'file extent');parts.append(b)
  ck(total==s.st_size and os.fstat(fd)==s and p.lstat()==s,'stable body');return b''.join(parts)
 finally:os.close(fd)
def doc(p):return json.loads(read(p))
def git(args,data=None):
 env={'PATH':'/usr/bin:/bin','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_NO_REPLACE_OBJECTS':'1','GIT_NO_LAZY_FETCH':'1','GIT_TERMINAL_PROMPT':'0','GIT_OPTIONAL_LOCKS':'0'};r=subprocess.run(['git','--no-replace-objects','-c','protocol.allow=never','-C',str(S),*args],input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,env=env);ck(r.returncode==0 and len(r.stdout)<=8*1024**2 and len(r.stderr)<=65536,'bounded read-only Git '+args[0]);return r.stdout

A=F/'financial-genuine-wrapper-root-expectation-adoption01-2026-10-03'
def frozen(name,pin):
 d=F/name;b=read(d/'MANIFEST01.json');ck(sha(b)==pin,'pinned independent evidence manifest');m=json.loads(b);expected={r['path'] for r in m['members']};actual={str(p.relative_to(d)) for p in d.rglob('*')};ck(actual==expected|{'MANIFEST01.json'},'complete frozen membership')
 for r in m['members']:
  p=d/r['path'];s=p.lstat();ck(r['kind']=='file' and stat.S_ISREG(s.st_mode) and stat.S_IMODE(s.st_mode)==r['mode'],'frozen type mode');b=read(p);ck(len(b)==r['bytes'] and sha(b)==r['sha256'],'frozen body hash')
 return d
P=frozen('financial-genuine-wrapper-installed-auxiliary-review01-2026-10-03','01c86798a19194f5f6ab3fbc7d8ea16fb8b47614c69f59e5893365d7374ddf63')
E=frozen('financial-genuine-wrapper-runtime-expectation-review01-2026-10-03','15a922fe02a11e89882b9cda6871eb7b05a7166eed2256a3ab0c363044e9772a')
prior=doc(P/'READBACK01.json');ad=doc(A/'ADOPTION01.json');mapping=doc(A/'CURRENT_SOURCE_MAP01.json');rows={r['path']:r for r in mapping['rows']};baseline={r['path']:r for r in prior['joined']}
ck(git(['rev-parse','HEAD']).decode().strip()==ad['actual_current_source']==mapping['current_source']==H,'current HEAD receipt map')
parents=[l.split()[1].decode() for l in git(['cat-file','-p',H]).splitlines() if l.startswith(b'parent ')];ck(parents==[BASE] and ad['prior_source']==BASE,'direct parent44')
ck(all(not os.path.lexists(S/n) for n in ['.git/objects/info/alternates','.git/info/grafts','.git/refs/replace']),'no alternate source roots')
def tree(rev):
 out={}
 for entry in git(['ls-tree','-r','-z',rev]).split(b'\0'):
  if not entry:continue
  meta,name=entry.split(b'\t');mode,typ,oid=meta.decode().split();ck(typ=='blob' and mode in ('100644','100755'),'committed regular blob');out[name.decode()]={'git_mode':mode,'oid':oid}
 return out
old=tree(BASE);current=tree(H);new='fixture_inputs/financial_wrapper_expectation01/environment.json';pin='1ff7418a2b7c77300aea731cea5bba78277d323241ac0ec59f41f43207c66d87'
ck(len(old)==242 and set(old)==set(baseline) and all(current.get(n)==old[n] for n in old),'all242 unchanged committed modes and OIDs');ck(set(current)==set(old)|{new} and len(current)==243 and set(rows)==set(current),'exact243 only expectation addition');actual=set()
for root,ds,fs in os.walk(S,followlinks=False):
 if Path(root)==S:ds.remove('.git')
 for n in ds:ck(stat.S_ISDIR((Path(root)/n).lstat().st_mode),'directory no redirect')
 actual.update(str((Path(root)/n).relative_to(S)) for n in fs)
ck(actual==set(current),'full live file membership exact');reply=git(['cat-file','--batch'],(''.join(current[n]['oid']+'\n' for n in sorted(current))).encode());offset=0;joined=[]
for n in sorted(current):
 end=reply.index(b'\n',offset);oid,typ,size=reply[offset:end].decode().split();size=int(size);b=reply[end+1:end+1+size];offset=end+size+2;r=rows[n]
 ck(typ=='blob' and oid==current[n]['oid']==r['git_object'] and reply[offset-1:offset]==b'\n' and hashlib.sha1(b'blob '+str(size).encode()+b'\0'+b).hexdigest()==oid,'full actual committed body OID join')
 ck(read(S/n)==b and sha(b)==r['sha256'] and len(b)==r['bytes'] and stat.S_IMODE((S/n).lstat().st_mode)==r['mode'] and r['git_mode']==current[n]['git_mode']==('100755' if r['mode']&0o111 else '100644'),'map installed bytes modes Git')
 if n in baseline:ck(all(r[k]==baseline[n][k] for k in ['sha256','bytes','mode','git_mode']),'historical242 unchanged accepted bytes')
 joined.append(dict(r))
ck(offset==len(reply),'complete batch framing');b=read(S/new);ck(sha(b)==pin==ad['exact_historical_expectation_sha256']==mapping['environment_input']['sha256'],'expected new body pin');ck(b==read(F/'financial-genuine-wrapper-runtime-expectation-investigation01-2026-10-03/prepared01/environment.EXPECTATION.json'),'exact accepted historical prepared origin')
D=S/'fixture_inputs/financial_wrapper_draft01';env=doc(D/'environment.DRAFT.json');ck(all(env[k] is None for k in ['cuda_available','cuda_build','torch_version']),'original3NULL draft unchanged');draft=doc(D/'DRAFT01.json');ck(len(draft['slots'])==18 and all(not s['admitted'] and s['actual_outcome'] is None for s in draft['slots']),'18unreserved draft slots');ck(mapping['registered_role_map'] is None and mapping['actual_live_Torch_equality'] is None,'current map unresolved fields honest');ck(sum(n.startswith('tradingagents/') for n in current)==149 and sum(r['role']=='implementation' for r in baseline.values())==194,'149package194implementation retained');ck(git(['status','--porcelain','--untracked-files=all'])==b'' and git(['rev-parse','HEAD']).decode().strip()==H,'final stable clean source');ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'no numerical imports')
out={'schema_version':1,'decision':'ACCEPTED_INSTALLED_HISTORICAL_EXPECTATION_SOURCE_CAPTURE_ELIGIBILITY_ONLY','current_source':H,'parent':BASE,'checks':len(checks),'tracked':243,'unchanged_prior_tracked':242,'implementation':194,'package':149,'auxiliary':49,'expectation_sha256':pin,'adoption_sha256':sha(read(A/'ADOPTION01.json')),'current_map_sha256':sha(read(A/'CURRENT_SOURCE_MAP01.json')),'live_Torch_equality':None,'registration_budget_execution_authority':False,'new_full_capture_required':True,'joined':joined};(O/'READBACK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='joined'},indent=2))
