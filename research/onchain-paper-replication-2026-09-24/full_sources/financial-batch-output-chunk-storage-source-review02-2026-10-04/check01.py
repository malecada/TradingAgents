import ast,copy,hashlib,importlib.util,io,json,os,stat,sys,types
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;A=B/'financial-batch-output-chunk-storage-preparation02-2026-10-04';OLD=B/'financial-batch-output-chunk-storage-preparation01-2026-10-04';REVIEW=B/'financial-batch-output-chunk-storage-source-review01-2026-10-04';checks=[];sha=lambda b:hashlib.sha256(b).hexdigest()
def ok(v,n):assert v,n;checks.append(n)
def refuse(call,n,allowed=(ValueError,KeyError,TypeError,FileNotFoundError)):
 try:call()
 except allowed as e:ok(True,n);return e
 else:raise AssertionError(n)
def authenticate(root,name,pin):
 raw=(root/name).read_bytes();ok(sha(raw)==pin,'exact seal '+root.name);m=json.loads(raw);actual=[]
 def walk(p,rel):
  s=p.lstat();r={'path':rel,'mode':stat.S_IMODE(s.st_mode)}
  if stat.S_ISLNK(s.st_mode):r.update(kind='symlink' if any(x['kind']=='symlink' for x in m['members']) else 'lexical-symlink',target=os.readlink(p))
  elif stat.S_ISDIR(s.st_mode):
   r['kind']='directory'
   for c in sorted(p.iterdir()):walk(c,rel+'/'+c.name)
  else:
   ok(stat.S_ISREG(s.st_mode) and s.st_size<=4194304,'bounded regular evidence');b=p.read_bytes();r.update(kind='file',bytes=len(b),sha256=sha(b))
  actual.append(r)
 for p in sorted(root.iterdir()):
  if p.name!=name:walk(p,p.name)
 ok(sorted(actual,key=lambda x:x['path'])==m['members'],'complete seal membership '+root.name);return m
oldm=authenticate(OLD,'MANIFEST01.json','1181852868d880e624caf3e4a3982f6bd27301983cc3fe2e7a2a0c92f6e3ef8d');newm=authenticate(A,'MANIFEST02.json','a513146948a0c469120eaa26844e2298cc5350e0135742c5bbe7d411c9c4238e');reviewm=authenticate(REVIEW,'MANIFEST01.json','21c95e8ca55a7c76f7eb6cdb4cd293e1efb7f77d0122587dd67a2cb92f22e1f0');ok(sha((REVIEW/'WITNESSES01.json').read_bytes())=='c7355b108ef4af2311b59653bb8f54491b7a15c29acd7349a1e813cd25c7bbd6','genuine old findings');pair=[REVIEW/'ownership-hardlink'/x for x in ['start.json','page-0000.json']];ok(pair[0].stat().st_ino==pair[1].stat().st_ino and all(p.stat().st_nlink==2 for p in pair),'old real hardlink pair unchanged')
inverses=json.loads((A/'INVERSE01.json').read_bytes())
for name,v in inverses.items():
 raw=(A/name).read_bytes();oldraw=(OLD/name).read_bytes();ok(sha(raw)==v['successor_sha256'] and sha(oldraw)==v['original_sha256'],'literal source pins '+name);s=raw.decode()
 for e in reversed(v['edits']):ok(s.count(e['after'])==1,'one inverse edit '+name);s=s.replace(e['after'],e['before'])
 ok(s.encode()==oldraw and ast.dump(ast.parse(s))==ast.dump(ast.parse(oldraw)),'full byte AST inverse '+name)
# Each module uses its real unchanged IO imports and its own actual codec module.
sys.path.insert(0,str(A));import recovery04 as R
import owned_io as IO

def module(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
oldC=module(OLD/'codec01.py','old_codec');newC=module(A/'codec01.py','new_codec');sys.modules['codec01']=oldC;oldL=module(OLD/'local_store01.py','old_local');sys.modules['codec01']=newC;newL=module(A/'local_store01.py','new_local')
d={'schema_version':1,'kind':'mcm-batch-output-bytes','role':'mcm-output','dtype':'<f4','shape':[1,32],'order':'C','scope':{k:'a'*64 for k in newC.SCOPE},'motifs':32,'spent_samples':512};raw=bytes(range(128));files={};terminal=newC.encode_stream(io.BytesIO(raw),d,lambda n,b:files.setdefault(n,b),chunk_bytes=32)
redgreen={}
# CS1 exact old wrong-graph bypass -> successor refusal; positive expectation frozen against reader/provisional mutation.
for label,C in [('old',oldC),('new',newC)]:
 expected=copy.deepcopy(d);expected['scope']['graph']='b'*64
 def reader(n):expected['scope']['graph']='a'*64;return files[n]
 if label=='old':res=C.verify_stream(reader,terminal,expected);ok(res['status']=='complete-byte-proof-only','old mutable descriptor bypass actual');redgreen['CS1_old']='incorrect initial graph accepted'
 else:refuse(lambda:C.verify_stream(reader,terminal,expected),'new old mutable descriptor bypass refused');redgreen['CS1_new']='incorrect initial graph refused'
for callback in ['reader','provisional']:
 expected=copy.deepcopy(d);out=[]
 def mutate():expected['scope']['graph']='b'*64;expected['dtype']='invalid';expected['shape'][0]=999
 def reader(n):
  if callback=='reader':mutate()
  return files[n]
 def deliver(b):out.append(b);mutate()
 result=newC.verify_stream(reader,terminal,expected,deliver);ok(b''.join(out)==raw and result['raw_sha256']==sha(raw),'private expectation survives '+callback+' mutation')
# CS2 all exception families poison; original witness retains exact fatal and cannot retry.
class DirectBase(BaseException):pass
for index,T in enumerate([ValueError,RuntimeError,MemoryError,KeyboardInterrupt,SystemExit,GeneratorExit,DirectBase]):
 root=H/('verify-'+str(index));root.mkdir(mode=0o700);error=T('exact original callback');prefix=[]
 with newL.LocalStore(root) as store:
  p=newC.encode_stream(io.BytesIO(raw),d,store.put,chunk_bytes=32)
  def deliver(b):prefix.append(b);raise error
  try:store.verify(p,d,deliver)
  except BaseException as e:ok(e is error,'original verify exception exact '+T.__name__)
  else:raise AssertionError('failure swallowed')
  ok(store.poisoned and len(prefix)==1,'verify terminal poison '+T.__name__);refuse(lambda:store.verify(p,d),'never verify again '+T.__name__);refuse(lambda:store.put('page-0001.json',b'x'),'never put again '+T.__name__)
root=H/'old-verify';root.mkdir(mode=0o700)
with oldL.LocalStore(root) as store:
 p=oldC.encode_stream(io.BytesIO(raw),d,store.put,chunk_bytes=32);error=KeyboardInterrupt('old exact')
 try:store.verify(p,d,lambda b:(_ for _ in ()).throw(error))
 except KeyboardInterrupt as e:ok(e is error,'old original fatal retained')
 ok(not store.poisoned and store.verify(p,d)['status']=='complete-byte-proof-only','old fatal retry bypass actual');redgreen['CS2_old']='retry accepted';redgreen['CS2_new']='all7 exception families poisoned/retry refused'
# CS3 original exact scaled8KiB real overshoot versus new initial headroom refusal.
root=H/'old-scaled';root.mkdir(mode=0o700);oldlimit=oldL.LIMIT;oldL.LIMIT=8192
try:
 with oldL.LocalStore(root) as store:
  store.put('start.json',b'x');refuse(lambda:store.put('terminal.json',b'y'),'old postwrite allocated refusal');allocated=root.stat().st_blocks*512+sum(p.stat().st_blocks*512 for p in root.iterdir());ok(allocated==12288,'original scaled retained allocation witness');redgreen['CS3_old']={'limit':8192,'retained_allocated':allocated}
finally:oldL.LIMIT=oldlimit
root=H/'new-scaled8192';root.mkdir(mode=0o700);newlimit=newL.LIMIT;newL.LIMIT=8192
try:refuse(lambda:newL.LocalStore(root),'new scaled initial reservation refusal');ok(not list(root.iterdir()),'new scaled no file created');redgreen['CS3_new_initial']={'limit':8192,'retained_allocated':root.stat().st_blocks*512}
finally:newL.LIMIT=newlimit
# Admit exactly one next-file reservation and refuse the second before names/open/write.
root=H/'new-one-reservation';root.mkdir(mode=0o700);initial=root.stat().st_blocks*512+newL.DIRECTORY_HEADROOM+newL.SCRATCH_HEADROOM;cost=2*newL.BLOCK;newL.LIMIT=initial+cost
try:
 with newL.LocalStore(root) as store:
  store.put('start.json',b'x');before=(store.reserved,store.reserved_logical,store.total,set(store.names));refuse(lambda:store.put('terminal.json',b'y'),'new projected second reservation refuses');ok((store.reserved,store.reserved_logical,store.total,set(store.names))==before and not (root/'terminal.json').exists(),'precreate refusal no extra reservation/body');ok(store.poisoned and (root/'start.json').read_bytes()==b'x','first retained no deletion')
 redgreen['CS3_one_reservation']={'initial':initial,'cost':cost,'scaled_limit':newL.LIMIT,'retained_files':sorted(p.name for p in root.iterdir())}
finally:newL.LIMIT=newlimit
for size in [1,newL.BLOCK-1,newL.BLOCK,newL.BLOCK+1,newC.FILE]:
 expected=((size+newL.BLOCK-1)//newL.BLOCK)*newL.BLOCK+newL.ENTRY_HEADROOM
 ok(newL.project(0,0,size,expected)==(expected,size),'roundup exact '+str(size));refuse(lambda:newL.project(0,0,size,expected-1),'one unit headroom insufficient '+str(size))
for args in [(True,0,1,1000000),(0,False,1,1000000),(0,0,True,1000000),(0,0,0,1000000),(0,0,newC.FILE+1,10000000)]:refuse(lambda:newL.project(*args),'strict reservation scalar types')
# Controlled scalar disk availability seam, no claim that actual disk is exhausted.
root=H/'floor-headroom';root.mkdir(mode=0o700);original_shutil=newL.shutil
with newL.LocalStore(root) as store:
 projected,_=newL.project(store.reserved,store.reserved_logical,1,newL.LIMIT);before=store.reserved;newL.shutil=types.SimpleNamespace(disk_usage=lambda p:types.SimpleNamespace(free=newL.FLOOR+projected-1))
 try:refuse(lambda:store.put('start.json',b'x'),'floor plus whole reservation refuses before create');ok(not list(root.iterdir()) and store.reserved==before and store.poisoned,'low-headroom no actual write')
 finally:newL.shutil=original_shutil
# Original put firstfatal/cleanup with monotone spent reservation after write failure.
original_os=newL.os
for i,first in enumerate([MemoryError,KeyboardInterrupt,SystemExit]):
 for j,second in enumerate([OSError,MemoryError,KeyboardInterrupt]):
  root=H/f'put-fatal-{i}-{j}';root.mkdir(mode=0o700);store=newL.LocalStore(root);primary=first('write');secondary=second('close');before=store.reserved;fds=[]
  def write(fd,b):fds.append(fd);raise primary
  def close(fd):os.close(fd);raise secondary
  newL.os=types.SimpleNamespace(**{k:getattr(os,k) for k in dir(os)});newL.os.write=write;newL.os.close=close
  try:
   try:store.put('start.json',b'opaque')
   except BaseException as e:ok(e is primary,'put firstfatal exact retained');ok(store.reserved==before+cost and store.reserved_logical==6 and store.names=={'start.json'} and store.poisoned,'failed reservation no refund');ok(all(not Path('/proc/self/fd/'+str(fd)).exists() for fd in fds),'real write fd absent')
   else:raise AssertionError('fatal swallowed')
  finally:newL.os=original_os;store.close()
# Verification callback fatal followed by real directory-close errors under the actual context manager.
for index,first in enumerate([ValueError,MemoryError,KeyboardInterrupt,SystemExit]):
 root=H/f'verify-close-{index}';root.mkdir(mode=0o700);primary=first('callback');secondary=MemoryError('directory close');store=newL.LocalStore(root);p=newC.encode_stream(io.BytesIO(raw),d,store.put,chunk_bytes=32);fd=store.fd
 def close(fd):os.close(fd);raise secondary
 newL.os=types.SimpleNamespace(**{k:getattr(os,k) for k in dir(os)});newL.os.close=close
 try:
  try:
   with store:store.verify(p,d,lambda b:(_ for _ in ()).throw(primary))
  except BaseException as e:ok(e is (secondary if first is ValueError else primary),'context firstfatal precedence exact');ok(store.poisoned and store.closed and not Path('/proc/self/fd/'+str(fd)).exists(),'verify failure terminal and actual fd closed')
  else:raise AssertionError('missing fatal')
 finally:newL.os=original_os
# Small multi-page both-dtype checks, metadata/record mutation and exact local full-member refusal.
for role,dtype in [('score-batches','<f8'),('mcm-output','<f4')]:
 spec=copy.deepcopy(d);spec.update(role=role,dtype=dtype,shape=[17,32]);raw2=bytes(i%251 for i in range(newC.descriptor(spec)));f={};p=newC.encode_stream(io.BytesIO(raw2),spec,lambda n,b:f.setdefault(n,b),chunk_bytes=32);out=[];res=newC.verify_stream(f.__getitem__,p,spec,out.append);ok(b''.join(out)==raw2 and res['members']==sorted(f),'full bothdtype ordered multi-page payload')
 for name in f:
  bad=dict(f);bad[name]=bad[name][:-1];refuse(lambda:newC.verify_stream(bad.__getitem__,p,spec),'every referenced truncation '+role+' '+name)
 for key,value in [('dtype','>f4'),('order','F'),('motifs',31),('spent_samples',511),('shape',[17,31])]:
  bad=copy.deepcopy(spec);bad[key]=value;refuse(lambda:newC.verify_stream(f.__getitem__,p,bad),'descriptor semantics '+key)
 terminal_dict=json.loads(f['terminal.json']);terminal_dict['pages'].reverse();bad=dict(f);bad['terminal.json']=newC.canonical(terminal_dict);refuse(lambda:newC.verify_stream(bad.__getitem__,newC.sha(bad['terminal.json']),spec),'rehashed page order refusal')
for variant in ['extra','hardlink','symlink','mode']:
 root=H/('member-'+variant);root.mkdir(mode=0o700)
 with newL.LocalStore(root) as store:
  p=newC.encode_stream(io.BytesIO(raw),d,store.put,chunk_bytes=32)
  if variant=='extra':(root/'unexpected').write_bytes(b'x')
  elif variant=='hardlink':os.link(root/'start.json',root/'retained-hardlink')
  elif variant=='symlink':(root/'literal').symlink_to('absent')
  else:(root/'start.json').chmod(0o644)
  refuse(lambda:store.verify(p,d),'actual member '+variant+' refusal');ok(store.poisoned,'member-check failure terminal poison');refuse(lambda:store.verify(p,d),'member failed instance cannot retry')
refuse(lambda:newC.publish_live(None,None,None),'unconditional live publication refusal')
for n in ['codec01.py','local_store01.py','INVERSE01.json','PROTOCOL02.md','MACHINE02.json','MANIFEST02.json']:
 with (H/('ORIGINAL_'+n)).open('xb') as f:f.write((A/n).read_bytes())
result={'schema_version':1,'checks':len(checks),'check_names':checks,'old_member_count':len(oldm['members']),'new_member_count':len(newm['members']),'review01_original_count':len(reviewm['members']),'red_green':redgreen,'production64MiB_capacity_measured':False,'filesystem_universal_upper_bound_verified':False,'live_publication_admitted':False,'floor_negative_uses_scalar_testdouble':True,'old_hardlink_group_preserved':True}
with (H/'READBACK01.json').open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'checks':len(checks),'readback_sha256':sha((H/'READBACK01.json').read_bytes()),'bytes':(H/'READBACK01.json').stat().st_size}))
