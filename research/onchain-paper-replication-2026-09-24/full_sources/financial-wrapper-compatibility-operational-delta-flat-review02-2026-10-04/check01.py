"""Different-author metadata/source/opaque qualification, no runtime authority."""
from pathlib import Path
import ast,copy,gzip,hashlib,importlib.util,io,json,os,stat,sys,tarfile,traceback
D=Path(__file__).resolve().parent;B=D.parent;MAIN=B.parents[2];A=B/'financial-wrapper-compatibility-operational-delta-flat-successor02-2026-10-04';sys.path.insert(0,str(D));spec=importlib.util.spec_from_file_location('independent_flat',D/'restore01.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M);R=M.R;H=lambda b:hashlib.sha256(b).hexdigest();rows=[]
def ck(n,v,**kw):
 assert v,n;rows.append(dict(name=n,**kw));(D/'CHECKS01.json').write_text(json.dumps(rows,indent=2)+'\n')
def no(n,fn):
 try:fn()
 except BaseException as e:
  if not isinstance(e,Exception):raise
  rows.append({'name':n,'refused':type(e).__name__,'reason':str(e)});(D/'CHECKS01.json').write_text(json.dumps(rows,indent=2)+'\n')
 else:raise AssertionError(n)
source=(D/'restore01.py').read_text();old=(D/'ORIGINAL_restore01.py').read_text();inv=json.loads((D/'AUTHOR_SOURCE_INVERSE01.json').read_text());rebuilt=source
for e in reversed(inv['edits']):
 assert rebuilt[e['new_start']:e['new_end']]==e['new'];rebuilt=rebuilt[:e['new_start']]+e['old']+rebuilt[e['new_end']:]
ck('complete literal inverse',rebuilt==old and H(old.encode())=='b8c16007f3945e30d1a1a4889504f1ed5cfc77256f4c03f7cbd8a4a7ac28659d')
oldast=ast.parse(old);newast=ast.parse(source);oldf={x.name:ast.dump(x) for x in oldast.body if isinstance(x,ast.FunctionDef)};newf={x.name:ast.dump(x) for x in newast.body if isinstance(x,ast.FunctionDef)}
ck('changed functions independently enumerated',sorted(n for n in oldf if oldf[n]!=newf[n])==['authenticate_selected','run','selection_rows','validate_remote'])
ck('added functions independently enumerated',sorted(set(newf)-set(oldf))==['load_failed_capture','restore_failed_delta'])
for n,pin in M.PINS.items():ck('exact dependency:'+n,H((D/n).read_bytes())==pin and (D/n).read_bytes()==(A/n).read_bytes(),scope='byte pin only; watcher not independently accepted')
ck('exact source and author machine',H(source.encode())=='4832c8f2664f1e97c339a5b6c80fdde6f73a6ca808856deb6324608e8f2e290e' and H((D/'AUTHOR_MACHINE01.json').read_bytes())=='951535ba7e1607402ad9d6adb0a93dce68936fc9d9862e580ec68d6026d7ba20')
for n,pin in M.REQUIRED.items():
 p=MAIN/n;s=p.lstat();ck('actual Main selected:'+n,stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==pin['bytes'] and H(p.read_bytes())==pin['sha256'])
ck('exact15/507946',len(M.REQUIRED)==15 and sum(r['bytes'] for r in M.REQUIRED.values())==507946)
C=B/'financial-wrapper-compatibility-operational-delta-capture02-2026-10-04';F=B/'financial-wrapper-compatibility-operational-delta-failed-remote-capture02-2026-10-04';c,m=M.load_capture(C);fc,fm=M.load_failed_capture(F)
for label,capture,manifest in [('operational',c,m),('failed',fc,fm)]:
 snap=Path(capture['snapshot']);actual={str(p.relative_to(snap)) for p in snap.rglob('*')};ck(label+' complete snapshot membership',actual=={r['path'] for r in manifest['members']} and stat.S_IMODE(snap.stat().st_mode)==manifest['root_mode'])
 for r in manifest['members']:
  p=snap/r['path'];s=p.lstat();ck(label+' literal snapshot:'+r['path'],stat.S_IMODE(s.st_mode)==r['mode'] and ((r['kind']=='directory' and stat.S_ISDIR(s.st_mode)) or (r['kind']=='file' and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==r['bytes'] and H(p.read_bytes())==r['sha256'])))
orig=json.loads((F/'ORIGINAL_FAILED_ROOT_SCOPE43.json').read_bytes());root=Path(fc['original_root']);ck('failed complete root43',len(orig['members'])==43 and {str(p.relative_to(root)) for p in root.rglob('*')}=={r['path'] for r in fm['members']})
for r in orig['members']:
 p=root/r['path'];s=p.lstat();ck('actual original failed:'+r['path'],stat.S_IMODE(s.st_mode)==r['mode'] and ((r['kind']=='directory' and stat.S_ISDIR(s.st_mode)) or (r['kind']=='file' and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==r['bytes'] and H(p.read_bytes())==r['sha256'])))
for r in json.loads((C/'ORIGIN_MAP01.json').read_bytes())['origins']:
 p=Path(r['original']);s=p.lstat();ck('actual original operational:'+r['path'],stat.S_ISREG(s.st_mode) and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==r['original_mode'] and s.st_size==r['bytes'] and H(p.read_bytes())==r['sha256'])
failed=json.loads((root/'FAILED01.json').read_bytes());ck('original failure remains unknown/failed',failed['operations'][2]['exit'] is None and failed['operations'][2]['actual_reaped_exit']==0 and fc['Root_outer_exit']==1 and fc['historical_changed_directory_path_or_field'] is None and fc['actual_external_or_flat_receipt'] is None)
q={'remote_commit':'0'*40,'rows':[dict(path=n,**r) for n,r in sorted(M.REQUIRED.items())]};ck('source selection parser only',len(M.selection_rows(q))==15)
for i in range(15):
 z=copy.deepcopy(q);z['rows'][i]['sha256']='0'*64;no('each selection hash:'+str(i),lambda z=z:M.selection_rows(z))
for label,fn in [('missing row',lambda q:q['rows'].pop()),('duplicate row',lambda q:q['rows'].append(q['rows'][0])),('reversed rows',lambda q:q['rows'].reverse()),('float extent',lambda q:q['rows'][0].update(bytes=float(q['rows'][0]['bytes']))),('boolean extent',lambda q:q['rows'][0].update(bytes=True))]:
 z=copy.deepcopy(q);fn(z);no(label,lambda z=z:M.selection_rows(z))
no('missing actual remote',lambda:M.validate_remote({},q,'0'*64));no('genuine failed receipt not success',lambda:M.validate_remote(failed,q,'0'*64));no('null external pins',lambda:M.run(None,None));no('unknown external receipt hash missing body',lambda:M.run('0'*64,'0'*64));no('wrong failed scope',lambda:M.load_failed_capture(C));no('wrong operational scope',lambda:M.load_capture(F))
# Actual separate flat outputs from genuine frozen archives; independent canonical reconstruction.
owned=D/'roundtrip01';owned.mkdir(mode=0o700);samples=[]
def boundary():samples.append(M.W.census(owned))
results=[]
for bundle,capture,manifest,fn,leaf,archive in [(C,c,m,M.restore_delta,M.OUTPUT,'operational-delta01.tar.gz'),(F,fc,fm,M.restore_failed_delta,M.FAILED_OUTPUT,'failed-remote02.tar.gz')]:
 before=len(os.listdir('/proc/self/fd'));result=fn(bundle,capture,manifest,owned,boundary);dest=owned/leaf;meta=M.verify_flat(dest,result,capture,manifest,boundary);compressed=io.BytesIO()
 with gzip.GzipFile(filename='',mode='wb',fileobj=compressed,mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tar:
   for r in manifest['members']:
    info=tarfile.TarInfo(r['path']);info.mode=r['mode'];info.uid=info.gid=info.mtime=0;info.uname=info.gname=''
    if r['kind']=='directory':info.type=tarfile.DIRTYPE;tar.addfile(info)
    else:
     p=dest/meta['flat_members'][r['path']];body=p.read_bytes();ck('restored body:'+leaf+':'+r['path'],len(body)==r['bytes'] and H(body)==r['sha256'] and stat.S_IMODE(p.stat().st_mode)==0o600);info.size=len(body);tar.addfile(info,io.BytesIO(body))
 ck('canonical archive exact:'+leaf,compressed.getvalue()==(bundle/archive).read_bytes());ck('balanced real descriptors:'+leaf,len(os.listdir('/proc/self/fd'))==before);results.append(result)
 no('fresh namespace mandatory:'+leaf,lambda bundle=bundle,capture=capture,manifest=manifest,fn=fn:fn(bundle,capture,manifest,owned,boundary))
(D/'ROUNDTRIP01.json').write_text(json.dumps({'results':results,'samples':samples,'regular':64,'metadata_files':2,'actual_remote_receipt':None,'root_restore':False},indent=2)+'\n')
# Preserve first complete scope and second partial output with exact actual fatal cleanup.
partial=D/'partial01';partial.mkdir(mode=0o700);first=M.restore_delta(C,c,m,partial,lambda:None);create=R.FlatOutput.create;close=R.FlatOutput.close;primary=MemoryError('review primary after real create');secondary=SystemExit('review secondary after real close');count=[];closed=[];before=len(os.listdir('/proc/self/fd'))
def failcreate(self,n,b):
 create(self,n,b);count.append(n)
 if len(count)==2:raise primary
def failclose(self):close(self);closed.append(True);raise secondary
R.FlatOutput.create=failcreate;R.FlatOutput.close=failclose
try:
 try:M.restore_failed_delta(F,fc,fm,partial,lambda:None)
 except BaseException as e:ck('real partial exact first fatal',e is primary,traceback=traceback.format_exc())
 else:raise AssertionError('missing injected fatal')
finally:R.FlatOutput.create=create;R.FlatOutput.close=close
ck('both completed and partial evidence retained',len(list((partial/M.OUTPUT).iterdir()))==34 and len(list((partial/M.FAILED_OUTPUT).iterdir()))==2 and closed==[True] and len(os.listdir('/proc/self/fd'))==before)
for i,P in enumerate((ValueError,MemoryError,SystemExit)):
 for j,S in enumerate((ValueError,MemoryError,SystemExit)):
  p=P('primary');s=S('secondary');fd=os.open(partial/f'fd-{i}-{j}',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);before=len(os.listdir('/proc/self/fd'))
  def action():os.close(fd);raise s
  try:R._cleanup((action,),primary=p)
  except BaseException as e:
   fatal=next((x for x in (p,s) if isinstance(x,MemoryError) or not isinstance(x,Exception)),None);ck(f'cleanup exact fatal {i}/{j}',e is fatal if fatal is not None else isinstance(e,M.W.IO.CleanupFailure))
  else:raise AssertionError('cleanup accepted')
  ck(f'cleanup real FD close {i}/{j}',len(os.listdir('/proc/self/fd'))==before-1)
# Actual read type/link/cap refusals independent of watcher internals.
negative=D/'negative01';negative.mkdir(mode=0o700);(negative/'body').write_bytes(b'opaque');os.link(negative/'body',negative/'hard');(negative/'link').symlink_to(negative/'body');os.mkfifo(negative/'fifo')
for n in ('body','hard','link','fifo'):no('read refuses type/link:'+n,lambda n=n:R.read(negative,n))
(negative/'single').write_bytes(b'opaque');no('read finite file cap',lambda:R.read(negative,'single',limit=5));no('traversal refused',lambda:R.read(negative,'../outside'));no('changed extent/hash byte refused',lambda:M.verify_flat(D/'witness-owned01'/M.FAILED_OUTPUT,json.loads((D/'WITNESS01.json').read_bytes()).get('unused',results[1]),fc,fm,lambda:None))
ck('no generated runtime authority',(D/'FLAT_RECOVERY01.json').exists() is False and (D/'FLAT_INTENT01.json').exists() is False)
print(json.dumps({'positive_or_refusal_checks':len(rows),'known_currentness_witness':'WITHHELD','no_actual_run_entry':True}))
