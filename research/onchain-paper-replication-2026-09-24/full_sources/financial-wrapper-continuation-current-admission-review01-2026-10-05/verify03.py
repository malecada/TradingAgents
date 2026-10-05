from pathlib import Path
import ast,email,hashlib,importlib.metadata,json,os,stat,subprocess,sys,time
D=Path(__file__).resolve().parent;F=D.parent;ROOT=F.parents[2];CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');P=CAP.parent.parent/'genuine-financial-wrapper-continue100-compatibility-root-launch-20261005-01';C=F/'heartbeat-root-checkpoint10-2026-10-04';sys.path.insert(0,str(P));import recovery04 as R
SOURCE='664e2ca5fa11d6640ab79f64c5aa222aeb3a9128';OLD='32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41';pins={};checks=[];start=time.monotonic()
def ck(n,v):assert v,n;checks.append(n)
def runtime_metadata(p):
 p=Path(p);ck('runtime metadata canonical',p.name=='METADATA' and p.resolve()==p and p.is_relative_to(Path(sys.prefix)/'lib/python3.13/site-packages'))
 before=R.sig(p.lstat());ck('runtime metadata finite regular',stat.S_ISREG(p.lstat().st_mode) and p.stat().st_size<=R.FILE);fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  ck('runtime descriptor',R.sig(os.fstat(fd))==before);parts=[];size=0
  while True:
   b=os.read(fd,65536)
   if not b:break
   size+=len(b);ck('runtime metadata extent',size<=before[4]);parts.append(b)
  ck('runtime metadata stable',R.sig(os.fstat(fd))==before==R.sig(p.lstat()));result=b''.join(parts)
 finally:os.close(fd)
 ck('runtime metadata afterclose',R.sig(p.lstat())==before);return result
def read(p):
 p=Path(p);b=runtime_metadata(p) if p.name=='METADATA' else R.read(p.parent,p.name);pin=(R.sig(p.lstat()),R.digest(b));ck('unchanged reread '+str(p),p not in pins or pins[p]==pin);pins[p]=pin;return b
def obj(p):return json.loads(read(p))
def ref(r):
 b=read(Path(r['path']));ck('reference '+r['path'],R.digest(b)==r['sha256']);return json.loads(b)
def git(*args):return subprocess.run(['git','-C',str(CAP),*args],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30).stdout
q=obj(P/'REQUEST_DRAFT01.json');install=obj(C/'CONTINUATION_PARENT_INSTALL01.json');m=obj(C/'CONTINUATION_SOURCE_MANIFEST01.json');adoption=obj(C/'CONTINUATION_CAPSULE_ADOPTION01.json')
ck('source current design',q['source']==q['design_source']==m['source']==SOURCE and git('rev-parse','HEAD').decode().strip()==SOURCE)
ck('Root install bytes',R.digest(read(P/'parent01.py'))==q['caller_sha256']==install['caller_sha256']=='b50d1e727979a989f3da1e18a5b204cc3d29169ad425806e8550aa88af5ed0be')
ck('Root draft original',R.digest(read(P/'REQUEST_DRAFT01.json'))==install['request_sha256']);ck('unreleased',q['final_review'] is None)
for n,pin in q['helper_hashes'].items():ck('helper '+n,R.digest(read(P/n))==pin==install['helper_hashes'][n])
ck('source manifest map',q['source_files']==m['source_files'] and len(m['source_files'])==359 and m['tracked_count']==360)
def tree(commit):
 result={}
 for row in git('ls-tree','-rz',commit).split(b'\0'):
  if row:
   header,name=row.split(b'\t');mode,kind,oid=header.decode().split();ck('regular Git '+name.decode(),mode in ('100644','100755') and kind=='blob');result[name.decode()]=(mode,oid)
 return result
new=tree(SOURCE);old=tree(OLD);ck('355 original bodies retained in Git',len(old)==355 and all(new.get(n)==v for n,v in old.items()));ck('complete360 map',set(new)==set(q['source_files'])|{q['registration']})
for n,(mode,oid) in new.items():
 b=read(CAP/n);ck('working/Git body '+n,hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid);ck('Git executable class '+n,bool((CAP/n).stat().st_mode&0o111)==(mode=='100755'))
 if n in q['source_files']:ck('source pin '+n,R.digest(b)==q['source_files'][n])
g= obj(CAP/q['registration']);ck('registration',R.digest(read(CAP/q['registration']))==q['registration_sha256']);exp=g['experiments'][q['identity']];ck('29 current roles',len(exp['inputs'])==29 and q['input_hashes']=={k:v['sha256'] for k,v in exp['inputs'].items()})
for role,r in exp['inputs'].items():ck('input '+role,R.digest(read(CAP/r['path']))==r['sha256'])
prep=F/'financial-wrapper-continuation-parent-preparation01-2026-10-05';draft=obj(prep/'GATE4_DRAFT01.json')
for identity in (q['identity'],'financial-wrapper-classification-eager-predict-compatibility-20261004-01'):draft['experiments'][identity]['source_files']=q['source_files']
ck('exact reviewed4 gate',draft==g);ck('original13 unchanged',R.digest(read(CAP/'fixture_inputs/financial_wrapper_compatibility01/gates.json'))=='e1846c9fbd5d1964c867c9c7027e3e9a6009520c07841ed720c035374dbeb806')
rt=json.loads(read(CAP/exp['inputs']['runtime_mapping']['path']));ck('runtime full map',rt==q['runtime_mapping']);ck('runtime identity',sys.executable==rt['executable'] and sys.prefix==rt['prefix'] and sys.version.split()[0]==rt['python']=='3.13.13');ck('interpreter',Path(sys.executable).resolve()==Path(rt['resolved_executable']) and R.digest(R.read(Path(rt['resolved_executable']).parent,Path(rt['resolved_executable']).name,64*1024**2))==rt['executable_sha256']);ck('lock',R.digest(read(CAP/'uv.lock'))==rt['lock_sha256'])
seen=set()
for row in rt['distribution_records']:
 p=Path(row['record']);ck('installed RECORD scope',p.is_relative_to(Path(sys.prefix)/'lib/python3.13/site-packages') and p.name=='RECORD' and p.parent.name.endswith('.dist-info'));ck('RECORD '+row['name'],R.digest(read(p))==row['record_sha256']);metadata=email.message_from_bytes(read(p.parent/'METADATA'));norm=lambda s:s.lower().replace('_','-').replace('.','-');ck('direct installed name/version '+row['name'],norm(metadata['Name'])==norm(row['name']) and metadata['Version']==row['version'] and row['name'] not in seen);seen.add(row['name']);ck('default metadata version '+row['name'],importlib.metadata.version(row['name'])==row['version'])
ck('251 unique',len(seen)==251)
contract=ref(install['required_metadata_proof_field']['continuation_trusted_proof_contract']);ck('contract current',contract['current_source']==SOURCE);recovery=ref(contract['outcome_recovery']);review=ref(recovery['review']);ck('actual100 recovered',recovery['source']==OLD and recovery['decision']=='accepted-actual-complete100-byte-recovery' and review['decision']=='ACCEPTED_ACTUAL_COMPATIBILITY_COMPLETE100_BYTE_RECOVERY')
history=[]
for directory in sorted((CAP/'research_runs').iterdir()):
 if directory.name=='.lock':continue
 claim=obj(directory/'claim.json');terminalnames=[x for x in ('failed.json','complete.json') if (directory/x).exists()];ck('one terminal '+directory.name,len(terminalnames)==1);term=obj(directory/terminalnames[0]);ck('claim identity '+directory.name,claim['experiment_id']==term['experiment_id']==directory.name and term['claim_sha256']==R.digest(read(directory/'claim.json')) and claim['program_id']==g['program_id']);history.append({'identity':directory.name,'claim_sha256':R.digest(read(directory/'claim.json')),'terminal_sha256':R.digest(read(directory/terminalnames[0])),'status':term['status'],'effective_attempt_budget':claim['effective_attempt_budget']})
ck('actual1complete3failed',len(history)==4 and sum(x['status']=='complete' for x in history)==1 and sum(x['status']=='failed' for x in history)==3 and max(x['effective_attempt_budget'] for x in history)==20)
extension=exp['cumulative_budget_extension'];ext=ref({'path':str(CAP/extension['extension']['path']),'sha256':extension['extension']['sha256']});exreview=ref({'path':str(CAP/extension['review']['path']),'sha256':extension['review']['sha256']});allocation=ref({'path':str(CAP/ext['allocation']['path']),'sha256':ext['allocation']['sha256']});ck('base18 cumulative20',ext['cumulative_ceiling']==20 and ext['base_family']==g['families'][exp['family']] and ext['base_family']['attempt_budget']==18 and ext['base_family']['prior_attempts']==0)
for p in (P/'attempt',CAP/'research_runs'/q['identity'],CAP/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/q['identity']):ck('fresh '+str(p),not os.path.lexists(p))
oldmeta=obj(F/'financial-wrapper-compatibility-final-source-runtime-bridge02-2026-10-04/SOURCE_INPUT_RUNTIME_PROOF01.json')
# Fixed immutable accepted refs remain source-pinned; authenticate their bodies without repeating their reviews.
for r in oldmeta['compatibility_preclaim_external_refs'].values():ck('external opaque '+r['path'],R.digest(read(Path(r['path'])))==r['sha256'])
ck('no numerical or project imports',not any(n in sys.modules for n in ('numpy','torch','pandas')) and not any(n.startswith('tradingagents') for n in sys.modules))
for p,(sig,digest) in tuple(pins.items()):ck('final body '+str(p),R.digest(runtime_metadata(p) if p.name=='METADATA' else R.read(p.parent,p.name))==digest and R.sig(p.lstat())==sig)
ck('finalHEAD',git('rev-parse','HEAD').decode().strip()==SOURCE);ck('bounded actual review',time.monotonic()-start<120)
result={'source':SOURCE,'identity':q['identity'],'checks':len(checks),'history':history,'runtime_records':len(seen),'proof_contract':install['required_metadata_proof_field']['continuation_trusted_proof_contract'],'external_refs':oldmeta['compatibility_preclaim_external_refs'],'request_sha256':R.digest(read(P/'REQUEST_DRAFT01.json')),'registration':q['registration'],'registration_sha256':q['registration_sha256'],'caller_sha256':q['caller_sha256'],'runtime_mapping_sha256':exp['inputs']['runtime_mapping']['sha256'],'actual100_recovery':contract['outcome_recovery'],'admission_executed':False,'numerical_authority':False}
(D/'READBACK01.json').write_bytes(R.encode(result));(D/'BODY_PINS01.json').write_bytes(R.encode({str(p):{'signature':list(v[0]),'sha256':v[1]} for p,v in pins.items()}));print(json.dumps({'checks':len(checks),'bodies':len(pins)}))
