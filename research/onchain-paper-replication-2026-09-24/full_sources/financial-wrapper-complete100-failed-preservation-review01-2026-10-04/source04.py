from pathlib import Path
import ast,hashlib,json,stat,importlib.util,copy
from types import SimpleNamespace
D=Path(__file__).resolve().parent;F=D.parent;A=F/'financial-wrapper-complete100-failed-preservation-tooling01-2026-10-04';C=F/'financial-wrapper-complete100-failed-outcome-capture02-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ok(v,n):assert v,n;checks.append(n)
ok(sha((A/'MANIFEST01.json').read_bytes())=='4f161389773ecf6a99b191dd58f0198be560d1cefaf3021691d638f0b8fb5fff','author exactseal')
rows=json.loads((A/'MANIFEST01.json').read_bytes())['members'];names=set()
for r in rows:
 p=A/r['path'];s=p.lstat();names.add(r['path']);mode=int(r['mode'],8)if isinstance(r['mode'],str)else r['mode'];ok(stat.S_IMODE(s.st_mode)==mode,'author mode '+r['path'])
 if r['kind']=='file':ok(stat.S_ISREG(s.st_mode)and s.st_size==r['bytes']and sha(p.read_bytes())==r['sha256'],'author body '+r['path'])
 else:ok(stat.S_ISDIR(s.st_mode),'author directory '+r['path'])
ok({p.relative_to(A).as_posix()for p in A.rglob('*')}==names|{'MANIFEST01.json'},'full original author scope')
inv=json.loads((A/'SOURCE_INVERSE01.json').read_bytes())
for name in ('recover01.py','restore01.py'):
 item=inv[name];s=(A/('ORIGINAL_'+name)).read_text();ok(sha(s.encode())==item['original_sha256'],'exact original '+name)
 for edit in item['edits']:ok(edit['old']in s,'inverse literal present '+name);s=s.replace(edit['old'],edit['new'])
 ok(s==(A/name).read_text(),'whole literal inverse '+name);ok(ast.dump(ast.parse(s))==ast.dump(ast.parse((A/name).read_text())),'wholeAST inverse '+name)
spec=importlib.util.spec_from_file_location('candidate_flat',A/'restore01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);R=m.R;m.pins_ready();cap=json.loads((C/'CAPTURE01.json').read_bytes());scopes=m.load_scopes(C,cap);m.validate_union(C,cap,scopes);ok(len(scopes)==10 and len(m.REQUIRED)==35,'actual complete fixed10scope35body union')
t=D/'tiny04';t.mkdir(mode=0o700);bundle=t/'bundle';bundle.mkdir(mode=0o700);small={}
for label in m.LABELS:
 root=t/('source-'+label);root.mkdir(mode=0o700);(root/'opaque').write_bytes((label+'\0').encode()*3);(root/'empty').mkdir(mode=0o700);mf=R.scan(root);arc=R.pack(root,mf,bundle/('complete-'+label+'01.tar.gz'));small[label]={'manifest':mf,'archive':arc}
output=t/'good';output.mkdir(mode=0o700);calls=[];results=m.restore_scopes(bundle,small,output,lambda:calls.append(1));ok(len(calls)==40 and len(results)==10,'10scope40innerobservations fits64outer')
for label,receipt in results.items():
 meta=json.loads(R.read(output/('flat-'+label+'01'),receipt['metadata_file']));ok(meta['manifest']==small[label]['manifest'],'full tiny mode and directory metadata '+label)
 for name,leaf in meta['flat_members'].items():ok(R.read(output/('flat-'+label+'01'),leaf)==(t/('source-'+label)/name).read_bytes(),'fresh10scope body '+label)
try:m.restore_scopes(bundle,small,output,lambda:None)
except ValueError:checks.append('replay refused')
else:raise AssertionError('replay')
partial=t/'partial';partial.mkdir(mode=0o700);calls=[];fatal=MemoryError('tiny scope2fatal')
def stop():
 calls.append(1)
 if len(calls)==3:raise fatal
try:m.restore_scopes(bundle,small,partial,stop)
except BaseException as e:ok(e is fatal and (partial/'flat-capsule0101/body-metadata.json').exists()and not(partial/'flat-capsule0201').exists(),'real partialfirstfatal retained')
else:raise AssertionError('fatal lost')
entry=next(n for n in ast.parse((A/'restore01.py').read_bytes()).body if isinstance(n,ast.FunctionDef)and n.name=='entry')
for first in (ValueError('ordinary'),MemoryError('primary'),KeyboardInterrupt('primary')):
 for later in (OSError('later'),MemoryError('later'),SystemExit('later')):
  def main():raise first
  def put(*a):raise later
  ns={'main':main,'R':SimpleNamespace(put=put,_cleanup=R._cleanup),'HERE':D};exec(compile(ast.Module(body=[entry],type_ignores=[]),'actual_entry_extract','exec'),ns)
  try:ns['entry']()
  except BaseException as e:
   expected=first if isinstance(first,(MemoryError,KeyboardInterrupt))else later if isinstance(later,(MemoryError,SystemExit))else None
   ok(e is expected if expected is not None else type(e).__name__=='CleanupFailure','actual cleanup pair '+type(first).__name__+'/'+type(later).__name__)
  else:raise AssertionError('no failure')
remote=(A/'recover01.py').read_text();tree=ast.parse(remote);gitnode=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='git');calls_ast=sorted({ast.unparse(n.func)for n in ast.walk(gitnode)if isinstance(n,ast.Call)});ok(not any('census'in v or 'scan'in v or 'rlimit'in v for v in calls_ast),'FP-GIT-01 no writable-tree census or rlimit invoked in actual Git loop');ok('git_extent_readback'not in remote and 'st_blocks'not in remote,'posttransfer physical census not integrated')
(D/'FP_GIT_01.json').write_text(json.dumps({'finding':'WITHHELD_FP_GIT_01','source_sha256':sha((A/'recover01.py').read_bytes()),'actual_git_call_set':calls_ast,'source_lines':{'git_loop':'70-133','fetches':'173 and184','separate_census':'git_extent_readback01.py'},'facts':['Actual subprocess loop bounds streamed stdout/stderr, elapsed time, free disk floor only.','Neither current whole logical/allocated/member totals nor per-Git writable extent are checked during fetch or before success receipt.','Separate post-transfer census is never invoked by driver; it cannot retroactively enforce64MiB whole-store limit.'],'required_remedy':'Separate frozen successor with explicit bounded complete writable-tree accounting sampled during and after child work, clear overshoot/blocked-scan limits, firstfatal/processgroup kill and reap. Do not claim selected4MiB bound is universal Gitpack bound.','actual_remote_executed':False},indent=2,sort_keys=True)+'\n')
(D/'SOURCE_READBACK04.json').write_text(json.dumps({'checks':len(checks),'checks_detail':checks,'local_capture_accepted':True,'flat_source_byte_utility_checks_pass':True,'remote_execution_release':False,'blocking_finding':'FP-GIT-01'},indent=2,sort_keys=True)+'\n');print(json.dumps({'checks':len(checks)}))
