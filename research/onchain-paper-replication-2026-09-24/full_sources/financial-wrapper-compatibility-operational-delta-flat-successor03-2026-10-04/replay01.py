from pathlib import Path
import importlib.util,json,hashlib,os,stat,copy,io,gzip,tarfile,ast
O=Path(__file__).resolve().parent;F=O.parent;s=importlib.util.spec_from_file_location('twoflat',O/'restore01.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M);R=M.R;h=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(n,v):
 assert v,n;checks.append(n)
def refuse(n,f):
 try:f()
 except (ValueError,KeyError,TypeError,FileNotFoundError,FileExistsError,EOFError):checks.append(n)
 else:raise AssertionError(n)
B=F/'financial-wrapper-compatibility-operational-delta-capture02-2026-10-04';FB=F/'financial-wrapper-compatibility-operational-delta-failed-remote-capture02-2026-10-04';c,m=M.load_capture(B);fc,fm=M.load_failed_capture(FB)
ck('41/33+42/31',len(m['members'])==41 and len(fm['members'])==42)
q={'remote_commit':'0'*40,'rows':[dict(path=n,**p) for n,p in sorted(M.REQUIRED.items())]};ck('15rows',len(M.selection_rows(q))==15)
for label,mut in [('missing',lambda q:q['rows'].pop()),('extra',lambda q:q['rows'].append(q['rows'][0])),('reorder',lambda q:q['rows'].reverse()),('wronghash',lambda q:q['rows'][0].update(sha256='0'*64)),('floatbyte',lambda q:q['rows'][0].update(bytes=float(q['rows'][0]['bytes']))),('boolbyte',lambda q:q['rows'][0].update(bytes=True))]:
 z=copy.deepcopy(q);mut(z);refuse(label,lambda z=z:M.selection_rows(z))
refuse('noactualreceipt',lambda:M.validate_remote({},q,'0'*64));refuse('wrongrole',lambda:M.load_failed_capture(B));refuse('oldrole',lambda:M.load_capture(FB));refuse('nullfuturepin',lambda:M.run(None,None))
owned=O/'replay-owned01';owned.mkdir(mode=0o700);samples=[]
def boundary():samples.append(M.W.census(owned))
r=M.restore_delta(B,c,m,owned,boundary);fr=M.restore_failed_delta(FB,fc,fm,owned,boundary)
for dest,rr,cap,man,archive in [(owned/M.OUTPUT,r,c,m,B/'operational-delta01.tar.gz'),(owned/M.FAILED_OUTPUT,fr,fc,fm,FB/'failed-remote02.tar.gz')]:
 meta=M.verify_flat(dest,rr,cap,man,boundary);out=io.BytesIO()
 with gzip.GzipFile(filename='',mode='wb',fileobj=out,mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as t:
   for row in man['members']:
    a=tarfile.TarInfo(row['path']);a.mode=row['mode'];a.uid=a.gid=a.mtime=0;a.uname=a.gname=''
    if row['kind']=='directory':a.type=tarfile.DIRTYPE;t.addfile(a)
    else:
     p=dest/meta['flat_members'][row['path']];b=p.read_bytes();ck('body:'+row['path'],h(b)==row['sha256'] and len(b)==row['bytes'] and stat.S_IMODE(p.stat().st_mode)==0o600);a.size=len(b);t.addfile(a,io.BytesIO(b))
 ck('canonical:'+dest.name,out.getvalue()==archive.read_bytes())
refuse('reusefirst',lambda:M.restore_delta(B,c,m,owned,boundary));refuse('reusesecond',lambda:M.restore_failed_delta(FB,fc,fm,owned,boundary))
# Corrupt only owned fixture after successful verification; original scopes remain frozen.
meta=json.loads((owned/M.FAILED_OUTPUT/fr['metadata_file']).read_bytes());leaf=next(iter(meta['flat_members'].values()));(owned/M.FAILED_OUTPUT/leaf).write_bytes(b'changed');refuse('current-body-corruption',lambda:M.verify_flat(owned/M.FAILED_OUTPUT,fr,fc,fm,boundary))
# Complete first output is retained when second restoration fails after a real file creation.
partial=O/'replay-partial01';partial.mkdir(mode=0o700);pr=M.restore_delta(B,c,m,partial,lambda:None);primary=MemoryError('injected-after-real-second-body');secondary=SystemExit('injected-after-real-close');create=R.FlatOutput.create;close=R.FlatOutput.close;count=[0];closed=[]
def fail_create(self,name,body):
 create(self,name,body);count[0]+=1
 if count[0]==2:raise primary
def fail_close(self):
 close(self);closed.append(True);raise secondary
R.FlatOutput.create=fail_create;R.FlatOutput.close=fail_close
try:
 try:M.restore_failed_delta(FB,fc,fm,partial,lambda:None)
 except BaseException as e:ck('partial-firstfatal',e is primary)
 else:raise AssertionError('partialfatal accepted')
finally:R.FlatOutput.create=create;R.FlatOutput.close=close
ck('partialretained',len(list((partial/M.FAILED_OUTPUT).iterdir()))==2 and (partial/M.OUTPUT/pr['metadata_file']).is_file() and bool(closed))
# All nine original primary/cleanup classes with genuine owned close, no double close.
for i,a in enumerate([ValueError('p'),MemoryError('p'),SystemExit('p')]):
 for j,b in enumerate([ValueError('c'),MemoryError('c'),SystemExit('c')]):
  fd=os.open(owned/f'fd-{i}-{j}',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  def action(fd=fd,e=b):os.close(fd);raise e
  try:
   R._cleanup((action,),primary=a);raise a
  except BaseException as e:
   expected=next((v for v in [a,b] if isinstance(v,MemoryError) or not isinstance(v,Exception)),None)
   ck(f'fd-fatal-{i}-{j}', e is expected if expected is not None else isinstance(e,M.W.IO.CleanupFailure))
  try:os.fstat(fd)
  except OSError:checks.append(f'fdclosed-{i}-{j}')
  else:raise AssertionError('leak')
# Tiny malformed archive domains, no live receipt or original modification.
tree=owned/'tiny';tree.mkdir(mode=0o700);(tree/'opaque').write_bytes(b'opaque\x00\xff');tm=R.scan(tree);arc=owned/'tiny.gz';ai=R.pack(tree,tm,arc);raw=arc.read_bytes()
for label,b in [('truncated',raw[:-4]),('trailing',raw+b'extra'),('magic',b'X'+raw[1:])]:
 p=owned/(label+'.gz');p.write_bytes(b);d=owned/label;d.mkdir(mode=0o700);info=dict(ai,bytes=len(b),sha256=h(b))
 try:R.restore(p,info,tm,d)
 except Exception as e:checks.append('frame:'+label);(owned/(label+'.err')).write_text(type(e).__name__+'\n')
 else:raise AssertionError(label)
ck('originalsunchanged',R.digest(R.read(B,'CAPTURE01.json'))==M.CAPTURE and R.digest(R.read(FB,'CAPTURE01.json'))==M.FAILED_CAPTURE)
result={'checks':len(checks),'names':checks,'local_two_scope_results':[r,fr],'sampled_observations':samples,'actual_remote_receipt':None,'actual_root_restore':False,'partial_failure_retained':True};(O/'REPLAY_CONTROLS01.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(checks),'controls; actual owned64bodies+2metadata roundtrip')
