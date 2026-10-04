"""Owned opaque tail control only: no public run, release, actual remote or authority fixture."""
from pathlib import Path
import sys,ast,json,os,types,hashlib
BASE=Path(__file__).resolve().parent;D=BASE/(sys.argv[1]+'-'+sys.argv[2]+'-final');D.mkdir(mode=0o700);F=BASE.parent;P=(F/'financial-wrapper-compatibility-final-bundle-transport-correction03-2026-10-05' if sys.argv[2]=='old' else BASE)/'BASELINE';sys.path.insert(0,str(P));import restore_bundle01 as S
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
fn=next(n for n in ast.parse((P/'restore_bundle01.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='run');tail=fn.body[next(i for i,x in enumerate(fn.body) if 'original request/receipt unchanged' in ast.unparse(x)):];assert isinstance(tail[0],ast.Expr) and 'original request/receipt unchanged' in ast.unparse(tail[0]);assert any('cohort.check' in ast.unparse(x) for x in tail);tailmod=ast.fix_missing_locations(ast.Module(body=tail,type_ignores=[]));(D/'EXACT_TAIL_AST01.txt').write_text(ast.dump(tailmod,include_attributes=False)+'\n')
proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)});real=R.os;closed=[];changed=[]
def close(fd):
 target=os.readlink('/proc/self/fd/'+str(fd));os.close(fd)
 if target==str(root/'BUNDLE_FLAT_RECOVERY01.json'):
  closed.append(fd)
  if sys.argv[1] not in ('new-healthy','selected-late'):(root/request_name).write_bytes(b'changed request after final read');changed.append(True)
scan_fds=[];scan_mutated=[]
def scandir(fd):
 if isinstance(fd,int) and os.readlink('/proc/self/fd/'+str(fd))==str(selected):scan_fds.append(fd)
 return os.scandir(fd)
original_close=close
def close_with_selected(fd):
 original_close(fd)
 if sys.argv[1]=='selected-late' and fd in scan_fds:
  (selected/'first.tgz').write_bytes(b'changed selected archive after final scan');scan_mutated.append(True)
proxy.close=close_with_selected;proxy.scandir=scandir;env={'R':R,'B':S.B,'HERE':root,'q':q,'remote_raw':remote_raw,'request_name':request_name,'raw':raw,'request_sha':request_sha,'results':results,'samples':samples,'selected':selected,'profile':profile,'cohort':cohort,'boundary':boundary}
inputs=S.VerifiedCohort()
if hasattr(S,'input_read'):
 S.input_read(inputs,root,request_name)
 def actual_body(row):
  data=S.input_read(inputs,S.B.ROOT,row['path']);assert len(data)==row['bytes'] and R.digest(data)==row['sha256'];return data
 env.update(inputs=inputs,actual_body=actual_body)
if sys.argv[2]=='new':
 # Execute exact new sampled selected-population source block on opaque bodies only.
 begin=next(i for i,x in enumerate(fn.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='m' for t in x.targets))
 end=next(i for i,x in enumerate(fn.body) if isinstance(x,ast.Expr) and ast.unparse(x).startswith('inputs.tree('))
 records=[];required={}
 for name in sorted(p.name for p in selected.iterdir()):
  data=(selected/name).read_bytes();row={'path':name,'bytes':len(data),'sha256':R.digest(data),'git_object':hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()};records.append(row);required[name]={'bytes':len(data),'sha256':row['sha256']}
 env.update(records=records,required=required,os=os,hashlib=hashlib,input_read=S.input_read)
 exec(compile(ast.fix_missing_locations(ast.Module(body=fn.body[begin:end+1],type_ignores=[])),'exact-selected-cohort-source','exec'),env)
error=None
R.os=proxy
try:exec(compile(tailmod,'exact-source-run-tail','exec'),env)
except ValueError as caught:error=str(caught)
finally:R.os=real
assert (error is not None)==(sys.argv[1]=='new-green' or (sys.argv[1]=='selected-late' and sys.argv[2]=='new')),error
assert len(closed)==1;assert bool(changed)==(sys.argv[1] not in ('new-healthy','selected-late'));assert (R.scan(selected)==profile['full_manifest'])==(sys.argv[1]!='selected-late');cohort.check()
try:os.fstat(closed[0])
except OSError:pass
else:raise AssertionError('actual receipt fd not closed')
# One inherited fatal precedence check, not a matrix.
primary=KeyboardInterrupt('opaque earlier fatal')
try:
 try:raise primary
 finally:R._cleanup((lambda:(_ for _ in ()).throw(OSError('opaque cleanup failure')),),primary=primary)
except BaseException as actual:assert actual is primary
result={'finding':'FT02_INPUT_COHORT_AFTER_RECEIPT','source_sha256':hashlib.sha256((P/'restore_bundle01.py').read_bytes()).hexdigest(),'exact_tail_lines':[tail[0].lineno,tail[-1].end_lineno],'two_actual_opaque_scopes_restored':True,'actual_receipt_fd_closed_once':True,'actual_request_changed_after_last_read':bool(changed),'exact_tail_returned_success':error is None,'refusal':error,'final_output_cohort_passed':True,'selected_population_unchanged':sys.argv[1]!='selected-late','earlierfatal_preserved':True,'public_run_invoked':False,'actual_remote_or_release_fabricated':False,'Root_or_CAP_modified':False,'tail_only_engineering_evidence':True,'selected_final_scan_fd_closed_then_mutated':bool(scan_mutated)};(D/'WITNESS01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
