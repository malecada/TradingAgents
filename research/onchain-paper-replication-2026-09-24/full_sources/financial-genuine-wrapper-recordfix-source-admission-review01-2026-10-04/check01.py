import ast,hashlib,json,os,stat,subprocess,sys
from pathlib import Path
from types import SimpleNamespace
O=Path(__file__).resolve().parent;F=O.parent;M=Path.cwd();A=F/'financial-genuine-wrapper-root-recordfix-adoption01-2026-10-04';OLD=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-native-20261003-01/source');S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-native-20261004-01/source');H='649fb8a11089524aaef7843dffeeb90a3a55ca17';B='d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0';GATE='fixture_inputs/financial_wrapper_recordfix01/gates.json';PFX='fixture_inputs/financial_wrapper_recordfix01/';CHANGE='tradingagents/research/onchain_replication/financial_wrapper_fixture.py';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(x,m):
 assert x,m
 checks.append(m)
def read(p):
 st=p.lstat();ck(stat.S_ISREG(st.st_mode) and st.st_nlink==1 and st.st_size<=4194304 and p.resolve()==p,'bounded canonical regular source')
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  b=b''
  while len(b)<=st.st_size:
   q=os.read(fd,65536)
   if not q:break
   b+=q
  after=os.fstat(fd);ck(len(b)==st.st_size and (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'stable body');return b
 finally:os.close(fd)
def doc(p):return json.loads(read(p))
def git(root,args,data=None):
 z=subprocess.run(['git','--no-replace-objects','-c','protocol.allow=never','-C',str(root),*args],input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,env={'PATH':'/usr/bin:/bin','GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1','GIT_OPTIONAL_LOCKS':'0','GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1'});ck(z.returncode==0 and len(z.stdout)<=8*1024**2 and len(z.stderr)<=65536,'bounded readonly Git');return z.stdout
def tree(root,head):
 result={}
 for row in git(root,['ls-tree','-r','-z',head]).split(b'\0'):
  if not row:continue
  meta,n=row.split(b'\t');mode,kind,oid=meta.decode().split();ck(kind=='blob' and mode in ('100644','100755'),'regular tracked Git');result[n.decode()]=(mode,oid)
 return result
adoption=doc(A/'SOURCE_ADOPTION01.json');gate=doc(S/GATE);oldgate=doc(OLD/'fixture_inputs/financial_wrapper_registration01/gates.json');ID=adoption['fresh_identity'];e=gate['experiments'][ID]
ck(git(S,['rev-parse','HEAD']).decode().strip()==H and git(S,['rev-parse','HEAD^']).decode().strip()==B,'actual direct successor source')
ck(git(S,['status','--porcelain','--untracked-files=all'])==b'' and git(OLD,['rev-parse','HEAD']).decode().strip()==B,'new clean original immutable')
t=tree(S,H);old=tree(OLD,B);ck(len(t)==325 and len(old)==290 and set(old)<=set(t),'full325 old290 retained')
ck(set(e['source_files'])==set(t)-{GATE} and len(e['source_files'])==324 and e['source_files']==adoption['source_files'],'exact source closure324 no self hash')
ck(sha(read(S/GATE))==adoption['registration_sha256']=='4474df26460aab41281bfdcc311129b613a90d76963e853858841200d9faa69a','actual new gate pin')
changed=[];joined=[]
for n,(mode,oid) in t.items():
 b=read(S/n);st=(S/n).lstat();ck(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid and ('100755' if st.st_mode&0o111 else '100644')==mode,'every current body OID mode')
 if n in e['source_files']:ck(sha(b)==e['source_files'][n],'every current source pin')
 if n in old:
  ob=read(OLD/n);ck(hashlib.sha1(b'blob '+str(len(ob)).encode()+b'\0'+ob).hexdigest()==old[n][1],'original unchanged committed body')
  if b!=ob:changed.append(n)
  ck(mode==old[n][0],'old tracked modes preserved')
 else:ck(stat.S_IMODE(st.st_mode)==0o644 and mode=='100644','declared new support0644 mapping')
 joined.append({'path':n,'sha256':sha(b),'bytes':len(b),'mode':stat.S_IMODE(st.st_mode),'git_mode':mode,'git_oid':oid})
ck(changed==[CHANGE] and sha(read(S/CHANGE))=='e2d9208ac51fd5876b63b6a72f734fc4fedd28fa42ac9c7fa1014346feb8404c','exact one reviewed correction')
closure=doc(S/(PFX+'source_closure.json'));ck(len(closure['installed'])==194 and sum(n.startswith('tradingagents/') for n in closure['installed'])==149,'194implementation149package')
for n,h in closure['installed'].items():ck(sha(read(S/n))==h==e['source_files'][n],'all scientific closure bodies')
ck(len(gate['experiments'])==11 and all(gate['experiments'][n]==v for n,v in oldgate['experiments'].items()) and gate['families']==oldgate['families'],'all10 original gate definitions unchanged exact family')
family=gate['families'][e['family']];ck(family['attempt_budget']==18 and family['prior_attempts']==0 and 'cumulative_budget_extension' not in e,'unchanged18 budget0prior no extension')
for row in adoption['copied_metadata_support']:ck(read(S/row['path'])==read(Path(row['original_path'])) and sha(read(S/row['path']))==row['sha256'] and len(read(S/row['path']))==row['bytes'],'actual copied support origin')
for n,h in adoption['role_hashes'].items():ck(sha(read(S/n))==h,'all8role bodies')
for role,ref in e['inputs'].items():ck(ref['dataset']=='synthetic' and sha(read(S/ref['path']))==ref['sha256'],'all8 actual input bindings')
ck(sha(read(S/e['charter']['path']))==e['charter']['sha256'],'actual charter pin')
charter=doc(S/e['charter']['path']);oldcharter=doc(OLD/'fixture_inputs/financial_wrapper_registration01/CHARTER02.json');ck({k:v for k,v in charter.items() if k!='operational_source_correction'}==oldcharter,'entire original charter preserved with additive correction')
amend=doc(S/(PFX+'OPERATIONAL_AMENDMENT01.json'));ck(amend['defined_identity_count']==19 and amend['prospective_numerical_phase_count']==18 and amend['numerical_attempt_budget']==18 and amend['numerical_claims_before']==0 and amend['prior_attempts']==0 and amend['old_outer_is_numerical_claim'] is False and amend['spent_numerical_attempt_refund'] is False and amend['spent_numerical_attempt_transfer'] is False,'exact operational accounting distinction')
ck(amend['prospective_numerical_order']==[ID]+amend['original_order'][1:] and amend['preserved_identity_definitions']==amend['original_order']+[ID] and amend['permanently_reserved_original_outer']==amend['original_order'][0],'fixed fresh order original19definitions retained')
for field in ['independent_amendment_review','original_failed_scope_acceptance']:
 ref=amend[field];ck(sha(read(S/ref['path']))==ref['sha256'],'actual amendment reference '+field)
for ref in amend['original_failed_scope_full_recovery'].values():ck(sha(read(S/ref['path']))==ref['sha256'],'actual complete failed recovery prerequisite')
ck(doc(S/amend['original_failed_scope_acceptance']['path'])['decision']=='FAILED_SCOPE_BYTE_UNION_ACCEPTED','actual prerequisite verdict not invented')
for root in [OLD,S]:ck(not os.path.lexists(root/'research_runs') and not os.path.lexists(root/'research_artifacts'),'actual genuine zero claim namespace')
# Genuine readonly API calls from this exact isolated source; no Run/start/Owner or numerical modules.
sys.path.insert(0,str(S));os.chdir(S)
from tradingagents.research import admission
from tradingagents.research.onchain_replication import job,financial_wrapper_fixture
ck(Path(admission.__file__)==S/'tradingagents/research/admission.py' and Path(job.__file__)==S/'tradingagents/research/onchain_replication/job.py' and Path(financial_wrapper_fixture.__file__)==S/CHANGE,'all actual imported source origins')
actual,jobvalue=job._admitted(SimpleNamespace(root=S,registration=GATE,experiment=ID,source=H))
ck(actual.ready is True and actual.source==H and actual.design_source==H and actual.effective_attempt_budget==18,'genuine current-design ready metadata admission budget18')
ck(len(actual.inputs)==8 and len(actual.experiment['source_files'])==324 and admission.claims(S)==[],'actual source/input/current claims closure')
refusals=[]
for identity in oldgate['experiments']:
 try:admission.admit(root=S,registration=GATE,experiment=identity,source=H)
 except ValueError as exc:refusals.append({'identity':identity,'exception':type(exc).__name__,'message':str(exc)})
 else:raise AssertionError('historical old source registration unexpectedly executable')
ck(len(refusals)==10,'all10 historical source-bound entries refuse corrected source')
ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'actual no numerical imports')
ck(all(not os.path.lexists(root/'research_runs') and not os.path.lexists(root/'research_artifacts') for root in [OLD,S]),'no claim or output created')
ck(git(S,['status','--porcelain','--untracked-files=all'])==b'' and git(S,['rev-parse','HEAD']).decode().strip()==H and git(OLD,['status','--porcelain','--untracked-files=all'])==b'','actual unchanged source after API calls')
out={'schema_version':1,'decision':'ACCEPTED_ACTUAL_CORRECTED_SOURCE_AND_READONLY_ADMISSION_ONLY','checks':len(checks),'source':H,'design_source':H,'original_source':B,'adoption_sha256':sha(read(A/'SOURCE_ADOPTION01.json')),'registration':GATE,'registration_sha256':sha(read(S/GATE)),'tracked':325,'source_pins':324,'implementation':194,'package':149,'implementation_changed':changed,'implementation_unchanged':193,'fresh_identity':ID,'numerical_attempt_budget':18,'prior_attempts':0,'numerical_claims':0,'operational_identity_definitions':19,'prospective_numerical_phases':18,'actual_calls':{'job._admitted':1,'admission.admit_historical_refusals':10,'admission.claims':1,'ResearchRun.start':0},'actual_ready':actual.ready,'old_entry_refusals':refusals,'Torch_or_CUDA_observed':False,'new_full_external_preservation':False,'new_caller_or_numerical_release':False,'joined':joined}
(O/'READBACK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('joined','old_entry_refusals')},indent=2))
