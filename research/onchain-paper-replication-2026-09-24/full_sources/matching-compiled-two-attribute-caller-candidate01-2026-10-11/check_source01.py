"""Finite parser and literal seam checks; never imports scientific/owner code."""
import ast,difflib,hashlib,json,os,resource,signal,types
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10);resource.setrlimit(resource.RLIMIT_CPU,(9,9));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(10)
P=Path(__file__).resolve().parent;F=P.parent;O=F/'matching-compiled-uncached-edge-caller-candidate03-2026-10-11';A=F/'matching-compiled-two-attribute-agreement01-2026-10-11';checks=[]
def ck(v,name):assert v,name;checks.append(name)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
policy=json.loads((P/'POLICY_TEMPLATE01.json').read_text());oldpolicy=json.loads((F/'pilot34-native-owner-qualification01-2026-10-11/POLICY_ROLE01.json').read_text())
source=(P/'compiled_edge_owner.py').read_text();tree=ast.parse(source)
nodes=[n for n in tree.body if isinstance(n,ast.Assign) or isinstance(n,ast.FunctionDef) and n.name in ('require','freeze','attach','current_policy','options','join')]
ns={'Path':Path};exec(compile(ast.Module(body=nodes,type_ignores=[]),'policy-parser-only','exec'),ns)
ck(dict(ns['freeze'](policy))==policy,'new exact typed policy accepted')
ck(ns['freeze'](None) is None,'unselected policy preserved')
for value,label in [(oldpolicy,'legacy format and bodies'),(dict(policy,format=oldpolicy['format']),'legacy format with new bodies'),(dict(policy,library_sha256=oldpolicy['library_sha256']),'old library'),(dict(policy,runtime_bytes=True),'boolean extent'),(dict(policy,abi_path='../abi'),'relative role')]:
 try:ns['freeze'](value)
 except ValueError:ck(True,'refuse '+label)
 else:ck(False,'accepted unsupported '+label)
a=types.SimpleNamespace();b=types.SimpleNamespace();ns['attach'](a,policy);ns['attach'](b,policy);ns['join'](a,b);ck(ns['options'](a)=={'compiled_edge_policy_value':policy},'actual forwarding keyword unchanged');ns['attach'](a,None);ck(ns['options'](a)=={},'default no keyword')
for key in ('source','library','runtime','abi'):
 q=Path(policy[key+'_path']);ck(q.is_file() and digest(q)==policy[key+'_sha256'],'actual immutable '+key+' reference')
 if key in ('runtime','abi'):ck(q.stat().st_size==policy[key+'_bytes'],'exact '+key+' extent')
ck(Path(policy['library_path']).stat().st_size==21920,'new exact library extent21920')
ck((P/'edge_chunk_adapter.py').read_bytes()==(A/'edge_chunk_adapter.py').read_bytes() and digest(P/'edge_chunk_adapter.py')==policy['adapter_sha256'],'adapter exact accepted body')
ck(policy['adapter_path']==str(P.parents[3]/'tradingagents/research/onchain_replication/edge_chunk_adapter.py'),'template targets genuine installed adapter seam, not a fake source roster')
reverse=source
for old,new in reversed(json.loads((P/'OWNER_LITERAL_CHANGES01.json').read_text())):reverse=reverse.replace(new,old)
ck(reverse==(O/'compiled_edge_owner.py').read_text(),'owner full inverse only5 literals')
memo=(P/'batched_numeric_reuse.py').read_text();ck(memo.replace(digest(P/'compiled_edge_owner.py'),digest(O/'compiled_edge_owner.py'))==(O/'batched_numeric_reuse.py').read_text(),'memo inverse only owner source pin')
req=json.loads((P/'SOURCE_REQUIREMENTS01.json').read_text());patch=[];inverse=[];changed=[]
for rel,row in req.items():
 n=Path(rel).name;s=(P/n).read_text();ast.parse(s);ck(digest(P/n)==row['sha256'] and len(s.encode())==row['bytes'],'source requirement '+n)
 before=(O/n).read_text()
 if before!=s:
  changed.append(n);patch.extend(difflib.unified_diff(before.splitlines(True),s.splitlines(True),fromfile=n,tofile=n));inverse.extend(difflib.unified_diff(s.splitlines(True),before.splitlines(True),fromfile=n,tofile=n))
ck(set(changed)=={'compiled_edge_owner.py','edge_chunk_adapter.py','batched_numeric_reuse.py'},'seven full route modules unchanged including PairExecutor')
ck(''.join(patch)==(P/'FORWARD.patch').read_text() and ''.join(inverse)==(P/'INVERSE.patch').read_text(),'complete literal inverse')
for n in ('batched_pair_executor.py','matching_immutable_session.py','matching_checkpoint.py','matching_annealing.py'):ck(digest(P/n) in memo,'actual retained lower dependency pin '+n)
ck(digest(P/'matching_annealing.py')=='86ccc3a471827bdce7784145914240d04416d2cc0023e8acb77fb26ae473df57','unchanged corrected kernel')
(P/'SOURCE_RESULT01.json').write_text(json.dumps({'status':'PASS_FINITE_SOURCE_ONLY','checks':checks,'scientific_imports':False,'native_loaded':False,'actual_authority':False,'installed':False,'template_adapter_requires_future_exact_install':True},indent=2)+'\n');print(len(checks),'checks')
