"""Independent real-source read-only lineage plus qualified source mutations."""
import ast,copy,hashlib,json,runpy
from pathlib import Path
from types import SimpleNamespace
H=Path(__file__).resolve().parent;F=H.parent;C=F/'held-consumer-auxiliary-source-pins-preparation02-2026-10-03';P=F/'held-consumer-auxiliary-source-pins-preparation01-2026-10-03'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha((C/'MANIFEST02.json').read_bytes())=='2561573ec56fd942f1adda622ef9e39541be3c9ee4438d0893d2a95afa6de209'
members=json.loads((C/'MANIFEST02.json').read_bytes())['files']
if isinstance(members,dict):members=[dict(v,path=k) for k,v in members.items()]
for row in members:
 b=(C/row['path']).read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256']
for n in ['generate_inputs01.py','build_release_draft01.py']:assert (C/n).read_bytes()==(P/n).read_bytes()
receipt=json.loads((F/'held-consumer-root-source-composition04-2026-10-03/SOURCE_COMPOSITION04.json').read_bytes());S=Path(receipt['source_root']);HEAD=receipt['actual_source_commit'];ANCHOR=receipt['actual_148_package_anchor'];rows=sorted([{'path':r['target'],'sha256':r['sha256'],'bytes':r['bytes']} for r in receipt['source_entries']],key=lambda r:r['path'])
assert (C/'capsule_builder01.py.baseline04.txt').read_bytes()==(S/'fixture_tools/capsule_builder01.py').read_bytes()
# Both modules' top-level code is stdlib imports/constants/function definitions.
# No exporter, graph generator, legacy registration or job entry is called.
B=runpy.run_path(str(C/'capsule_builder01.py'));OLD=runpy.run_path(str(S/'fixture_tools/capsule_builder01.py'))
def refusal(call):
 try:call()
 except (ValueError,KeyError,TypeError) as e:return str(e)
 raise AssertionError('unexpected acceptance')
assert refusal(lambda:OLD['held_source_plan'](S,HEAD,ANCHOR,rows))=='held anchor must genuinely descend directly from original S2'
plan=B['held_source_plan'](S,HEAD,ANCHOR,rows);assert len(plan['source_files'])==199 and len(plan['package_files'])==148 and plan['execution_admitted'] is False
def load(path,names,env):
 nodes=[n for n in ast.parse(path.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in names or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in n.targets)]
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),env)
G={'Path':Path,'json':json,'hashlib':hashlib};load(C/'generate_inputs01.py',{'canonical','sha','require','HELD_ROLES','AUXILIARY_ROLES','_held_ref','held_input_plan','held_auxiliary_metadata','render_held_auxiliary_declaration'},G)
null=G['held_input_plan']({},plan);assert len(null['remaining_roles'])==15 and null['auxiliary_metadata'] is None and null['execution_admitted'] is False
checks=['actual old lineage RED/new199body+148anchor GREEN','actual null15-role plan is unadmitted']
fn=B['held_source_plan'];ns=fn.__globals__;real=ns['_held_git']
for case in ['wrong_parent','source_not_descendant','extra_current_package','missing_anchor_package']:
 def fake(root,*args):
  if case=='wrong_parent' and args==('show','-s','--format=%P','903488c49ad25e8026ec849a1c8b30ca5f90bcff'):return b'0'*40+b'\n'
  if case=='source_not_descendant' and args==('merge-base','--is-ancestor',B['HELD_SOURCE04'],HEAD):raise ValueError('qualified non-descendant response')
  raw=real(root,*args)
  if case=='extra_current_package' and args==('ls-tree','-r','--name-only',HEAD):return raw+b'tradingagents/research/unlisted.py\n'
  if case=='missing_anchor_package' and args==('ls-tree','-r','--name-only',ANCHOR):return b'\n'.join(x for x in raw.split(b'\n') if x!=b'tradingagents/research/onchain_replication/resource_fixture.py')
  return raw
 ns['_held_git']=fake
 try:refusal(lambda:fn(S,HEAD,ANCHOR,rows))
 finally:ns['_held_git']=real
 checks.append(case+' refused (explicit Git-response injection)')
for case in ['missing_row','extra_row','dispatch_hash','source_helper_hash']:
 altered=copy.deepcopy(rows)
 if case=='missing_row':altered.pop()
 elif case=='extra_row':altered.append({'path':'extra.py','sha256':'0'*64,'bytes':1})
 else:next(r for r in altered if r['path']==('tradingagents/research/onchain_replication/resource_fixture.py' if case=='dispatch_hash' else 'fixture_tools/capsule_builder01.py'))['sha256']='0'*64
 refusal(lambda:fn(S,HEAD,ANCHOR,altered));checks.append(case+' refused')
# Whole source inverse: exactly four fixed constants plus the one function delta.
a=(C/'capsule_builder01.py.baseline04.txt').read_text();b=(C/'capsule_builder01.py').read_text();ta=ast.parse(a);tb=ast.parse(b);af=next(n for n in ta.body if isinstance(n,ast.FunctionDef) and n.name=='held_source_plan');bf=next(n for n in tb.body if isinstance(n,ast.FunctionDef) and n.name=='held_source_plan');edits=[(bf.lineno,bf.end_lineno,a.splitlines(True)[af.lineno-1:af.end_lineno])]
for n in tb.body:
 if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id.startswith('HELD_SOURCE04') for v in n.targets):edits.append((n.lineno,n.end_lineno,[]))
assert len(edits)==5;lines=b.splitlines(True)
for start,end,replacement in sorted(edits,reverse=True):lines[start-1:end]=replacement
assert ''.join(lines)==a and ast.dump(ast.parse(''.join(lines)))==ast.dump(ta)
bf=copy.deepcopy(bf);bf.body=[n for n in bf.body if not(isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='source04')];restored=[]
for n in bf.body:
 if isinstance(n,ast.If) and ast.unparse(n.test)=='source04':restored.extend(n.orelse)
 else:restored.append(n)
bf.body=restored;assert ast.dump(bf)==ast.dump(af);checks.append('whole inverse bytes/AST plus original function inverse exact')
# Full draft refuses genuinely uninstalled candidate module origins before any
# source check. No synthetic positive module-origin labels are used in this review.
class NoImports(ast.NodeTransformer):
 def visit_ImportFrom(self,n):return ast.copy_location(ast.Pass(),n)
draft=next(n for n in ast.parse((C/'build_release_draft01.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='held_metadata_draft')
d={'Path':Path,'json':json,'require':B['require'],'__file__':str(C/'build_release_draft01.py'),'builder':SimpleNamespace(__file__=str(C/'capsule_builder01.py')),'generator':SimpleNamespace(__file__=str(C/'generate_inputs01.py'))}
exec(compile(ast.fix_missing_locations(NoImports().visit(ast.Module(body=[draft],type_ignores=[]))),str(C/'build_release_draft01.py'),'exec'),d)
assert 'helper origin differs' in refusal(lambda:d['held_metadata_draft'](S,HEAD,ANCHOR,rows,{}));checks.append('actual uninstalled origin refusal; no origin-label positive authority')
inventory=json.loads((C/'PROSPECTIVE_IMPLEMENTATION_SOURCES02.json').read_bytes());print('INVENTORY_SCHEMA',list(inventory))
result={'scope':'uninstalled candidate source verification; real Source04 Git/current/anchor source reads only','candidate_builder_sha256':sha(b.encode()),'author_manifest_members':len(members),'checks':checks,'actual_source_plan':plan,'null_roles':null,'native_jobs_claims':0,'numerical_imports':False}
(H/'READBACK02.json').write_text(json.dumps(result,indent=2)+'\n')
for check in checks:print('PASS',check)
print('PASS',len(checks),'independent bounded checks;',len(members),'author members; no installed helper/admission/native claim')
