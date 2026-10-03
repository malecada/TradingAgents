"""Bounded offline byte-copy recipe. No admission, numeric import or execution."""
import argparse,ast,copy,hashlib,json,os,stat,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
MAIN=HERE.parents[3]
FS=HERE.parent
CAP=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source')
HEAD='d443208795f59292c156c5b81b687594efacea4d'
CHANGE='tradingagents/research/onchain_replication/original_dictionary.py'
OLD='cbe571a3758695b2ff63a45031c90840a7358538f9a2c0bad31077db8439a6d9'
NEW='e05aa225b6bcf8f4e14a644d0a03f2a9aff6cb36ae4a5b02a3dded72d94580b9'
CASES={'success':'original-import-held-success-20261003-01','second_target_publication_failure':'original-import-held-publication-failure-20261003-01'}
ROLES=('runtime','software_environment','native_environment','native_policy','original_import_index','original_evidence','matching','target_catalog','case_contract','registration','budget_extension','budget_review','charter','budget_allocation','auxiliary_sources')
LIMIT=4*1024**2

def require(ok,msg):
 if not ok:raise ValueError(msg)
def sha(b):return hashlib.sha256(b).hexdigest()
def encode(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n'
def read(p):
 p=Path(p);s=p.lstat();require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=LIMIT,'regular bounded single-link body required')
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  before=os.fstat(fd);b=os.read(fd,LIMIT+1);after=os.fstat(fd)
  require((s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns) and len(b)==s.st_size,'stable body read');return b
 finally:os.close(fd)
def write(p,b,mode=0o600):
 require(len(b)<=LIMIT,'output bound');p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 os.chmod(p,mode)
def git(*args):
 # Fixed local objects only; no fetch, network protocol, shell or hook invocation.
 env=os.environ.copy();env.update(GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0',GIT_CONFIG_NOSYSTEM='1')
 r=subprocess.run(['git','-c','protocol.allow=never','-C',str(CAP),*args],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=15)
 require(r.returncode==0 and len(r.stdout)<=LIMIT and len(r.stderr)<=LIMIT,'bounded local Git read');return r.stdout

def expectations():
 raw=read(HERE/'SOURCE_EXPECTATIONS02.json');require(sha(raw)=='e7ba2f536d8783f380db41922af04e030a680258bb87ed918648a0c57d89d436','frozen complete recipe expectations changed');return json.loads(raw)
def one_change(before,after):
 expected=expectations()
 require(type(before) is dict and type(after) is dict and len(before)==len(after)==199,'exact199 implementation entries required')
 require(sum(k.startswith('tradingagents/') for k in before)==148 and sum(k.startswith('tradingagents/') for k in after)==148,'exact148 package entries required')
 require(before==expected['baseline'] and after==expected['candidate'],'exact complete authenticated source maps required')
 require([k for k in sorted(before) if before[k]!=after[k]]==[CHANGE],'exact one body changed')
 require(before[CHANGE]==OLD and after[CHANGE]==NEW,'exact reviewed source replacement')
def draft_case(exp,case):
 d=copy.deepcopy(exp)
 d['charter']=None;d['cumulative_budget_extension']=None;d['parent']=None
 return {'status':'DRAFT_NOT_RELEASED','case':case,'fresh_identity':None,'source_commit':None,'design_source':None,'registration_commit':None,'capsule_root':None,'experiment':d,'roles':dict.fromkeys(ROLES),'caller':None,'independent_review':None,'full_recovery':None,'dependent_success_evidence':None,'cumulative_allocation':None}
def release(_):raise ValueError('source recipe is never execution authority; genuine Root gate, cumulative amendment, allocation, source/input/runtime review and recovery required')

def build():
 out=HERE/'generated01';require(not out.exists(),'never replace prior generated output');require(os.statvfs(HERE).f_bavail*os.statvfs(HERE).f_frsize>=10*1024**3,'10GiB disk floor')
 require(git('rev-parse','HEAD').decode().strip()==HEAD,'original closed HEAD changed')
 gate_raw=read(CAP/'held-fixture-registration01.json');gate=json.loads(gate_raw)
 e=gate['experiments'][CASES['success']];aux=json.loads(read(CAP/'held-auxiliary-success01.json'))
 exclude={x['reference']['path'] for x in aux['entries']}|{'held-auxiliary-success01.json'}
 baseline={k:v for k,v in e['source_files'].items() if k not in exclude}
 require(len(baseline)==199 and sum(k.startswith('tradingagents/') for k in baseline)==148,'actual199/148 closure')
 candidate=dict(baseline);candidate[CHANGE]=NEW;one_change(baseline,candidate)
 tree={}
 for row in git('ls-tree','-rz',HEAD).split(b'\0'):
  if not row:continue
  meta,name=row.split(b'\t');mode,kind,oid=meta.decode().split();require(kind=='blob','tracked regular blobs only');tree[name.decode()]=(mode,oid)
 origins={};copies={}
 def preserve(p,relative=None):
  raw=read(p);key=relative or str(p.relative_to(FS));target=out/'evidence'/key
  if key not in copies:write(target,raw);copies[key]=sha(raw)
  origins[str(p)]={'sha256':sha(raw),'bytes':len(raw),'copy':str(target.relative_to(out))};return raw
 fatal=FS/'held-consumer-canonical-fatal-supplement01-2026-10-03'
 canonical=FS/'held-consumer-canonical-successor-preparation01-2026-10-03'
 new=preserve(fatal/'original_dictionary.py');require(sha(new)==NEW,'reviewed successor body')
 old=preserve(canonical/'baseline.py');canon=preserve(canonical/'original_dictionary.py');require(sha(old)==OLD and sha(canon)=='93c0cd1ae882d51df185458ce7304a46dfb66dc7ca337285039541fa70176e88','original/canonical joins')
 inv=json.loads(preserve(fatal/'INVERSE01.json'));require(new.count(inv['new_text'].encode())==1 and new.replace(inv['new_text'].encode(),inv['old_text'].encode())==canon,'full fatal inverse')
 # Independently restore the sole membership slice, without importing numerical code.
 def membership(raw):
  t=ast.parse(raw);f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='validate')
  a=next(i for i,n in enumerate(f.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='indices')
  z=next(i for i,n in enumerate(f.body) if i>a and isinstance(n,ast.Expr) and 'repeated representative' in ast.unparse(n));return t,f,a,z
 ot,of,a,z=membership(old);nt,nf,b,w=membership(canon)
 lines=canon.decode().splitlines(keepends=True);lines[nf.body[b].lineno-1:nf.body[w].end_lineno]=old.decode().splitlines(keepends=True)[of.body[a].lineno-1:of.body[z].end_lineno]
 require(''.join(lines).encode()==old,'full canonical byte inverse')
 nf.body[b:w+1]=copy.deepcopy(of.body[a:z+1]);require(ast.dump(nt)==ast.dump(ot),'whole other canonical AST inverse')
 for folder,names in [('held-consumer-canonical-successor-review01-2026-10-03',['REVIEW01.md','MANIFEST01.json','LIMITATIONS01.json']),('held-consumer-canonical-fatal-supplement-review01-2026-10-03',['REVIEW01.md','MANIFEST01.json','READBACK01.json']),('held-consumer-post-outcome-actual-preservation-review01-2026-10-03',['ACTUAL_RECOVERY_REVIEW03.md','MANIFEST03.json','ACTUAL_RECOVERY_REVIEW03.json'])]:
  for name in names:preserve(FS/folder/name)
 for p in [fatal/'MANIFEST02.json',canonical/'MANIFEST01.json',canonical/'check01.py']:preserve(p)
 pins=json.loads(read(HERE/'REVIEW_PINS01.json'))
 for rel,pin in pins.items():require(sha(read(FS/rel))==pin,'exact review pin')
 inventory=[]
 for name in sorted(baseline):
  raw=read(CAP/name);require(sha(raw)==baseline[name],'actual baseline source hash');mode,oid=tree[name]
  require(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==oid,'actual Git blob hash')
  require((int(mode,8)&0o111)==(CAP/name).stat().st_mode&0o111,'actual executable mode')
  picked=new if name==CHANGE else raw
  write(out/'baseline'/name,raw,stat.S_IMODE((CAP/name).stat().st_mode));write(out/'candidate'/name,picked,stat.S_IMODE((CAP/name).stat().st_mode))
  inventory.append({'path':name,'git_commit':HEAD,'baseline_git_oid':oid,'git_mode':mode,'physical_mode':stat.S_IMODE((CAP/name).stat().st_mode),'baseline_sha256':sha(raw),'candidate_sha256':sha(picked),'baseline_bytes':len(raw),'candidate_bytes':len(picked),'candidate_git_blob_oid':hashlib.sha1(b'blob '+str(len(picked)).encode()+b'\0'+picked).hexdigest()})
 # Inputs are opaque, including original samples/dictionary and NPY bodies.
 input_copies={};drafts={}
 for case,identity in CASES.items():
  exp=gate['experiments'][identity];require(len(exp['inputs'])==33,'original33 input roles')
  d=draft_case(exp,case);rootpath='fixture_inputs/held/'+case+'01/'
  for role,ref in exp['inputs'].items():
   raw=read(CAP/ref['path']);require(sha(raw)==ref['sha256'],'original opaque input join')
   if ref['path'] not in input_copies:write(out/'input-baseline'/ref['path'],raw);input_copies[ref['path']]={'sha256':sha(raw),'bytes':len(raw)}
  # Two root-specific documents must be rerendered after Root chooses a fresh capsule.
  job=json.loads(read(CAP/exp['inputs']['execution_job']['path']));job['resources']['disk_paths']=[None];job['resources']['storage_budget']['root']=None
  workspace=dict.fromkeys(('root','ledger','artifacts','git_common'))
  for role,document in [('execution_job',job),('execution_workspace',workspace)]:
   raw=encode(document);path=exp['inputs'][role]['path'];write(out/'input-draft'/path,raw);d['experiment']['inputs'][role]['sha256']=sha(raw)
  # Strip all inherited authority source pins; Root must add newly reviewed auxiliary bodies.
  d['experiment']['source_files']=candidate
  for role in ('runtime','software_environment','native_environment','native_policy','original_import_index','original_evidence','matching','target_catalog'):
   p=CAP/'fixture_inputs/held/roles01'/str(role+'.json');raw=read(p);write(out/'role-baseline'/case/str(role+'.json'),raw)
   d['roles'][role]={'historical_reference':{'path':str(p.relative_to(CAP)),'sha256':sha(raw),'bytes':len(raw)},'future_reference':None,'status':'REQUIRES_ROOT_REBIND_OR_REVALIDATE'}
  d['unchanged_input_roles']=sorted(set(exp['inputs'])-{'execution_job','execution_workspace'});d['case_contract']=None;d['outputs']=exp['outputs'];drafts[case]=d
 # Original C6 source provenance: claim metadata only; no payload parsing.
 claim=json.loads(read(CAP/'fixture_inputs/original/08-claim.json'))
 provenance={'claim_sha256':sha(read(CAP/'fixture_inputs/original/08-claim.json')),'original_source':'c6b568d4b1c177ab94ac37fbad462c2decc721c0','claim_metadata_keys':sorted(claim)}
 require(claim['source']==provenance['original_source'] and len(claim['experiment']['source_files'])==26,'original C6/26-source claim metadata')
 provenance['source_objects']=[]
 for name,pin in sorted(claim['experiment']['source_files'].items()):
  raw=git('show',claim['source']+':'+name);require(sha(raw)==pin,'original C6 source body hash');write(out/'original-c6-source'/name,raw)
  provenance['source_objects'].append({'path':name,'sha256':pin,'bytes':len(raw),'git_oid':hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()})
 write(out/'SOURCE_MAP01.json',encode({'baseline_commit':HEAD,'implementation_count':199,'package_count':148,'changed_count':1,'unchanged_count':198,'entries':inventory}))
 write(out/'INPUT_BASELINE01.json',encode(input_copies));write(out/'DRAFT_CASES01.json',encode(drafts));write(out/'ORIGINS01.json',encode(origins));write(out/'ORIGINAL_PROVENANCE01.json',encode(provenance))
 write(out/'GATE_HISTORICAL.json',gate_raw)
 return {'status':'DRAFT_NOT_RELEASED','implementation_count':199,'package_count':148,'one_changed_body':CHANGE,'unchanged_bodies':198,'historical_baseline_commit':HEAD,'future_source_commit':None,'future_registration_commit':None,'future_budget':None,'paper_credit':0}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--release',action='store_true');a=p.parse_args()
 if a.release:release(None)
 else:print(json.dumps(build(),sort_keys=True))
