"""Owned opaque tail control only: no public run, release, actual remote or authority fixture."""
from pathlib import Path
import sys,ast,json,os,types,hashlib
D=Path(__file__).resolve().parent;F=D.parent;P=F/'financial-wrapper-compatibility-final-bundle-transport-preparation02-2026-10-05'/'BASELINE';sys.path.insert(0,str(P));import restore_bundle01 as S
R=S.R;root=D/'owned-tail';root.mkdir(mode=0o700);selected=root/'selected';selected.mkdir(mode=0o700);bundles=[]
for name in ('first','second'):
 src=D/('opaque-'+name);src.mkdir(mode=0o700);(src/'opaque').write_bytes(name.encode());(src/'empty').mkdir(mode=0o700);m=R.scan(src);R.put(selected/(name+'.json'),m);arc=R.pack(src,m,selected/(name+'.tgz'));bundles.append({'name':name,'manifest':{'path':name+'.json','bytes':len(R.encode(m)),'sha256':R.digest(R.encode(m))},'archive':{'path':name+'.tgz','bytes':arc['bytes'],'sha256':arc['sha256']}})
results,cohort=S.restore_archives({'bundles':bundles},selected,root,lambda:None,True)
for name,result in results.items():
 metadata=json.loads((root/('flat-'+name)/result['metadata_file']).read_bytes());assert (root/('flat-'+name)/metadata['flat_members']['opaque']).read_bytes()==name.encode()
# This is ordinary opaque metadata supplied only to the exact last five statements;
# no accepted release/remote object is built, and public run() is never called.
remote=D/'opaque-remote-bytes';remote.write_bytes(b'opaque comparison input');remote_raw=remote.read_bytes();ref={'path':remote.relative_to(S.B.ROOT).as_posix(),'bytes':len(remote_raw),'sha256':R.digest(remote_raw)};q={'actual_remote_receipt':ref};request_name='opaque-request.json';raw=R.encode(q);(root/request_name).write_bytes(raw);request_sha=R.digest(raw);profile={'full_manifest':R.scan(selected)};samples=[]
def boundary():samples.append(S.W.census(root))
fn=next(n for n in ast.parse((P/'restore_bundle01.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='run');tail=fn.body[-5:];assert isinstance(tail[0],ast.Expr) and 'original request/receipt unchanged' in ast.unparse(tail[0]);assert 'cohort.check' in ast.unparse(tail[-1]);tailmod=ast.fix_missing_locations(ast.Module(body=tail,type_ignores=[]));(D/'EXACT_TAIL_AST01.txt').write_text(ast.dump(tailmod,include_attributes=False)+'\n')
proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)});real=R.os;closed=[];changed=[]
def close(fd):
 target=os.readlink('/proc/self/fd/'+str(fd));os.close(fd)
 if target==str(root/'BUNDLE_FLAT_RECOVERY01.json'):
  closed.append(fd);(root/request_name).write_bytes(b'changed request after final read');changed.append(True)
proxy.close=close;R.os=proxy;env={'R':R,'B':S.B,'HERE':root,'q':q,'remote_raw':remote_raw,'request_name':request_name,'raw':raw,'request_sha':request_sha,'results':results,'samples':samples,'selected':selected,'profile':profile,'cohort':cohort,'boundary':boundary}
try:exec(compile(tailmod,'exact-source-run-tail','exec'),env)
finally:R.os=real
assert len(closed)==1 and changed==[True] and (root/request_name).read_bytes()!=raw;assert R.scan(selected)==profile['full_manifest'];cohort.check()
try:os.fstat(closed[0])
except OSError:pass
else:raise AssertionError('actual receipt fd not closed')
# One inherited fatal precedence check, not a matrix.
primary=KeyboardInterrupt('opaque earlier fatal')
try:
 try:raise primary
 finally:R._cleanup((lambda:(_ for _ in ()).throw(OSError('opaque cleanup failure')),),primary=primary)
except BaseException as actual:assert actual is primary
result={'finding':'FT02_INPUT_COHORT_AFTER_RECEIPT','source_sha256':hashlib.sha256((P/'restore_bundle01.py').read_bytes()).hexdigest(),'exact_tail_lines':[tail[0].lineno,tail[-1].end_lineno],'two_actual_opaque_scopes_restored':True,'actual_receipt_fd_closed_once':True,'actual_request_changed_after_last_read':True,'exact_tail_returned_success':True,'final_output_cohort_passed':True,'selected_population_unchanged':True,'earlierfatal_preserved':True,'public_run_invoked':False,'actual_remote_or_release_fabricated':False,'Root_or_CAP_modified':False,'tail_only_engineering_evidence':True};(D/'WITNESS01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
