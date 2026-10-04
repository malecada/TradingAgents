"""Root complete immutable failed-source/parent/outer capture; no fitting."""
import hashlib,importlib.util,json,os,shutil,sys,time
from pathlib import Path
M=Path.cwd();B=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=B/'financial-genuine-wrapper-root-recordfix-failed-scope-capture01-2026-10-04';P=B/'held-consumer-final-recovery-preparation04-2026-10-03'
assert not D.exists();D.mkdir(mode=0o700)
sys.path.insert(0,str(P));sp=importlib.util.spec_from_file_location('recordfix_failed_capture_r4',P/'recovery04.py');R=importlib.util.module_from_spec(sp);sp.loader.exec_module(R)
assert hashlib.sha256((P/'recovery04.py').read_bytes()).hexdigest()=='b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a'
roots={'source':Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-native-20261004-01/source'),'parent':Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-root-launch-20261004-01'),'outer':B/'financial-genuine-wrapper-root-recordfix-first-native01-2026-10-04'}
identity='financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01';claim=roots['source']/'research_runs'/identity/'claim.json';failed=claim.parent/'failed.json'
assert R.digest(R.read(claim.parent,claim.name))=='4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128';assert R.digest(R.read(failed.parent,failed.name))=='35158c0ecebfe4dc75203ba87d5372f2f85643c0b5f828a99e17aa28fe79c450'
terminal=json.loads(R.read(roots['outer'],'ACTUAL_TERMINAL01.json'));assert terminal['actual_exit']==1 and terminal['classification']=='UNEXPECTED_FAILURE_SPENT_NO_CHECKPOINT';assert not Path('/proc',str(terminal['actual_parent_pid'])).exists();assert not Path(terminal['actual_guard']['cgroup']).exists()
parts=Path('/proc/self/stat').read_text().split(') ',1)[1].split();R.put(D/'ACTUAL_INTENT01.json',{'pid':os.getpid(),'start_ticks':parts[19],'pgid':os.getpgid(0),'sid':os.getsid(0),'time_epoch':time.time(),'scope':'complete original failed Source+Parent+Root outer','native_or_numerical_started':False})
manifests={};archives={};floors=[]
for role,root in roots.items():
 free=shutil.disk_usage(root).free;assert free>=R.FLOOR;floors.append(free);manifest=R.scan(root);R.put(D/(role+'-manifest.json'),manifest);archive=R.pack(root,manifest,D/(role+'.tar.gz'));manifests[role]=manifest;archives[role]=archive;floors.append(shutil.disk_usage(root).free)
for role,root in roots.items():R.same(root,manifests[role])
assert all(n>=R.FLOOR for n in floors)
R.put(D/'CAPTURE01.json',{'schema_version':1,'status':'COMPLETE_FAILED_SCOPE_BYTES_ONLY','identity':identity,'source_commit':'649fb8a11089524aaef7843dffeeb90a3a55ca17','actual_native_exit':1,'genuine_failed_spent_claims':1,'highest_actual_budget':18,'claim_sha256':'4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128','failed_sha256':'35158c0ecebfe4dc75203ba87d5372f2f85643c0b5f828a99e17aa28fe79c450','archives':archives,'source_roots':{k:str(v) for k,v in roots.items()},'typed_members':{k:len(v['members']) for k,v in manifests.items()},'regular_members':{k:sum(r['kind']=='file' for r in v['members']) for k,v in manifests.items()},'logical_bytes':{k:sum(r.get('bytes',0) for r in v['members']) for k,v in manifests.items()},'observed_free_bytes':floors,'runtime_bodies_captured':False,'external_recovery':False,'numerical_or_native_started':False,'planned_checkpoint_present':False,'qualification':'Preserves complete actual failed raw stores/claims/native/Parent/controller/outer bytes; no POSIX/runtime recovery or fit/capacity credit. Original guard and Root null alias remain unchanged with separate qualification.'})
R.put(D/'CAPTURE_SOURCE01.json',{'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'r4_sha256':'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a','source':str(Path(__file__))});
with R.new_file(D/'capture01.py') as fd:
 raw=Path(__file__).read_bytes();offset=0
 while offset<len(raw):n=os.write(fd,raw[offset:]);assert n>0;offset+=n
 os.fsync(fd)
print(json.dumps({'status':'COMPLETE_FAILED_SCOPE_BYTES_ONLY','archives':archives,'typed':{k:len(v['members']) for k,v in manifests.items()},'regular':{k:sum(r['kind']=='file' for r in v['members']) for k,v in manifests.items()}}))
