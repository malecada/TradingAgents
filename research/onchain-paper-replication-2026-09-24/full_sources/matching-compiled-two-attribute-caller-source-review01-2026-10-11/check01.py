from pathlib import Path
import ast,json,hashlib,difflib
H=Path('research/onchain-paper-replication-2026-09-24/full_sources');N=H/'matching-compiled-two-attribute-caller-candidate01-2026-10-11';B=H/'matching-compiled-uncached-edge-caller-candidate03-2026-10-11';O=H/'matching-compiled-two-attribute-caller-source-review01-2026-10-11';refs={};checks=[]
def ref(p):
 b=p.read_bytes();r={'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};refs[str(p)]=r;return r
def read(p):ref(p);return json.loads(p.read_text())
def ck(v,n):assert v,n;checks.append(n)
def dump(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
m=read(N/'MANIFEST01.json');ck(refs[str(N/'MANIFEST01.json')]['sha256'].startswith('3d7f1fdf'),'frozen candidate manifest')
for n,r in m['files'].items():a=ref(N/n);ck(all(a[k]==r[k] for k in ('sha256','bytes')),'exact member '+n)
for n,r in m['immutable_evidence_reused'].items():a=ref(H/n);ck(all(a[k]==r[k] for k in ('sha256','bytes')),'immutable evidence '+n)
prior=read(B/'MANIFEST03.json');requirements=read(N/'SOURCE_REQUIREMENTS01.json');ck(len(requirements)==10,'complete ten-source roster')
for path,r in requirements.items():a=ref(N/Path(path).name);ck(all(a[k]==r[k] for k in ('sha256','bytes')),'requirement '+Path(path).name)
changes=read(N/'OWNER_LITERAL_CHANGES01.json');owner=(N/'compiled_edge_owner.py').read_text();inverse=owner
ck(len(changes)==5,'five owner literal substitutions')
for old,new in changes:ck(inverse.count(new)==1,'unique owner new literal '+new);inverse=inverse.replace(new,old)
ck(inverse==(B/'compiled_edge_owner.py').read_text(),'owner complete literal inverse');ck(ast.dump(ast.parse(inverse))==ast.dump(ast.parse((B/'compiled_edge_owner.py').read_text())),'owner complete AST inverse')
oldhash=ref(B/'compiled_edge_owner.py')['sha256'];newhash=ref(N/'compiled_edge_owner.py')['sha256'];memo=(N/'batched_numeric_reuse.py').read_text();ck(memo.count(newhash)==1 and memo.replace(newhash,oldhash)==(B/'batched_numeric_reuse.py').read_text(),'memo sole owner pin inverse')
unchanged=['batched_numeric_execution.py','batched_pair_executor.py','compact_mcm_batched.py','matching_annealing.py','matching_checkpoint.py','matching_immutable_session.py','real_pilot_import_caller.py']
for n in unchanged:
 a=ref(B/n);ck(a['sha256']==prior['files'][n]['sha256'] and a['sha256']==ref(N/n)['sha256'],'exact accepted route '+n)
ck(ref(N/'edge_chunk_adapter.py')['sha256']==ref(H/'matching-compiled-two-attribute-agreement01-2026-10-11/edge_chunk_adapter.py')['sha256'],'accepted two-attribute adapter exact')
policy=read(N/'POLICY_TEMPLATE01.json')
for kind in ('source','library','runtime','abi'):
 a=ref(Path(policy[kind+'_path']));ck(a['sha256']==policy[kind+'_sha256'],'policy body '+kind)
 if kind+'_bytes' in policy:ck(a['bytes']==policy[kind+'_bytes'],'policy extent '+kind)
ck(policy['adapter_path']==str(Path.cwd()/'tradingagents/research/onchain_replication/edge_chunk_adapter.py') and policy['adapter_sha256']==ref(N/'edge_chunk_adapter.py')['sha256'],'prospective adapter installed destination only')
# Execute only exact extracted pure freeze parser; no module import/owner or file read via source.
tree=ast.parse(owner);keep=[n for n in tree.body if isinstance(n,ast.Assign) and all(isinstance(t,ast.Name) and t.id in ('SOURCE','LIBRARY','ADAPTER','FORMAT','FIELDS') for t in n.targets) or isinstance(n,ast.FunctionDef) and n.name in ('require','freeze')]
ns={'Path':Path};exec(compile(ast.Module(body=keep,type_ignores=[]),'<pure-policy-parser>','exec'),ns)
ck(dict(ns['freeze'](policy))==policy,'new frozen plain policy parses');ck(ns['freeze'](None) is None,'legacy absent None retained')
legacy=dict(policy);legacy['format']=changes[3][0]
try:ns['freeze'](legacy)
except ValueError as e:ck(str(e)=='unsupported edge bodies','old format refuses')
else:raise AssertionError('old format accepted')
compact=ast.parse((N/'compact_mcm_batched.py').read_text());fn=next(n for n in compact.body if isinstance(n,ast.FunctionDef) and n.name=='_edge_inputs');size=next(n for n in ast.walk(fn) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='size' for t in n.targets));actual_size=eval(compile(ast.Expression(size.value),'<exact-size-expression>','eval'),{'policy':policy,'kind':'library'})
ck(actual_size==17072,'actual genuine caller requires old extent');lib=ref(Path(policy['library_path']));ck(lib['bytes']==21920 and actual_size!=lib['bytes'],'authenticated real library mismatches caller extent')
# Owner read_reference's exact_size predicate directly proves refusal without opening/loading library through engine.
predicate=next(n.args[0] for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require' and len(n.args)>1 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='role extent differs')
from types import SimpleNamespace
ck(eval(compile(ast.Expression(predicate),'<exact-extent-predicate>','eval'),{'exact_size':actual_size,'before':SimpleNamespace(st_size=lib['bytes'])}) is False,'unchanged real extent guard refuses before owner construction')
review={'decision':'refused','candidate_manifest':refs[str(N/'MANIFEST01.json')],'checks':checks,'references':refs,'findings':[{'severity':'P1','path':str(N/'compact_mcm_batched.py'),'line':size.lineno,'function':'_edge_inputs','issue':'Genuine registered library role still uses exact_size17072, while authenticated policy library and selected EdgeOwner require21920. read_reference raises role extent differs before new backend can be reached.','expected_library_bytes':21920,'actual_caller_exact_size':actual_size,'required_successor':'New immutable candidate corrects the selected new-policy library extent at this caller seam and updates exact compact source requirement/pins; preserve old source and failure. Do not remove extent validation or broaden genuine role/path/hash guards.'}],'accepted_subscope':['Five owner literal inverse exact; memo owner pin only; remaining seven routes byte-identical acceptedcaller03.','Adapter matches previously source-reviewed two-attribute body.','Current C/library/runtime/ABI hashes and metadata extents match policy; installed adapter destination is prospective only.','Default None and old-format refusal retained in exact extracted pure parser.'],'execution_release':False,'installed':False,'native_or_scientific_import':False,'remaining_limits':['This concrete early refusal blocks complete real-caller source release.','No real Admission/Owner/Run, native loader, numerical arithmetic, Session/checkpoint execution, performance or capacity was tested.','Prior lifecycle/currentness/cleanup and arithmetic reviews reused, not rerun.']}
dump(O/'REVIEW01.json',review)
(O/'REPORT.md').write_text('Refused complete prospective caller01: compact_mcm_batched._edge_inputs at line121 still requires17,072B; the authenticated new library is21,920B. Exact extracted size expression plus unchanged read_reference extent predicate deterministically refuses with role extent differs before backend construction. Five owner literal changes, sole memo pin, seven unchanged routes, accepted adapter and public C/library/runtime/ABI joins otherwise match. A new immutable successor must correct this explicit new-policy caller extent and dependent source pins, preserving bounded extent and all genuine guards. No native/scientific imports or genuine authority execution occurred. Source-only parser and AST expression checks are not real runtime proof.\n')
dump(O/'MANIFEST01.json',{'status':'FROZEN_REFUSED_REAL_CALLER_SOURCE','files':{p.name:ref(p) for p in sorted(O.iterdir()) if p.name!='MANIFEST01.json'}})
print(json.dumps({'review':ref(O/'REVIEW01.json'),'manifest':ref(O/'MANIFEST01.json'),'checks':len(checks)}))
