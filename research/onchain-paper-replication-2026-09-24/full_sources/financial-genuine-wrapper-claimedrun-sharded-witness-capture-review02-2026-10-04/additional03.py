import ast,hashlib,importlib.util,json,os,sys
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;A=B/'financial-genuine-wrapper-claimedrun-sharded-witness-capture-preparation02-2026-10-04'
sys.path.insert(0,str(B/'held-consumer-final-recovery-preparation04-2026-10-03'));import recovery04 as R
ns={'__name__':'source_only','__file__':str(A/'capture_witness02.py')};exec(compile((A/'capture_witness02.py').read_bytes(),'source','exec'),ns);checks=[]
def ck(v,n):assert v,n;checks.append(n)
# Exercise actual put -> original new_file: real body and held parent descriptors.
for i,typ in enumerate((MemoryError,SystemExit,KeyboardInterrupt)):
 for j,ct in enumerate((OSError,MemoryError,SystemExit)):
  first=typ('body first fatal');secondary=ct('real close diagnostic');closed=[];write=os.write;close=os.close
  def badwrite(fd,data):raise first
  def badclose(fd):close(fd);closed.append(fd);raise secondary
  os.write=badwrite;os.close=badclose
  try:
   try:ns['put'](R,H/('put-%d-%d'%(i,j)),b'opaque')
   except BaseException as e:ck(e is first,'actual put first fatal identity')
   else:raise AssertionError('missing fatal')
  finally:os.write=write;os.close=close
  ck(len(closed)==2 and len(set(closed))==2,'both owned parent and body FDs closed')
  for fd in closed:
   try:os.fstat(fd)
   except OSError:checks.append('FD actually absent')
   else:raise AssertionError('leaked FD')
# Source caps and planner refuse an unexcepted body >2MiB; direct exception is not generic.
spec=importlib.util.spec_from_file_location('planner03',A/'shards01.py');P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
bad={'schema_version':1,'root_mode':448,'members':[{'path':'other-large','kind':'file','mode':384,'bytes':2097153,'sha256':'0'*64}]}
try:P.partition(bad)
except ValueError:checks.append('generic oversized body refused')
else:raise AssertionError('unexpected generic fallback')
# Authenticate original-source chain instead of trusting an inverse witness alone.
original=(A/'original-capture_witness01.py').read_bytes();prior=B/'financial-genuine-wrapper-claimedrun-sharded-witness-capture-preparation01-2026-10-04'
ck(original==(prior/'capture_witness01.py').read_bytes(),'exact previous withheld exporter source')
ck((A/'shards01.py').read_bytes()==(B/'financial-genuine-wrapper-claimedrun-final-capture-preparation02-2026-10-04/shards01.py').read_bytes(),'exact prior reviewed planner')
ck(ns['FILE']==4194304 and ns['LIMIT']==67108864 and ns['FLOOR']==10737418240,'unchanged caps')
# Current no-attempt namespaces and actual binding proof, read-only.
ck(not os.path.lexists(ns['HERE']/'union-bytes01'),'actual Root union absent')
ck(hashlib.sha256(R.read(B/'financial-genuine-wrapper-claimedrun-actual-outcome-binding-review01-2026-10-04','MANIFEST01.json')).hexdigest()=='0c39988229162fd10b0d0df77f71163a4675a778251a8d75634283e40482bea2','actual binding seal')
ck(not any(n in sys.modules for n in ('torch','numpy','scipy','pandas')),'stdlib-only')
(H/'ADDITIONAL03.json').write_text(json.dumps({'checks':checks,'count':len(checks),'actual_capture':False},sort_keys=True,indent=2)+'\n');print('PASS',len(checks))
