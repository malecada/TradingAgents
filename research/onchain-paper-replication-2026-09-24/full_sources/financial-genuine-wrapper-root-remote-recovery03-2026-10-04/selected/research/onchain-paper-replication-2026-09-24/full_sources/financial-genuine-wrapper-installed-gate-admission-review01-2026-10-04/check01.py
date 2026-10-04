import ast,hashlib,json,os,stat,subprocess,sys
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-native-20261003-01/source');A=F/'financial-genuine-wrapper-root-initial-input-adoption01-2026-10-04';G=F/'financial-genuine-wrapper-registration-preparation01-2026-10-04/generated03';P=F/'financial-genuine-wrapper-root-gate-preparation01-2026-10-04';H='d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0';BASE='1a8c612d5d66858c725f9196e80b2140b9e6fc81';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,m):
 assert v,m
 checks.append(m)
def sig(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def read(p):
 s=p.lstat();ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2 and p.resolve()==p,'canonical bounded input');fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  ck(sig(os.fstat(fd))==sig(s),'opened actualinode');parts=[];count=0
  while True:
   b=os.read(fd,65536)
   if not b:break
   count+=len(b);ck(count<=s.st_size,'bounded extent');parts.append(b)
  ck(sig(os.fstat(fd))==sig(s)==sig(p.lstat()) and count==s.st_size,'unchanged actualbody');return b''.join(parts)
 finally:os.close(fd)
def doc(p,pin=None):
 b=read(p);ck(pin is None or sha(b)==pin,'pin '+p.name);return json.loads(b)
def git(args,data=None):
 r=subprocess.run(['git','--no-replace-objects','-c','protocol.allow=never','-C',str(S),*args],input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,env={'PATH':'/usr/bin:/bin','GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1','GIT_OPTIONAL_LOCKS':'0','GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1'});ck(r.returncode==0 and len(r.stdout)<=8*1024**2 and len(r.stderr)<=65536,'bounded offline Git');return r.stdout

A=F/'financial-genuine-wrapper-root-gate-adoption01-2026-10-04';R=F/'financial-genuine-wrapper-root-readonly-admission01-2026-10-04';I=F/'financial-genuine-wrapper-installed-input-gate-review01-2026-10-04';prior=doc(I/'READBACK01.json','a656381d02a342e6d9eb7e0e63129553cef8725eead628efc1ae7b1fbd8d5aa3');old={r['path']:r for r in prior['joined']};m=doc(I/'MANIFEST01.json','dc7b8658787c138fa2432a276debaacfcfd69ef6b57a2e223b9487306f608d5f')
for row in m['members']:
 p=I/row['path'];b=read(p);ck(row['kind']=='file' and sha(b)==row['sha256'] and len(b)==row['bytes'] and stat.S_IMODE(p.stat().st_mode)==row['mode'],'previous review typedbody preserved')
ad=doc(A/'ADOPTION01.json');order=doc(A/'FIXED_ORDER01.json');proposal=doc(P/'PROPOSAL01.json');support=proposal['support_adoption'];gpath='fixture_inputs/financial_wrapper_registration01/gates.json';gate=doc(S/gpath,'6818dfdc48879fde8bf149bd1dae252885c6460a209e31af5a17a66012247691');ck(read(S/gpath)==read(P/'GATE_PROPOSAL01.json'),'installed gate exactaccepted proposal');ck(git(['rev-parse','HEAD']).decode().strip()==H==ad['actual_current_source'] and git(['rev-parse',H+'^']).decode().strip()==BASE==ad['prior_source'],'actual direct269parent');tree={}
for e in git(['ls-tree','-r','-z',H]).split(b'\0'):
 if not e:continue
 left,n=e.split(b'\t');mode,typ,oid=left.decode().split();ck(typ=='blob' and mode in ('100644','100755'),'actual regular committed member');tree[n.decode()]={'git_mode':mode,'git_oid':oid}
ck(len(tree)==290 and set(tree)==set(old)|set(support)|{gpath} and len(old)==269 and len(support)==20,'actual290 exact269+20+gate');ck(set(ad['adopted_paths'])==set(support)|{gpath},'adoption exact21paths');actual=set()
for root,ds,fs in os.walk(S,followlinks=False):
 if Path(root)==S:ds.remove('.git')
 for n in ds:ck(stat.S_ISDIR((Path(root)/n).lstat().st_mode),'real source directories')
 actual.update(str((Path(root)/n).relative_to(S)) for n in fs)
ck(actual==set(tree),'complete actualfilesystem290');reply=git(['cat-file','--batch'],(''.join(tree[n]['git_oid']+'\n' for n in sorted(tree))).encode());offset=0;joined=[]
for n,row in sorted(tree.items()):
 end=reply.index(b'\n',offset);oid,typ,size=reply[offset:end].decode().split();size=int(size);b=reply[end+1:end+1+size];offset=end+size+2;mode=stat.S_IMODE((S/n).lstat().st_mode);ck(typ=='blob' and oid==row['git_oid'] and reply[offset-1:offset]==b'\n' and hashlib.sha1(b'blob '+str(size).encode()+b'\0'+b).hexdigest()==oid,'actual committed bodyOID');ck(read(S/n)==b and row['git_mode']==('100755' if mode&0o111 else '100644'),'livebody mode matchesGit')
 if n in old:ck(old[n]['git_oid']==oid and old[n]['sha256']==sha(b) and old[n]['bytes']==len(b) and old[n]['mode']==mode and old[n]['git_mode']==row['git_mode'],'all269unchanged exactmodes/body/OID')
 elif n in support:ck(read(Path(support[n]['actual_prepared_path']))==b and sha(b)==support[n]['sha256'] and len(b)==support[n]['bytes'] and mode==0o644,'actual20adopted exactsupport bodies0644')
 else:ck(n==gpath and mode==0o644,'actual gate0644')
 joined.append({'path':n,'sha256':sha(b),'bytes':len(b),'mode':mode,**row})
ck(offset==len(reply),'complete batch');sourcepins={r['path']:r['sha256'] for r in joined if r['path']!=gpath};runtime={p.name:sha(read(p)) for p in (S/'tradingagents/research').glob('*.py')};ck(len(runtime)==7 and len(sourcepins)==289 and sum(n.startswith('tradingagents/') for n in tree)==149 and ad['implementation_unchanged']==194 and ad['auxiliary']==96,'29028919414996 actualcounts');charter=doc(S/'fixture_inputs/financial_wrapper_registration01/CHARTER02.json');family=gate['families']['synthetic-financial-wrapper'];ck(family['attempt_budget']==18 and family['prior_attempts']==0 and family['mechanism_id']=='synthetic-full-financial-wrapper-v1','committed actualbase18prior0')
for exp,e in gate['experiments'].items():
 ck(e['source_files']==sourcepins and e['runtime_hashes']==runtime and e['parent'] is None and len(e['inputs'])==8,'exactactual289source7runtime8initialinputs')
 for role,ref in e['inputs'].items():ck(sha(read(S/ref['path']))==ref['sha256']==sourcepins[ref['path']] and ref['dataset']=='synthetic','actual80input bodyjoins')
 ck(e['charter']['sha256']==sha(read(S/e['charter']['path'])) and e['stage']=='development' and e['reuse']=='exploratory','actualcharter exploratory scope')
phases=sorted(charter['phases'],key=lambda r:r['slot_index']);ids=[r['proposed_identity'] for r in phases];ck([r['slot_index'] for r in phases]==list(range(1,19)) and len(set(ids))==18,'exact18uniquecharter slots');ck(order['complete18_topological_order']==ids and order['initial10_order']==[n for n in ids if n in gate['experiments']] and len(gate['experiments'])==10 and order['first_initial']==ids[0]=='financial-wrapper-classification-eager-interrupt1-20261003-01','exactorder initial10projection');positions={n:i for i,n in enumerate(ids)}
for r in phases:ck(all(positions[d]<positions[r['proposed_identity']] for d in r['proposed_dependencies']),'every actualcharter dependency precedeschild')
ck(order['actual_source']==H and order['actual_gate_sha256']==sha(read(S/gpath)) and order['caller_must_bind_this_exact_order'] is True and order['unexpected_failure_halts_numerical_release'] is True and order['planned_interruption_FAILED_does_not_refund_budget'] is True,'exact documentaryorder source/noRefund stop');ck(set(ids)-set(gate['experiments'])=={r['proposed_identity'] for r in phases if r['phase'] in ['continue100','predict']},'exact8dependent unregistered')
readback=doc(R/'READBACK02.json','bac328184195565392d393d4072fc958701519a8b2ba2aa76ec7037ffdd58f30');terminal=doc(R/'ACTUAL_TERMINAL02.json');failure=doc(R/'HARNESS_FAILURE01.json');ck(terminal['exit']==0 and terminal['actual_readback_sha256']==sha(read(R/'READBACK02.json')) and terminal['actual_genuine_readonly_admission']==10 and terminal['ResearchRun_start'] is False,'actualRootterminal/readback join');ck(len(readback['results'])==readback['count']==10 and {r['experiment'] for r in readback['results']}==set(gate['experiments']),'all10actual APIreported entries')
for r in readback['results']:
 e=gate['experiments'][r['experiment']];ck(r['source']==r['design_source']==H and r['registration_sha256']==sha(read(S/gpath)) and r['ceiling']==18 and r['family']==family and r['ready'] is True and r['input_count']==8 and r['source_pins']==289 and r['cells']==e['cells'],'genuine readonlyrecord source/design/gate/ceiling/inputs joins')
for module,pin in readback['imported_source_hashes'].items():
 p=S/Path(*module.split('.'));p=p/'__init__.py' if p.is_dir() else p.with_suffix('.py');ck(sha(read(p))==pin and str(p.relative_to(S)) in tree,'actual importedmodule source provenance')
source=ast.parse(read(S/'tradingagents/research/admission.py'));cls=next(n for n in source.body if isinstance(n,ast.ClassDef) and n.name=='Admission');fields={n.target.id for n in cls.body if isinstance(n,ast.AnnAssign)};ck('inputs' in fields and 'resolved_inputs' not in fields and 'effective_attempt_budget' in fields,'actual genuine Admission dataclass fields');ck(failure['exception']=='AttributeError' and failure['first_genuine_admit_returned_before_error'] is True and failure['actual_claim'] is False and failure['ResearchRun_start_called'] is False,'original failedcollector preserved notRun');ck(readback['ResearchRun_start_called'] is False and readback['actual_claims_before_after']==0 and readback['numerical_imports'] is False and readback['inputs_or_outcome_decoded'] is False,'actual Rootreadonly limitations');ck(all(not (S/n).exists() for n in ['research_runs','research_artifacts','fixture_outer']),'actual claims/output namespaces absent');ck(git(['rev-parse','HEAD']).decode().strip()==H and git(['status','--porcelain','--untracked-files=all'])==b'','finalclean unchanged source290');ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'reviewer no numericalimports');out={'schema_version':1,'decision':'ACCEPTED_ACTUAL_INSTALLED_GATE_AND_RECORDED_READONLY_ADMISSION_ONLY','checks':len(checks),'actual_source':H,'parent_source':BASE,'tracked':290,'source_pins_per_experiment':289,'implementation':194,'package':149,'auxiliary':96,'all269unchanged':True,'adopted_support':20,'gate_sha256':sha(read(S/gpath)),'family_base':18,'prior_attempts':0,'initial_entries':10,'withheld_dependent_entries':8,'current_claims':0,'fixed_order_sha256':sha(read(A/'FIXED_ORDER01.json')),'readback_sha256':sha(read(R/'READBACK02.json')),'actual_terminal_sha256':sha(read(R/'ACTUAL_TERMINAL02.json')),'failed_collector_sha256':sha(read(R/'HARNESS_FAILURE01.json')),'reviewer_repeated_admit_or_start':False,'full_current290recovery':False,'native_or_capacity_or_runtime_release':False,'qualification':'Root actual terminal/readback authenticated against installed API/source; no repeated admission or synthetic authority object. ready=True is narrow admission/time readiness, not native release. Fixed order remains documentary caller input awaiting actual binding.','joined':joined};(O/'READBACK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='joined'},indent=2))
