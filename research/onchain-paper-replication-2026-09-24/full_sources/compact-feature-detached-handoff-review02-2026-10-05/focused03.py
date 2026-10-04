"""Actual stdlib filesystem predicates only; no Run, Owner, Receipt or loader fixture."""
from pathlib import Path
import ast,hashlib,json,os,stat,sys,types
BASE=Path(__file__).resolve().parent;D=BASE/(sys.argv[1]+'-fixed');D.mkdir(mode=0o700);ROOT=BASE.parents[3];P=BASE.parent/('compact-feature-detached-handoff01-2026-10-05' if sys.argv[1]=='old-red' else 'compact-feature-detached-handoff02-2026-10-05');SRC=ROOT/'tradingagents/research/onchain_replication'
def extract(path,names,env):
 tree=ast.parse(path.read_bytes());nodes=[x for x in tree.body if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and x.name in names];assert len(nodes)==len(names);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),env);return env
base={'os':os,'sys':sys,'stat':stat,'Path':Path,'json':json};io=extract(SRC/'score_batches.py',{'CleanupFailure','_require','_cleanup','_close_after_failure','_release','_open','_root'},dict(base));io=types.SimpleNamespace(**io)
e=extract(SRC/'compact_owner.py',{'entries','present'},dict(base,io=io,require=io._require));compact=types.SimpleNamespace(**e)
mo=extract(SRC/'matching_owner.py',{'metadata','signature'},dict(base,require=io._require,LIMIT=65536,digest=lambda b:hashlib.sha256(b).hexdigest()));matching=types.SimpleNamespace(**mo)
root=D/'opaque';root.mkdir(mode=0o700);graphroot=root/'research_artifacts/onchain_compact_graphs/workflow/experiment';graphroot.mkdir(parents=True);g=graphroot/('a'*64);g.mkdir();(g/'artifact').mkdir()
journal=root/'research_artifacts/onchain_pair_workflows/workflow/experiment';owner=journal/'compact';stage=owner/'dictionary';stage.mkdir(parents=True)
terminal=root/'research_artifacts/onchain_compact_terminals/workflow/experiment';terminal.mkdir(parents=True)
paths=[g/'start.json',g/'complete.json',g/'artifact/manifest.json',journal/'owner.json',journal/'complete.json',owner/'complete.json',stage/'intent.json',stage/'stage-complete.json',owner/'owner.json',journal/'start.json',journal/'claim.json']
for p in paths+[terminal/'start.json',terminal/'complete.json']:p.write_bytes(b'{"opaque":1}\n')
snapshots={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths};v={'graph_root':str(graphroot),'components':{'a'*64:{}},'metadata_pins':snapshots,'failure_roots':sorted({str(owner),str(owner.parent),*[str(Path(n).parent) for n in snapshots]})}
# Exact filesystem statements copied from candidate check_metadata. No active-run
# or authority checks are bypassed to execute a loader: that function is not called.
fn=next(n for n in ast.parse((P/'overlay/compact_detached_handoff.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='check_metadata')
nodes=[n for n in fn.body if ('compact_owner.entries(' in ast.unparse(n) or isinstance(n,ast.For) and any(k in ast.unparse(n.iter) for k in ("v['components']","v['failure_roots']","v['metadata_pins']")))]
if sys.argv[1]!='old-red':
 nodes.extend(n for n in fn.body if isinstance(n,ast.For) and "('start.json', 'complete.json')"==ast.unparse(n.iter))
assert len(nodes)==(4 if sys.argv[1]=='old-red' else 6)
code=compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'exact-detached-filesystem-predicates','exec')
env={'compact_owner':compact,'matching_owner':matching,'Path':Path,'require':io._require,'v':v,'ad':types.SimpleNamespace(root=root)}
if sys.argv[1]!='old-red':
 for p in (terminal/'start.json',terminal/'complete.json'):snapshots[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 v['failure_roots'].append(str(terminal));v['terminal_attempt']=str(terminal);v['saved_namespaces']=[]
 for path,names in ((terminal,{'start.json','complete.json'}),(journal.parent,{journal.name}),(journal,{'owner.json','start.json','claim.json','compact','complete.json'}),(owner,{'owner.json','complete.json','dictionary'})):
  st=path.lstat();v['saved_namespaces'].append({'path':str(path),'members':sorted(names),'device':st.st_dev,'inode':st.st_ino})
exec(code,env);compact.entries(journal.parent,{journal.name},required={journal.name})
mode=sys.argv[1];refusal=None
if mode in ('old-red','new-missing'):
 (terminal/'complete.json').rename(terminal/'saved_original_complete.json');(terminal/'failed.json').write_bytes(b'{"opaque_failure":1}\n')
elif mode=='new-foreign':(journal.parent/'foreign-experiment').mkdir()
elif mode=='new-owner-body':(owner/'owner.json').write_bytes(b'{"changed":1}\n')
try:exec(code,env)
except (ValueError,FileNotFoundError) as e:refusal=type(e).__name__+': '+str(e)
assert (refusal is not None)==(mode not in ('old-red','new-healthy')),refusal
assert not any(x in sys.modules for x in ('numpy','torch','pandas'))
result={'mode':mode,'source_sha256':hashlib.sha256((P/'overlay/compact_detached_handoff.py').read_bytes()).hexdigest(),'exact_filesystem_predicates':True,'refusal':refusal,'actual_factory_lease_loader_or_arrays':False,'actual_run_owner_receipt_or_authority_constructed':False,'numerical_imports':False};(D/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
