from pathlib import Path
import importlib.util,json,os,stat,time,sys,hashlib
P=Path(__file__).absolute().parent;s=importlib.util.spec_from_file_location('watch_independent02',P/'watch01.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);O=P/'owned02';O.mkdir(mode=0o700);checks=[];rows=[]
def ck(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
for mode in ('inode','mode'):
 root=O/mode;root.mkdir(mode=0o700);body=root/'body';body.write_bytes(b'opaque')
 orig=Path.lstat;count=0;changes=0
 def endpoint(p,*a,**kw):
  global count,changes
  if p==body:
   count+=1
   if count%2==0:
    if mode=='inode':body.rename(O/('retained-'+str(changes)));body.write_bytes(b'opaque')
    else:os.chmod(body,0o600 if changes%2==0 else 0o644)
    changes+=1
  return orig(p,*a,**kw)
 Path.lstat=endpoint;caught=None
 try:m.census(root)
 except ValueError as e:caught=e
 finally:Path.lstat=orig
 ck('persistent-'+mode+'-refuses',caught is not None and changes==3)
 rows.append({'control':mode,'changes':changes,'refused':caught is not None})
# A real ephemeral filename becomes a durable name; one complete retry includes it.
root=O/'publication';root.mkdir(mode=0o700);pending=root/'.pending-owned';pending.write_bytes(b'full retained body')
orig=Path.lstat;changed=False

def rename_before_stat(p,*a,**kw):
 global changed
 if p==pending and not changed:
  changed=True;pending.rename(root/'published')
 return orig(p,*a,**kw)
Path.lstat=rename_before_stat;begin=time.monotonic()
try:result=m.census(root)
finally:Path.lstat=orig
ck('real-disappeared-enumerated-name-retry',result['complete_attempts']==2 and result['logical_bytes']==18 and result['members']==2 and time.monotonic()-begin>=.1)
# Both extent endpoints retained without inode replacement or pending exclusion.
root=O/'extent';root.mkdir(mode=0o700);body=root/'.pending-counted';body.write_bytes(b'ab')
orig=Path.lstat;count=0

def grow(p,*a,**kw):
 global count
 if p==body:
  count+=1
  if count==2:
   with body.open('ab') as f:f.write(b'cdefgh')
 return orig(p,*a,**kw)
Path.lstat=grow
try:result=m.census(root)
finally:Path.lstat=orig
ck('actualgrowth-maxendpoint',result['logical_bytes']==8 and result['regular_extent_changes']==1 and result['complete_attempts']==1)
# Wait interruption selects actual fatal, no third try.
original_sample=m._sample;original_sleep=m.time.sleep;seen=[];fatal=KeyboardInterrupt('real sleep callback interruption')
def fail(root):seen.append(True);raise m.ChangingTree('owned')
def pause(n):raise fatal
m._sample=fail;m.time.sleep=pause;caught=None
try:m.census(root)
except BaseException as e:caught=e
finally:m._sample=original_sample;m.time.sleep=original_sleep
ck('retry-sleep-fatal-not-retried',caught is fatal and seen==[True])
# Authenticate original failed raw status without changing null into reaped result.
A=P.parent/'financial-wrapper-operational-forensic-watch-correction04-2026-10-04';hist=A/'historical-failed-remote02';raw=(hist/'FAILED01.json').read_bytes();failed=json.loads(raw);review=json.loads((hist/'READBACK01.json').read_bytes());exit=json.loads((hist/'ROOT_REMOTE02_EXIT01.json').read_bytes())
ck('actualfailedreceiptpin',hashlib.sha256(raw).hexdigest()=='7491cc3c1940b68cab9b218e972a13c925f5ce1ff21d9f0a2f32ee416246268a')
ck('raw-observed-null-separate-reaped0',[r['exit'] for r in failed['operations']]==[0,0,None] and [r['actual_reaped_exit'] for r in failed['operations']]==[0,0,0])
ck('historical-root1',exit['actual_outer_exit']==1)
ck('historical-component-unknown',review['historical_changed_path'] is None and review['historical_changed_signature_component'] is None and review['remote_success_receipt'] is None and review['flat_outcome'] is None)
(P/'READBACK02.json').write_text(json.dumps({'checks':len(checks),'names':checks,'actual_identity_refusals':rows,'historical_failed_source_sha256':hashlib.sha256(raw).hexdigest(),'no_remote_native_or_numeric_execution':True},indent=2)+'\n');print(json.dumps({'checks':len(checks),'status':'PASS_SOURCE_ONLY'}))
