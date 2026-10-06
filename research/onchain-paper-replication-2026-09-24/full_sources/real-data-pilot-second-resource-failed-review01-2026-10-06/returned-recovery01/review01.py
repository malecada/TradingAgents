"""Second failed-pilot archive: one returned stream, zero original body streams."""
from pathlib import Path
import hashlib,io,json,stat,tarfile
R=Path.cwd();BASE=Path('research/onchain-paper-replication-2026-09-24');F=BASE/'full_sources'
P=F/'real-data-pilot-second-resource-failed-review01-2026-10-06';H=P/'returned-recovery01'
I='real-pilot-second-resource-failed-preservation-20261006-01';S=BASE/'storage'/I
CAP=F/'real-data-pilot-second-resource-failed-increment01-2026-10-06';ORIGINAL=CAP/'failed-increment01.tar'
cache={};counts={}
def raw(p):
 p=Path(p);assert p!=ORIGINAL
 if p not in cache:
  q=R/p;s=q.lstat();assert q.resolve(strict=True)==q and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2
  b=q.read_bytes();z=q.lstat();assert len(b)==s.st_size and (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns)
  cache[p]=b;counts[str(p)]=counts.get(str(p),0)+1
 return cache[p]
def sha(p):return hashlib.sha256(raw(p)).hexdigest()
def read(p):return json.loads(raw(p))
def ref(p):return {'path':str(p),'sha256':sha(p)}
def write(n,v):
 p=H/n
 with p.open('x') as f:f.write(json.dumps(v,sort_keys=True,indent=2)+'\n')
 return p
assert sha(P/'INCREMENT_SELECTION01.json')=='e07439c085399448192ba1003f343767a32ce33d2cf95f3c7896f21959717b2d'
assert sha(P/'ordinary-entry01/CHECK01.json')=='6168e18296b344f53d70ef09013b599de8f67ef38743525514a4893a96c2cbc0'
assert sha(P/'OUTCOME_REVIEW01.json')=='6cb4bdae9a8b1dc13c43811d37b57518d50f967b3e425183a0696e7fc5b4e9d7'
scope=read(P/'INCREMENT_SELECTION01.json');capture=read(CAP/'CAPTURE01.json');proof=read(P/'ordinary-entry01/CHECK01.json')
assert proof['decision']=='accepted' and proof['archive']==capture['archive']
assert capture['selection']==ref(P/'INCREMENT_SELECTION01.json')
complete=read(S/'complete.json');selection=read(S/'selection01.json');verified=read(S/'00-verified.json');restore=read(S/'00-recovered-restore.json')
assert complete['identity']==selection['identity']==I and complete['selection']==selection and complete['files']==[verified]
assert complete['count']==1 and complete['bytes_preserved']==481280
assert complete['originals_retained'] is True and complete['recoveries_retained'] is True and complete['no_automatic_retry'] is True
assert sha(S/'complete.json')==sha(S/'completion-candidate.json')==sha(S/'recovered-complete.json')
assert sha(S/'00-restore.json')==sha(S/'00-recovered-restore.json') and sha(S/'00-verified.json')==sha(S/'00-kept.json')
assert {k:v for k,v in verified.items() if k not in ('original_retained','recovered_body_retained')}==restore
assert verified['body_roundtrip_verified'] is True and verified['original_retained'] is True and verified['recovered_body_retained'] is True
row=selection['files'][0];assert all(verified[k]==v for k,v in row.items())
assert row['path']==str(ORIGINAL) and row['bytes']==481280 and row['sha256']==capture['archive']['sha256']
assert verified['remote_object']==selection['remote']+'/00.bin' and verified['remote_restore']==selection['remote']+'/00-restore.json'
assert read(S/'00-attempted.json')=={'number':0,'row':row} and read(S/'intent.json')['selection']==selection
s=ORIGINAL.lstat();assert (R/ORIGINAL).resolve(strict=True)==R/ORIGINAL and stat.S_ISREG(s.st_mode) and s.st_nlink==row['nlink']==1
assert stat.S_IMODE(s.st_mode)==row['mode'] and row['stat_identity']==[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
returned=S/'00-recovered.bin';b=raw(returned);assert len(b)==481280 and hashlib.sha256(b).hexdigest()==row['sha256']=='beec1ce98ef3214a8486a01af03e939301f2966369faf39f29cb4362d65e87d6'
expected={r['path']:r for r in scope['files']+scope['directories']};captured={r['path']:r for r in capture['members']}
assert len(expected)==len(captured)==48 and set(expected)==set(captured)
members=[]
with tarfile.open(fileobj=io.BytesIO(b),mode='r:') as tf:
 seen=set()
 for m in tf.getmembers():
  p=m.name.rstrip('/');assert p in expected and p not in seen and not Path(p).is_absolute() and '..' not in Path(p).parts;seen.add(p);r=expected[p];assert m.mode==r['mode']==captured[p]['mode']
  if r['kind']=='directory':assert m.isdir() and m.size==0;members.append({'path':p,'kind':'directory','mode':m.mode})
  else:
   assert m.isfile() and not m.issym() and not m.islnk() and m.size==r['bytes']==captured[p]['bytes']
   with tf.extractfile(m) as stream:payload=stream.read(m.size+1)
   h=hashlib.sha256(payload).hexdigest();assert len(payload)==m.size and h==r['sha256']==captured[p]['sha256']
   members.append({'path':p,'kind':'regular','mode':m.mode,'bytes':m.size,'sha256':h})
 assert seen==set(expected)
assert sum(m.get('bytes',0) for m in members)==395772 and sum(m['kind']=='regular' for m in members)==38
assert counts[str(returned)]==1 and str(ORIGINAL) not in counts
pids=set();transports={}
for name in ('00-recovered.bin','00-recovered-restore.json','recovered-complete.json'):
 p=S/(name+'.transport.json');t=read(p);size=len(raw(S/name))
 assert t['status']=='complete' and t['returncode']==0 and t['error_type'] is None and t['expected_bytes']==t['received_bytes']==size
 pids.add(t['pid']);transports[name]={'receipt':ref(p),'received_bytes':size,'returncode':0,'pid':t['pid']}
root=read(S/'ROOT_TERMINAL01.json');outer=read(S/'outer-exit01.json');guard=read(S/'guard01/final.json')
assert root['identity']==I and root['actual_root_session']==77194 and root['actual_root_terminal_chunk']=='95032a'
assert root['actual_root_exit_code']==root['native_child_exit_code']==outer['entry_selected_exit_code']==outer['guard_child_exit_code']==guard['child_exit_code']==0
assert guard['elapsed_seconds']==root['native_elapsed_seconds']==6.377868823999961
assert root['original_outer_exit']==outer and root['original_guard_sha256']==sha(S/'guard01/final.json')
assert guard['phase']==outer['guard_phase']=='complete' and root['cleanup_verified'] is True and guard['cleanup_verified'] is True and outer['cleanup_verified'] is True
assert outer['fatal_type'] is None and guard['owner_identity'] is None and guard['cleanup_stop_returncode']==5
assert guard['cleanup_unit_properties']['ActiveState']=='inactive' and guard['cleanup_unit_properties']['ControlGroup']=='' and guard['cleanup_unit_properties']['Result']=='success'
assert not Path(guard['cgroup']).exists() and not (S/'failed.json').exists()
child=read(S/'guard01/child_exit.json');cpu=read(S/'guard01/cpu_ready.json');assert child['exit_code']==0
pids.update((guard['monitor_pid'],child['workload_pid'],cpu['pid']));assert all(type(pid) is int and pid>0 and not Path('/proc',str(pid)).exists() for pid in pids)
preflight=read(S/'preflight01.json');assert preflight==read(S/'launch-attempt01.json') and preflight['head']==root['source']=='d8466b2058e1709459495ef2d7fc251e81eb79b5'
assert preflight['envelope_sha256']==sha(S/'envelope01.json')=='9cde1f3ef0754c30e7616377bc3e837484bf53c1ab8259216437d114dcd25d74'
assert sha(S/'RELEASE_REVIEW01.json')=='4fa062ea939a3f00c5b2adb51ac3a88d10454df6c0e9be05f270b3a82cb38752'
mp=write('RECOVERED_MEMBERS01.json',{'schema_version':1,'decision':'accepted','identity':I,'returned_archive':ref(returned),'original_capture':ref(CAP/'CAPTURE01.json'),'original_selection':ref(P/'INCREMENT_SELECTION01.json'),'original_body_proof_reused':ref(P/'ordinary-entry01/CHECK01.json'),'members':members,'regular_count':38,'directory_count':10,'total_names':48,'original_regular_bytes':395772,'returned_archive_streams':1,'original_archive_streams':0})
evidence={str(p):hashlib.sha256(v).hexdigest() for p,v in cache.items()};evidence[str(mp)]=sha(mp)
rp=write('RECOVERY_REVIEW01.json',{'schema_version':1,'decision':'accepted','identity':I,'source':root['source'],'evidence':dict(sorted(evidence.items())),
 'scope':'Actual complete external BYTE recovery of exact second failed-pilot archive, restoration metadata and remote completion record; independent returned member/name/mode/body join.',
 'complete_sha256':sha(S/'complete.json'),'archive':{'sha256':row['sha256'],'bytes':481280,'regular_bodies':38,'directory_names_modes':10,'total_names':48,'unpacked_regular_bytes':395772,'original_path':str(ORIGINAL),'returned_path':str(returned),'original_current_stat_unchanged':True,'member_review':ref(mp)},
 'root_actual_exit':{'exit_code':0,'session':77194,'terminal_chunk':'95032a'},'native':{'phase':'complete','elapsed_seconds':guard['elapsed_seconds'],'child_exit_code':0,'cleanup_verified':True,'cleanup_stop_returncode':5,'owner_identity':None,'cleanup_unit_properties':guard['cleanup_unit_properties'],'memory_events':guard['memory_events']},'outer':outer,'transport_receipts':transports,
 'current_cleanup':{'recorded_cgroup_absent':True,'selected_pid_exists':{str(pid):False for pid in sorted(pids)},'lifetime_process_history':None,'qualification':'Selected recorded PIDs and cgroup absent now; original unit terminal readbacks reused, no native command or lifetime reconstruction.'},
 'original_failed_experiment':'eth-paper-real-data-end-to-end-resource-20261006-02','original_failed_outcome':ref(P/'OUTCOME_REVIEW01.json'),'originals_retained':True,'recoveries_retained':True,'deletion_authorized':False,
 'qualification':'BYTE/member/name/mode acceptance only, not POSIX ownership/timestamps/xattrs reconstruction, runtime bodies, unrelated or historical raw/graph stores, future remote availability, scientific completion or capacity. Original02 remains permanentlyFAILED/spent; original nulls and cleanup-stop5 preserved.',
 'not_tested':['No original archive/body restream, private/scientific/runtime body read or numerical import.','No transport/network/native replay, extraction, deletion or scientific experiment.','No return/cashflow, leakage, fees/funding or predictive correctness claim tested.']})
manifest=write('MANIFEST01.json',{'schema_version':1,'decision':'accepted','identity':I,'files':[ref(H/'review01.py'),ref(mp),ref(rp)]})
print(json.dumps({'review':ref(rp),'manifest':ref(manifest),'members':ref(mp),'decision':'accepted','selected_absent_pids':len(pids)},sort_keys=True))
