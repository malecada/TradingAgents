import ast,hashlib,io,json,os,stat,subprocess,sys,gzip,tarfile
from pathlib import Path
D=Path(__file__).resolve().parent;F=D.parent;C=F/'financial-wrapper-claimedrun-failed-capture01-2026-10-04';T=F/'financial-wrapper-claimedrun-failed-remote01-2026-10-04';P=F/'financial-batch-output-genuine-byte-bridge-preparation03-2026-10-04';sys.path.insert(0,str(P));import recovery04 as R
sha=lambda b:hashlib.sha256(b).hexdigest();cap=json.loads((C/'CAPTURE01.json').read_bytes());checks=[]
def ok(v,msg):assert v,msg;checks.append(msg)
S=Path(cap['scopes']['capsule']['origin']);env=dict(os.environ);env['GIT_NO_REPLACE_OBJECTS']='1';commands=[]
def git(args):
 p=subprocess.run(['git','--no-replace-objects','-C',str(S),*args],env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
 ok(p.returncode==0 and not p.stderr,'bounded local Git '+args[0]);commands.append({'args':args,'exit':p.returncode,'stdout_sha256':sha(p.stdout),'bytes':len(p.stdout)});return p.stdout
ok(git(['rev-parse','HEAD']).decode().strip()==cap['source'],'unchanged actual source HEAD')
tree=git(['ls-tree','-r','-z',cap['source']]);rows=json.loads((C/'CAPSULE_MANIFEST01.json').read_bytes())['members'];by={r['path']:r for r in rows}
count=0
for item in tree.rstrip(b'\0').split(b'\0'):
 left,name=item.split(b'\t');mode,kind,oid=left.decode().split();n=name.decode();r=by[n];b=R.read(C/'capsule-snapshot',n)
 ok(kind=='blob'and mode in ('100644','100755')and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid,'current immutable Git body '+n)
 ok(bool(r['mode']&0o111)==(mode=='100755'),'Git execute bit vs literal mode '+n);count+=1
ok(count==339,'339 tracked source bodies')
terminal=json.loads((C/'parent-snapshot/attempt/parent-terminal.json').read_bytes());out=json.loads((C/'root-snapshot/ROOT_NATIVE_LAUNCH01_EXIT.json').read_bytes());ok(sha((C/'parent-snapshot/attempt/parent-terminal.json').read_bytes())==out['original_parent_terminal_sha256'],'original parent terminal byte join')
ok(terminal['actual_parent_exit']is None and terminal['actual_child_exit']==1 and out['actual_outer_process_exit_code']==1,'preserved null and distinct observed outer1')
pids=set();groups=set()
for p in (C/'parent-snapshot/attempt').rglob('owned-tree-cleanup.json'):
 q=json.loads(p.read_bytes());ok(q['remaining_original_identities']==[],'actual retained empty remaining identities')
 for row in q['owned_pid_start_records']:pids.add(row['pid']);groups.add(row['pgrp'])
for op in terminal['cleanup']['actual_control_operations'].values():pids.add(op['pid'])
for pid in sorted(pids):ok(not Path('/proc',str(pid)).exists(),'current recorded PID absence '+str(pid))
for group in sorted(groups):
 try:os.killpg(group,0)
 except ProcessLookupError:checks.append('current recorded process group absence '+str(group))
 else:raise AssertionError('group remains')
ok(not Path(terminal['cleanup']['cgroup']).exists(),'current recorded cgroup absence')
# Metadata hash joins only: checkpoint state is never deserialized.
outcome=json.loads((F/'financial-wrapper-claimedrun-native-outcome-review01-2026-10-04/MACHINE01.json').read_bytes());hashes={r.get('sha256'):r['path']for r in rows}
for key in ('claim_sha256','failed_sha256','checkpoint_manifest_sha256','checkpoint_state_sha256'):ok(outcome[key]in hashes,'captured actual opaque '+key)
# Tiny stdlib framing/refusal controls through exact pinned R4.
tiny=D/'tiny-frame';tiny.mkdir();(tiny/'opaque').write_bytes(b'opaque');m=R.scan(tiny);sink=io.BytesIO();R.tar_stream(tiny,m,sink);raw=sink.getvalue();ok(len(list(R.framed_members(raw)))==1,'tiny canonical raw frame')
def refused(raw,name):
 try:list(R.framed_members(raw))
 except BaseException as e:checks.append(name+': '+type(e).__name__)
 else:raise AssertionError(name)
refused(raw[:-7],'truncated gzip trailer')
inflated=gzip.decompress(raw);refused(gzip.compress(inflated[:-1024]+b'x'*1024,mtime=0),'nonzero TAR footer')
header=tarfile.TarInfo('link');header.type=tarfile.SYMTYPE;header.linkname='target';refused(gzip.compress(header.tobuf()+bytes(1024),mtime=0),'symbolic link refused')
header=tarfile.TarInfo('../escape');refused(gzip.compress(header.tobuf()+bytes(1024),mtime=0),'traversal refused')
# Exact remote reducer/write full body-vs-close fatal pairs, real closes.
tree=ast.parse((T/'recover01.py').read_bytes());names={'require','_raise_retained','write'};nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names];ns={'os':os,'FILE':4*1024**2};exec(compile(ast.Module(body=nodes,type_ignores=[]),'exact-local-write','exec'),ns)
realwrite=os.write;realclose=os.close
for i,A in enumerate((ValueError,MemoryError,SystemExit)):
 for j,B in enumerate((ValueError,MemoryError,SystemExit)):
  a=A('body');b=B('cleanup');closed=[]
  def write(fd,data):raise a
  def close(fd):realclose(fd);closed.append(fd);raise b
  os.write=write;os.close=close
  try:
   try:ns['write'](D/('fatal-%d-%d'%(i,j)),b'opaque')
   except BaseException as e:
    selected=a if A in (MemoryError,SystemExit)else b if B in (MemoryError,SystemExit)else a
    ok(e is selected and len(closed)==1,'actual write/close fatal '+str((i,j)))
   else:raise AssertionError('unexpected successful write')
  finally:os.write=realwrite;os.close=realclose
ok(not any(n in sys.modules for n in ('numpy','torch','scipy')),'no numerical imports')
(D/'READBACK02.json').write_bytes(R.encode({'checks':len(checks),'checks_detail':checks,'actual_local_git_commands':commands,'recorded_pids_now_absent':sorted(pids),'recorded_groups_now_absent':sorted(groups),'cgroup_now_absent':terminal['cleanup']['cgroup'],'opaque_outcome_members':{k:hashes[outcome[k]]for k in ('claim_sha256','failed_sha256','checkpoint_manifest_sha256','checkpoint_state_sha256')},'native_pid_complete_history_claim':False,'no_checkpoint_deserialization':True}))
print(json.dumps({'checks':len(checks),'local_git_commands':len(commands),'native_pid_complete_history_claim':False}))
