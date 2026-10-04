"""Finite stdlib opaque controls; never invokes helper main/entry."""
import ast,copy,hashlib,importlib.util,json,os,shutil,stat,sys,time
from pathlib import Path
from types import SimpleNamespace
H=Path(__file__).resolve().parent;sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,n):assert v,n;checks.append(n)
def load(name,file):
 sp=importlib.util.spec_from_file_location(name,H/file);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=load('flat_source','restore02.py');pending=load('pending_source','restore.template01.py');R=m.R
try:pending.pins_ready()
except ValueError:checks.append('unresolved actualcapture template refuses')
else:raise AssertionError('pending accepted')
m.pins_ready();ck(shutil.disk_usage(H).free>=R.FLOOR,'observed10GiBfloor');raw=(H/'recover01.py').read_text();tree=ast.parse(raw);ns={'Path':Path,'hashlib':hashlib,'json':json,'FILE':4194304,'REQUIRED':m.REQUIRED}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('require','digest','validate_fixed_selection','_raise_retained')],type_ignores=[]),'actual_remote_pure','exec'),ns)
s={'remote_commit':None,'rows':[dict(path=k,**v) for k,v in sorted(m.REQUIRED.items())]};ns['validate_fixed_selection'](s);ck(len(s['rows'])==7 and sum(r['bytes'] for r in s['rows'])==1063336 and 11+2*len(s['rows'])==25,'exact seven bodies25ops')
for name,mut in [('missing',lambda v:v['rows'].pop()),('duplicate',lambda v:v['rows'].append(v['rows'][0])),('hash',lambda v:v['rows'][0].update(sha256='0'*64)),('extent',lambda v:v['rows'][0].update(bytes=4194305)),('path',lambda v:v['rows'][0].update(path='research/../bad'))]:
 v=copy.deepcopy(s);mut(v)
 try:ns['validate_fixed_selection'](v)
 except ValueError:checks.append('fixed map mutation refused '+name)
 else:raise AssertionError(name)
# Genuine current capture only parsed/hash/framed, never restored.
C=H.parent/'financial-wrapper-complete100-final-supplement-capture01-2026-10-04';cap=json.loads((H/'ACTUAL_CAPTURE01.json').read_bytes());scopes=m.load_scopes(C,cap);framing=[]
for label,x in scopes.items():
 seen=[];expected={r['path']:r for r in x['manifest']['members']}
 for name,t,b in R.framed_members((C/('complete-'+label+'01.tar.gz')).read_bytes()):
  r=expected[name];ck(name not in seen and t.mode==r['mode'],'actual opaque frame '+label+'/'+name)
  if r['kind']=='file':ck(t.isfile() and len(b)==r['bytes'] and sha(b)==r['sha256'],'actual opaque bytes '+label+'/'+name)
  else:ck(t.isdir() and not b,'actual empty directory '+name)
  seen.append(name)
 ck(seen==list(expected),'actual complete ordered framing '+label);framing.append({'scope':label,'members':len(seen),'files':sum(r['kind']=='file' for r in expected.values()),'logical_bytes':sum(r.get('bytes',0) for r in expected.values())})
# Ordinary generated opaque two-scope utility fixtures, no fake remote receipt/context.
t=H/'tiny';t.mkdir(mode=0o700);bundle=t/'bundle';bundle.mkdir(mode=0o700);small={}
for label in m.LABELS:
 d=t/('original-'+label);d.mkdir(mode=0o700);(d/'opaque').write_bytes((label+'\x00opaque').encode()*11);(d/'empty').mkdir(mode=0o700);manifest=R.scan(d);info=R.pack(d,manifest,bundle/('complete-'+label+'01.tar.gz'));small[label]={'manifest':manifest,'archive':info}
out=t/'roundtrip';out.mkdir(mode=0o700);calls=[]
def boundary():
 ck(shutil.disk_usage(H).free>=R.FLOOR,'tiny actual floor');calls.append(len(calls))
result=m.restore_scopes(bundle,small,out,boundary);ck(len(calls)==8 and set(result)==set(m.LABELS),'all8 beforeafter and final rejoin boundaries')
for label in m.LABELS:
 meta=json.loads(R.read(out/('flat-'+label+'01'),result[label]['metadata_file']));ck(meta['manifest']==small[label]['manifest'],'exact tiny mode/emptydir metadata '+label)
 for name,leaf in meta['flat_members'].items():ck(R.read(out/('flat-'+label+'01'),leaf)==(t/('original-'+label)/name).read_bytes(),'tiny full opaque body '+label)
try:m.restore_scopes(bundle,small,out,boundary)
except ValueError:checks.append('complete namespace refuses replay')
else:raise AssertionError('replay')
partial=t/'partial';partial.mkdir(mode=0o700);fatal=KeyboardInterrupt('controlled second-scope boundary');counter=[]
def stop():
 counter.append(1)
 if len(counter)==3:raise fatal
try:m.restore_scopes(bundle,small,partial,stop)
except BaseException as e:ck(e is fatal and (partial/'flat-contract01/body-metadata.json').is_file() and not (partial/'flat-support01').exists(),'second-boundary fatal retains complete first scope')
else:raise AssertionError('fatal')
# Exact actual utility rejoin catches a changed already-restored first scope.
late=t/'late';late.mkdir(mode=0o700);events=[]
def alter():
 events.append(1)
 if len(events)==4:(late/'flat-contract01/body-00000.body').write_bytes(b'corrupted owned fixture')
try:m.restore_scopes(bundle,small,late,alter)
except ValueError:checks.append('late first-scope corruption refused')
else:raise AssertionError('late corruption')
missing=t/'extra-scope';missing.mkdir(mode=0o700)
try:m.restore_scopes(bundle,dict(small,foreign=small['contract']),missing,lambda:None)
except ValueError:checks.append('foreign scope refused before destination')
else:raise AssertionError('extra')
# Failure handler exact AST with genuine cleanup and controlled writer exceptions.
entry=next(n for n in ast.parse((H/'restore02.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='entry');pairs=[]
for first in (ValueError('ordinary'),KeyboardInterrupt('fatal'),MemoryError('memory')):
 for later in (OSError('writer'),SystemExit('fatalwriter'),MemoryError('memorywriter')):
  attempts=[]
  def main(first=first):raise first
  def writer(*args,later=later):attempts.append(True);raise later
  en={'main':main,'R':SimpleNamespace(put=writer,_cleanup=R._cleanup),'HERE':t};exec(compile(ast.Module(body=[entry],type_ignores=[]),'exact_failure_handler','exec'),en)
  try:en['entry']()
  except BaseException as e:
   if isinstance(first,MemoryError) or not isinstance(first,Exception):ck(e is first,'first actual fatal survives writer')
   elif isinstance(later,MemoryError) or not isinstance(later,Exception):ck(e is later,'later fatal outranks ordinary')
   else:ck(type(e).__name__=='CleanupFailure' and e.failures==(first,later),'ordinary pair retained in uncertainty')
   ck(attempts==[True],'failure journal attempted exactly once');pairs.append({'primary':type(first).__name__,'writer':type(later).__name__,'raised':type(e).__name__})
  else:raise AssertionError('lostfailure')
ck(not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')) and not any(n.startswith('tradingagents') for n in sys.modules),'only stdlib utility imports');(H/'CHECKS05.json').write_text(json.dumps({'checks':len(checks),'names':checks,'actual_fixed_capture_framing':framing,'fatal_pairs':pairs,'actual_remote_receipt':None,'actual_helper_main_or_entry_invoked':False,'actual_root_restore':False,'tiny_utility_restores_only':True},indent=2,sort_keys=True)+'\n');print(json.dumps({'checks':len(checks),'fixed_framed_members':sum(x['members'] for x in framing),'fatal_pairs':len(pairs)}))
