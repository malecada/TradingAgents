import hashlib,json,os,stat,datetime,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;P=H.parent/'financial-genuine-wrapper-claimedrun-source-handoff-preparation02-2026-10-04';R=H.parent/'financial-genuine-wrapper-root-claimedrun-handoff-generation01-2026-10-04';O=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-native-20261004-01/source');checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and p.resolve()==p and s.st_size<=64*1024**2
 b=p.read_bytes();t=p.lstat();assert (s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(t.st_dev,t.st_ino,t.st_mode,t.st_size,t.st_mtime_ns,t.st_ctime_ns);return b
def load(p):return json.loads(read(p))
def check(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
terminal=load(R/'ACTUAL_GENERATION01.json');check(sha(read(R/'ACTUAL_GENERATION01.json'))=='ebb4a9eac72827d5e5ecc3657bac8662dcd23de25e6cfc99e181e488e5e2d592','exact actual Root receipt');check(terminal['actual_exit']==0 and terminal['actual_direct_tool']=='517d4c','Root reported tool exit0');check(terminal['observed_original_pid_or_pgid'] is None,'original missing PID history stays null')
ad=load(R/'ADOPTION01.json');check(ad['actual_generation'] is False and ad['actual_admission'] is None and ad['actual_destination_source'] is None,'prior adoption fields preserved separately');check(ad['actual_independent_review_manifest']==sha(read(H/'MANIFEST02.json')),'genuine prior exact review join');check(ad['actual_author_manifest']==sha(read(P/'MANIFEST01.json')),'genuine author manifest join')
for r in ad['installed']:check(read(R/r['name'])==read(P/r['name']) and sha(read(R/r['name']))==r['sha256'],'actual primitive/candidate '+r['name'])
check(len(ad['installed'])==5,'exact five adopted files');check({p.name for p in R.iterdir()}=={r['name'] for r in ad['installed']}|{'ADOPTION01.json','ACTUAL_GENERATION01.json','generated01'},'complete Root generation tree')
check(len(terminal['generated_files'])==11,'exact11');check({p.name for p in (R/'generated01').iterdir()}=={Path(r['path']).name for r in terminal['generated_files']},'complete actual generated files')
for r in terminal['generated_files']:
 p=R/r['path'];b=read(p);check(b==read(P/r['path']) and sha(b)==r['sha256'] and len(b)==r['bytes'] and stat.S_IMODE(p.lstat().st_mode)==r['mode']==0o600,'actual generated body/hash/private mode '+r['path'])
d=load(R/'generated01/HANDOFF01.json');check(d['status']=='DRAFT_NOT_RELEASED' and d['release'] is False,'draft only')
for k in ('new_source','design_source','registration','charter','cumulative19_admission','independent_source_review','caller','complete_recovery','source_file_map','final_tracked_count'):check(d[k] is None,'null '+k)
for n,ref in d['input_roles'].items():check(ref['path']=='fixture_inputs/financial_wrapper_claimedrun01/'+n+'.json' and sha(read(R/'generated01'/f'{n}.json'))==ref['sha256'],'actual role '+n)
check(len(d['input_roles'])==8 and d['historical_claims_spent']==1 and d['checkpoint_ancestry_from_failed_recordfix'] is False,'eight roles spent1 no checkpoint ancestry')
src=load(R/'generated01/ORIGINAL_SOURCE_READBACK01.json');q=subprocess.run(['git','-c','core.hooksPath=/dev/null','rev-parse','HEAD'],cwd=O,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30);check(q.returncode==0 and q.stdout.decode().strip()==src['source']=='649fb8a11089524aaef7843dffeeb90a3a55ca17','actual original HEAD')
for n,r in src['tracked'].items():
 p=O/n;b=read(p);check(sha(b)==r['sha256'] and len(b)==r['bytes'] and stat.S_IMODE(p.stat().st_mode)==r['mode'],'actual retained original body/mode '+n);check(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==r['git_object'],'original blob '+n)
check(len(src['tracked'])==325,'original325');c=load(R/'generated01/source_closure.json');changed=[]
for n,h in c['installed'].items():
 if sha(read(O/n))!=h:changed.append(n)
check(len(c['installed'])==194 and sum(n.startswith('tradingagents/') for n in c['installed'])==149 and changed==['tradingagents/research/onchain_replication/financial_wrapper_fixture.py'],'194/149 onlyf4ea change193 same');check(c['installed'][changed[0]]==sha(read(R/'candidate.py')),'exact future candidate body')
runtime=load(R/'generated01/runtime_mapping.json');check(len(runtime['distribution_records'])==251,'251 runtime metadata rows')
for r in runtime['distribution_records']:check(sha(read(Path(r['record'])))==r['record_sha256'],'actual RECORD '+r['name'])
check(sha(read(Path(runtime['resolved_executable'])))==runtime['executable_sha256'] and sha(read(O/'uv.lock'))==runtime['lock_sha256'],'actual interpreter/lock');check(runtime['executable']==sys.executable and runtime['prefix']==sys.prefix,'actual research interpreter')
check(src['runtime_api_observed'] is False and src['runtime_dependency_bodies_recovered'] is False,'no runtimebody/API claim')
check(read(R/'generated01/ORIGINAL_GATES_PRESERVED.json')==read(O/'fixture_inputs/financial_wrapper_recordfix01/gates.json'),'complete historical gate bytes')
check(not any(x in sys.modules for x in ('numpy','torch','scipy','pandas')),'stdlib only')
out={'decision':'ACCEPTED_ACTUAL_ROOT_GENERATED_DRAFT_BYTES','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':len(checks),'check_names':checks,'actual_root_receipt_sha256':sha(read(R/'ACTUAL_GENERATION01.json')),'actual_root_direct_tool_report':'517d4c exit0 per pinned genuine Root receipt','original_process_identity_history':None,'independent_OS_execution_history':None,'generator_rerun':False,'all_eleven_match_accepted_author_bytes':True,'actual_future_source':None,'actual_admission':None,'actual_caller':None,'actual_release':False,'new_capsule_inspected':False,'new_capsule_absence_independently_tested':False,'scope':'Actual generated bytes and provenance, not installed Source or runtime/financial authority. Root timing/exit from genuine receipt; no fabricated PID history. Prior ADOPTION generationfalse remains historical.'};(H/'ACTUAL_READBACK03.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='check_names'}))
