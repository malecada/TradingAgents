from pathlib import Path
import ast,hashlib,importlib.util,json,sys,stat,io,copy,os
D=Path(__file__).resolve().parent;F=D.parent;A=F/'financial-wrapper-complete100-final-supplement-tooling01-2026-10-04';C=F/'financial-wrapper-complete100-final-supplement-capture01-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ok(v,n):assert v,n;checks.append(n)
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
ok(sha((A/'MANIFEST01.json').read_bytes())=='601581af0d2377175125c02ed6633c766dda7988353d2ccf5c53bd531a171bd7','author seal')
manifest=json.loads((A/'MANIFEST01.json').read_bytes());names=set()
for r in manifest['members']:
 p=A/r['path'];s=p.lstat();names.add(r['path']);mode=r['mode'];mode=int(mode,8)if isinstance(mode,str)else mode;ok(stat.S_IMODE(s.st_mode)==mode,'author mode '+r['path'])
 if r['kind']=='file':ok(stat.S_ISREG(s.st_mode)and s.st_size==r['bytes']and sha(p.read_bytes())==r['sha256'],'author body '+r['path'])
 elif r['kind']=='directory':ok(stat.S_ISDIR(s.st_mode),'author directory '+r['path'])
 else:ok(stat.S_ISLNK(s.st_mode),'author link '+r['path'])
ok({str(p.relative_to(A))for p in A.rglob('*')}==names|{'MANIFEST01.json'},'whole author scope')
ok(sha((A/'restore02.py').read_bytes())=='dcbf5ec290b1f34cb3a238be76976a0ad8ebf07003e8d5f43cfcbaacc1d8d5a0','flat exact')
ok(sha((A/'recover01.py').read_bytes())=='25080e2eeceb234fe63e69ab093c3d1c6af84d6584f476cc872ed43666056c1b','remote exact')
old=(A/'restore01.py').read_text();new=(A/'restore02.py').read_text();expected=old.replace("'recovery04.py': 'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a'","'recovery_pax01.py': 'a054d5922899b53579f4220ff3b427dc050dff075cb5470b43ff55e621b97eb2'").replace('import recovery04 as R','import recovery_pax01 as R');ok(new==expected,'whole two literal PAX binding inverse');ok(ast.dump(ast.parse(new))==ast.dump(ast.parse(expected)),'whole AST inverse')
m=load('review_flat',A/'restore02.py');R=m.R;oldR=load('review_oldR',A/'utilities/recovery04.py');m.pins_ready();cap=json.loads((C/'CAPTURE01.json').read_bytes());scopes=m.load_scopes(C,cap)
for name,row in m.REQUIRED.items():
 p=F.parents[2]/name;b=p.read_bytes();ok(len(b)==row['bytes']and sha(b)==row['sha256'],'actual7 pin '+name)
ok(len(m.REQUIRED)==7 and sum(r['bytes']for r in m.REQUIRED.values())==1063336,'sevenbody finite25ops context')
reds=[]
for label,x in scopes.items():
 raw=(C/('complete-'+label+'01.tar.gz')).read_bytes();frames=list(R.framed_members(raw));ok(len(frames)==len(x['manifest']['members']),'whole actual frame denominator '+label)
 for (name,t,b),row in zip(frames,x['manifest']['members']):
  ok(name==row['path']and t.mode==row['mode'],'actual path mode '+name);ok((row['kind']=='directory'and t.isdir()and not b)or(row['kind']=='file'and t.isfile()and len(b)==row['bytes']and sha(b)==row['sha256']),'actual opaque typed body '+name)
 sink=io.BytesIO();R.tar_stream(Path(cap['scopes'][label]['snapshot']),x['manifest'],sink);ok(sink.getvalue()==raw,'actual whole canonical compressed bytes '+label)
 try:list(oldR.framed_members(raw))
 except ValueError as e:reds.append({'scope':label,'error':str(e)})
ok(len(reds)==1 and reds[0]['scope']=='support'and reds[0]['error']=='noncanonical raw member slash/type','exact original b40 actual failure retained');(D/'ACTUAL_RED01.json').write_text(json.dumps(reds,indent=2)+'\n')
# Fresh actual opaque long-path2scope fixtures, no remote/Owner substitutes.
t=D/'tiny';t.mkdir(mode=0o700);bundle=t/'bundle';bundle.mkdir(mode=0o700);small={}
for label in m.LABELS:
 root=t/('original-'+label);root.mkdir(mode=0o700);long=root/('z'*99);long.mkdir(mode=0o700);(long/'payload').write_bytes((label+' opaque\0').encode()*13);(root/'empty').mkdir(mode=0o700);mfest=R.scan(root);info=R.pack(root,mfest,bundle/('complete-'+label+'01.tar.gz'));small[label]={'manifest':mfest,'archive':info}
out=t/'good';out.mkdir(mode=0o700);res=m.restore_scopes(bundle,small,out,lambda:None)
for label,receipt in res.items():
 target=out/('flat-'+label+'01');meta=json.loads(R.read(target,receipt['metadata_file']));ok(meta['manifest']==small[label]['manifest'],'fresh full original mode metadata')
 for name,leaf in meta['flat_members'].items():ok(R.read(target,leaf)==(t/('original-'+label)/name).read_bytes(),'fresh exact PAX payload')
def refuse(fn,label):
 try:fn()
 except (ValueError,OSError,EOFError):checks.append(label)
 else:raise AssertionError(label)
refuse(lambda:m.restore_scopes(bundle,small,out,lambda:None),'replay refused')
for label in m.LABELS:refuse(lambda label=label:list(oldR.framed_members((bundle/('complete-'+label+'01.tar.gz')).read_bytes())),'tiny old PAX RED')
partial=t/'partial';partial.mkdir(mode=0o700);counter=[];fatal=MemoryError('independent second boundary')
def boundary():
 counter.append(1)
 if len(counter)==3:raise fatal
try:m.restore_scopes(bundle,small,partial,boundary)
except BaseException as e:ok(e is fatal and (partial/'flat-contract01/body-metadata.json').exists()and not(partial/'flat-support01').exists(),'firstfatal retains first scope/no second')
else:raise AssertionError('fatal lost')
for suffix,mut in [('extra',lambda b:b+b'extra'),('truncated',lambda b:b[:-8])]:
 raw=(bundle/'complete-contract01.tar.gz').read_bytes();refuse(lambda raw=mut(raw):list(R.framed_members(raw)),'compressed '+suffix+' refused')
late=t/'late';late.mkdir(mode=0o700);counter=[]
def corrupt():
 counter.append(1)
 if len(counter)==4:(late/'flat-contract01/body-00000.body').write_bytes(b'changed')
refuse(lambda:m.restore_scopes(bundle,small,late,corrupt),'late retained first scope corruption refused')
# Genuine cleanup reducer used with extracted exact failure handler; no actual entry/main.
from types import SimpleNamespace
entry=next(n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef)and n.name=='entry')
for first in (ValueError('first'),MemoryError('first'),KeyboardInterrupt('first')):
 for second in (OSError('later'),MemoryError('later'),SystemExit('later')):
  def main():raise first
  def put(*args):raise second
  ns={'main':main,'HERE':D,'R':SimpleNamespace(put=put,_cleanup=R._cleanup)};exec(compile(ast.Module(body=[entry],type_ignores=[]),'exact_entry_tail','exec'),ns)
  try:ns['entry']()
  except BaseException as e:
   expected=first if isinstance(first,(MemoryError,KeyboardInterrupt))else second if isinstance(second,(MemoryError,SystemExit))else None
   ok(e is expected if expected is not None else type(e).__name__=='CleanupFailure','genuine firstfatal pair '+type(first).__name__+'/'+type(second).__name__)
  else:raise AssertionError('missing failure')
ok(not any(x in sys.modules for x in ('numpy','torch','scipy','pandas')),'no numerical imports')
(D/'READBACK01.json').write_text(json.dumps({'checks':len(checks),'checks_detail':checks,'actual_frames':sum(len(x['manifest']['members'])for x in scopes.values()),'actual_regular_bodies':sum(r['kind']=='file'for x in scopes.values()for r in x['manifest']['members']),'actual_Root_restore_or_entry':False},indent=2,sort_keys=True)+'\n');print(json.dumps({'checks':len(checks)}))
