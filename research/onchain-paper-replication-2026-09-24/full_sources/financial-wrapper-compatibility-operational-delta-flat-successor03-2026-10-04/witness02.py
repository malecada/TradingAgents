from pathlib import Path
import importlib.util,json,os,types,stat,hashlib
O=Path(__file__).resolve().parent;F=O.parent

def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
old=load('oldcohort',O/'ORIGINAL_restore01.py');new=load('newcohort',O/'restore01.py');B=F/'financial-wrapper-compatibility-operational-delta-capture02-2026-10-04';FB=F/'financial-wrapper-compatibility-operational-delta-failed-remote-capture02-2026-10-04';results=[]
for kind in ['bytes','mode','foreign','metadata','cross-scope']:
 for label,M in [('old',old),('new',new)]:
  root=O/('w02-'+kind+'-'+label);root.mkdir(mode=0o700);c,m=M.load_capture(B);fc,fm=M.load_failed_capture(FB);r=M.restore_delta(B,c,m,root,lambda:None);fr=M.restore_failed_delta(FB,fc,fm,root,lambda:None);dest=root/M.FAILED_OUTPUT;meta=json.loads((dest/fr['metadata_file']).read_bytes());files=list(meta['flat_members'].values());trigger=dest/files[-1];target=dest/files[0]
  if kind=='metadata':target=dest/fr['metadata_file']
  if kind=='cross-scope':target=root/M.OUTPUT/json.loads((root/M.OUTPUT/r['metadata_file']).read_bytes())['flat_members']['COMPOSITION_BASIS01.json']
  pin=(trigger.stat().st_dev,trigger.stat().st_ino);real=M.R.os;proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)});changed=[False];before=hashlib.sha256(target.read_bytes()).hexdigest();oldmode=stat.S_IMODE(target.stat().st_mode)
  def close(fd):
   s=os.fstat(fd);os.close(fd)
   if not changed[0] and (s.st_dev,s.st_ino)==pin:
    changed[0]=True
    if kind=='mode':target.chmod(0o644)
    elif kind=='foreign':(dest/'foreign.body').write_bytes(b'opaque')
    else:target.write_bytes(target.read_bytes()+b'changed')
  cohort=None
  if label=='new':
   cohort=M.VerifiedCohort();M.verify_flat(root/M.OUTPUT,r,c,m,lambda:None,cohort)
  else:M.verify_flat(root/M.OUTPUT,r,c,m,lambda:None)
  M.R.os=proxy;error=None
  try:
   if label=='new':M.verify_flat(dest,fr,fc,fm,lambda:None,cohort);cohort.check()
   else:M.verify_flat(dest,fr,fc,fm,lambda:None)
  except BaseException as e:error=e
  finally:M.R.os=real
  (O/'WITNESS_PROGRESS02.json').write_text(json.dumps({'kind':kind,'label':label,'changed':changed[0],'error_type':None if error is None else type(error).__name__,'error_text':None if error is None else str(error)},indent=2)+'\n')
  assert changed[0];assert (error is None) if label=='old' else isinstance(error,(ValueError,OSError))
  results.append({'kind':kind,'version':label,'actual_late_close_mutation':True,'accepted':error is None,'error_type':None if error is None else type(error).__name__,'target':str(target.relative_to(O)),'before_sha256':before,'after_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'before_mode':oldmode,'after_mode':stat.S_IMODE(target.stat().st_mode),'timestamp_reset':False})
(O/'WITNESSES01.json').write_text(json.dumps(results,indent=2)+'\n');print('PASS five real local oldRED/newREFUSAL pairs including cross-scope and metadata')
