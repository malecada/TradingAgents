from pathlib import Path
import ast,atexit,hashlib,importlib.util,json,os,stat,sys,time
H=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes/research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-preclaim-correction02-2026-10-04');rows=[];W=H/'owned-currentness05';W.mkdir(mode=0o700)
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
old=load('preclaim_old_pc1',H/'ORIGINAL_preclaim01.py');new=load('preclaim_corrected_pc2',H/'preclaim01.py');sha=lambda b:hashlib.sha256(b).hexdigest()
def put(n,v):(H/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def ck(n,v):rows.append({'case':n,'passed':bool(v)});assert v,n
atexit.register(lambda:put('CURRENTNESS_PROGRESS05.json',rows))
results=[];realclose=os.close
for kind in ('bytes','mode','replace','symlink','remove','deadline'):
 for label,m in (('original',old),('corrected',new)):
  d=W/(kind+'-'+label);d.mkdir(mode=0o700);a=d/'earlier';b=d/'later';a.write_bytes(b'original');b.write_bytes(b'later');r=m.Reader();r.read(a);r.read(b);ino=b.stat().st_ino;closed=[];changed=[False]
  def close(fd):
   st=os.fstat(fd);is_later=st.st_ino==ino;realclose(fd);closed.append(fd)
   if is_later and not changed[0]:
    changed[0]=True
    if kind=='bytes':
     a.write_bytes(b'changed!');s=a.stat();os.utime(a,ns=(s.st_atime_ns,s.st_mtime_ns+1000000000))
    elif kind=='mode':a.chmod(0o600 if stat.S_IMODE(a.stat().st_mode)!=0o600 else 0o644)
    elif kind=='replace':a.rename(d/'original-earlier');a.write_bytes(b'original')
    elif kind=='symlink':a.rename(d/'original-earlier');a.symlink_to(d/'original-earlier')
    elif kind=='remove':a.rename(d/'original-earlier')
    else:r.deadline=time.monotonic()-1
  error=None;m.os.close=close
  try:r.finish()
  except BaseException as e:error=e
  finally:m.os.close=realclose
  ck(kind+' mutation inside later actual cleanup '+label,changed[0]);ck(kind+' all actual descriptors closed once '+label,len(closed)==len(a.parts)+len(b.parts))
  ck(kind+' expected originalRED/correctedGREEN '+label,(error is None) if label=='original' and kind!='deadline' else isinstance(error,(ValueError,OSError)))
  absent=[]
  for fd in closed:
   try:os.fstat(fd)
   except OSError:absent.append(fd)
  ck(kind+' all descriptor numbers absent '+label,len(absent)==len(closed))
  results.append({'case':kind,'version':label,'source_sha256':sha(Path(m.__file__).read_bytes()),'mutation_during_later_cleanup':changed[0],'returned_success':error is None,'error_type':None if error is None else type(error).__name__,'error_message':None if error is None else str(error),'cached_original_hex':r.cache[a].hex(),'all_opened_FDs_closed_once':len(closed),'no_post_return_or_continuous_exclusion_claim':True})
for m in (old,new):
 d=W/('intact-'+('old' if m is old else 'new'));d.mkdir();a=d/'earlier';b=d/'later';a.write_bytes(b'one');b.write_bytes(b'two');r=m.Reader();r.read(a);r.read(b);r.finish();ck('two real intact body samples '+m.__name__,True)
ck('fixed caps unchanged',(new.FILE,new.TOTAL,new.SECONDS)==(old.FILE,old.TOTAL,old.SECONDS)==(4194304,8388608,120))
a=ast.parse((H/'ORIGINAL_preclaim01.py').read_bytes());b=ast.parse((H/'preclaim01.py').read_bytes())
def strip(t):
 for n in ast.walk(t):
  if isinstance(n,ast.ClassDef) and n.name=='Reader':n.body=[k for k in n.body if not isinstance(k,ast.FunctionDef) or k.name not in ('__init__','_physical','finish')]
 return ast.dump(t,include_attributes=False)
ck('all remaining original AST exactly unchanged',strip(a)==strip(b));ck('no numerical imports',not any(n in sys.modules for n in ('torch','numpy','pandas','scipy')))
put('CURRENTNESS_WITNESSES05.json',{'schema_version':1,'status':'PASS_ORIGINAL_REAL_CLEANUP_RED_TO_CORRECTED_REFUSAL_GREEN','rows':results,'original_PC1_sha256':sha((H/'ORIGINAL_PC1_WITNESS01.json').read_bytes()),'no_Admission_Run_Owner_or_recovery_created':True,'metadata_rejoins_are_sampled_not_atomic':True})
put('CHECKS05.json',{'status':'PASS_SOURCE_CURRENTNESS_ONLY','count':len(rows),'rows':rows});print(json.dumps({'checks':len(rows),'real_cleanup_pairs':6,'original_accepts_stale':5,'corrected_refusals':5,'both_deadline_refusals':2}))
