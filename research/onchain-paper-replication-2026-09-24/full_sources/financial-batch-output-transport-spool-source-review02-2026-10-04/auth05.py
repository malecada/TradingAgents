import ast,dataclasses,difflib,hashlib,json,os,stat,sys
from pathlib import Path
H=Path(__file__).resolve().parent;F=H.parent;A=F/'financial-batch-output-transport-spool-preparation02-2026-10-04';O=F/'financial-batch-output-transport-spool-preparation01-2026-10-04';V=F/'financial-batch-output-transport-spool-source-review01-2026-10-04';sys.path.insert(0,str(A));import spool04 as S
sha=lambda b:hashlib.sha256(b).hexdigest();checks=0

def ok(v):
 global checks
 assert v;checks+=1
for root,want,count in [(A,'a165e90de609e87d92f602bb4a845f538eed6e1f522aa8e471ab798d8ad70273',520),(O,'1fd3b54dc0bfefeba6bc69c2857ae2564145c86160030977a61c386c84714894',172),(V,'43a824fc32de494f2ef76c442cf72db1dd581abc53d88a5e95dd1d5db6e1e698',453)]:
 ok(sha((root/'MANIFEST01.json').read_bytes())==want);rows=json.loads((root/'MANIFEST01.json').read_text())['members'];ok(len(rows)==count)
 ok(sorted(str(p.relative_to(root)) for p in root.rglob('*') if p!=root/'MANIFEST01.json')==sorted(r['path'] for r in rows))
 for r in rows:
  p=root/r['path'];s=p.lstat();ok(stat.S_IMODE(s.st_mode)==r['mode'])
  if r['kind']=='file':b=p.read_bytes();ok(stat.S_ISREG(s.st_mode) and len(b)==r['bytes'] and sha(b)==r['sha256'])
  elif r['kind']=='directory':ok(stat.S_ISDIR(s.st_mode))
  else:ok(r['kind']=='symlink' and stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target'])
old=(O/'spool02.py').read_text();new=(A/'spool04.py').read_text()
ok(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='original01/spool02.py',tofile='successor02/spool04.py'))==(A/'INVERSE01.diff').read_text())
# Reverse the exact unified hunks independently into original source.
lines=new.splitlines(True);patch=(A/'INVERSE01.diff').read_text().splitlines(True);result=[];at=0;i=2
import re
while i<len(patch):
 header=patch[i];m=re.fullmatch(r'@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@.*\n',header);ok(m is not None);start=int(m.group(2))-1;result.extend(lines[at:start]);at=start;i+=1
 while i<len(patch) and not patch[i].startswith('@@'):
  q=patch[i];i+=1
  if q[0] in ' +':ok(lines[at]==q[1:]);at+=1
  if q[0] in ' -':result.append(q[1:])
result.extend(lines[at:]);back=''.join(result);ok(back==old);ok(ast.dump(ast.parse(back))==ast.dump(ast.parse(old)))
# Every original unchanged top-level/class AST remains exact.
def functions(text):
 t=ast.parse(text);out={}
 for n in t.body:
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):out[n.name]=ast.dump(n)
  if isinstance(n,ast.ClassDef):
   for m in n.body:
    if isinstance(m,ast.FunctionDef):out[n.name+'.'+m.name]=ast.dump(m)
 return out
x,y=functions(old),functions(new);changed={k for k in set(x)|set(y) if x.get(k)!=y.get(k)}
ok(changed==set(json.loads((A/'INVERSE01.json').read_text())['changed_functions']))
ok((A/'owned_io.py').read_bytes()==(O/'owned_io.py').read_bytes());ok(sha((A/'owned_io.py').read_bytes())=='09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb')
# All malformed Ack field types rejected, including equality aliases and nested
# Recovery Ack shape; these are pure protocol metadata, not research objects.
a=S.Ack('a'*64,0,0,1,'b'*64,'c'*64);ok(S.valid_ack(a))
for field in ('page','chunk','size'):
 for value in (False,True,0.0,1.0,'0',None,[],{},-1):
  ok(not S.valid_ack(dataclasses.replace(a,**{field:value})))
for field in ('plan','sha256','receipt_sha256'):
 for value in (None,True,0,b'a'*64,'A'*64,'a'*63,'a'*65,[]):ok(not S.valid_ack(dataclasses.replace(a,**{field:value})))
ok(not S.valid_ack({}));ok(not S.valid_ack(None))
# Source construction draft retained, not executed or silently repaired.
draft=(A/'spool03.py').read_bytes();ok(len(draft)>0)
try:ast.parse(draft)
except (IndentationError,SyntaxError):ok(True)
else:raise AssertionError('expected preserved unexecuted draft syntax error')
# Genuine owned walk fatal plus secondary close errors: every acquired walker FD
# closes, original KeyboardInterrupt wins, and the actual spool becomes failed.
p=S.Plan((S.Member(0,0,1,S.digest(b'x')),),1,0,0);l,a0=p.required();p=dataclasses.replace(p,logical_reservation=l,allocated_reservation=a0)
r=H/'walk-fatal';r.mkdir(mode=0o700);s=S.Spool(r,p);real_open=os.open;real_close=os.close;opened=[];closed=[];primary=KeyboardInterrupt('walker original fatal');counter=[0]
def op(*args,**kw):
 counter[0]+=1
 if counter[0]==4:raise primary
 fd=real_open(*args,**kw);opened.append(fd);return fd
def cl(fd):real_close(fd);closed.append(fd);raise OSError('real close completed, secondary uncertainty')
try:
 os.open=op;os.close=cl
 try:s.transfer(b'x',None,None)
 except BaseException as e:ok(e is primary)
 else:raise AssertionError('missing fatal')
finally:os.open=real_open;os.close=real_close
ok(s.failed and set(opened)==set(closed) and len(opened)==3)
for fd in opened:
 try:os.fstat(fd)
 except OSError:ok(True)
 else:raise AssertionError('walker fd leaked')
s.close()
# Real cleanup ancestor replacement is now caught by the postcleanup walk, and
# remains RECOVERED (not ELIGIBLE) with a terminal failure. SP4 is separate.
parent=H/'cleanup-parent';parent.mkdir();r=parent/'root';r.mkdir(mode=0o700);s=S.Spool(r,p);moved=H/'cleanup-parent-moved'
def cleanup():parent.rename(moved);parent.symlink_to(moved.name,target_is_directory=True)
def ack(i,m,b):return S.Ack(i,m.page,m.chunk,m.size,m.sha256,'a'*64)
try:s.transfer(b'x',ack,lambda a:S.Recovery(a,b'x'),cleanup)
except (OSError,ValueError):ok(s.failed and s.states==('RECOVERED',) and 'terminal' in s._sealed)
else:raise AssertionError('cleanup redirect accepted')
s.close()
# No admission/scientific libraries were loaded by the actual source controls.
ok(all(n not in sys.modules for n in ('numpy','torch','pandas','tradingagents.research.lifecycle')))
(H/'AUTH05.json').write_text(json.dumps({'checks':checks,'all_author_and_prior_members':1145,'literal_and_AST_inverse':True,'unchanged_IO':True,'old_draft_preserved':True,'walk_fatal_fd_count':len(opened),'SP1_SP2_SP3_corrected':True,'SP4_unresolved':True},sort_keys=True,indent=2)+'\n');print(checks,'checks passed')
