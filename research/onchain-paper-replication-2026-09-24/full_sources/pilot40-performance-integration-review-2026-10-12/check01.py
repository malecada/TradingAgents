import os,resource
os.sched_setaffinity(0,{2,3});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60))
import ast,json,hashlib,difflib,runpy,types
from pathlib import Path
F=Path('research/onchain-paper-replication-2026-09-24/full_sources');D=F/'pilot40-performance-integration-2026-10-12';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();m=json.loads((D/'SOURCE_INTEGRATION01.json').read_text());assert h(D/'SOURCE_INTEGRATION01.json')=='6a2883cb04682c33a12d435c62e1020cef39834a0e249c4d560030a776597118'
assert len(m['files'])==12 and sum(not r['selector_seam'] for r in m['files'])==10
patch='';inverse='';seam=''
for row in m['files']:
 p=Path(row['target']);c=Path(row['candidate']['path']);assert h(p)==row['final_sha256'] and p.stat().st_size==row['final_bytes'];assert h(c)==row['candidate']['sha256']==row['installed_sha256']
 if not row['selector_seam']:assert p.read_bytes()==c.read_bytes()
 else:seam+=''.join(difflib.unified_diff(c.read_text().splitlines(True),p.read_text().splitlines(True),fromfile=str(c),tofile=str(p)))
 bp=Path(row['baseline_path']) if row.get('baseline_path') else None
 if bp:assert h(bp)==row['baseline_sha256']
 before=bp.read_text() if bp else '';old=str(bp) if bp else '/dev/null'
 patch+=''.join(difflib.unified_diff(before.splitlines(True),p.read_text().splitlines(True),fromfile=old,tofile=str(p)))
 inverse+=''.join(difflib.unified_diff(p.read_text().splitlines(True),before.splitlines(True),fromfile=str(p),tofile=old))
assert patch==(D/'INTEGRATION_PATCH01.diff').read_text() and inverse==(D/'INTEGRATION_INVERSE01.diff').read_text() and seam==(D/'SELECTOR_SEAM01.diff').read_text()
print('PINS_INVERSE_PASS',flush=True)
# Fresh finite closure from authored definition, no job import/execution.
S=Path('tradingagents/research/onchain_replication');tree=ast.parse((S/'job.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='required_sources');env={'Path':Path,'__file__':str((S/'job.py').resolve())};exec(compile(ast.Module([fn],[]),str(S/'job.py'),'exec'),env);closure=env['required_sources']();pins=m['required_sources'];assert len(closure)==m['required_sources_count']==206 and closure==set(pins)
for p,digest in pins.items():assert h(Path(p))==digest
assert str(S/'weekly_graph_digest_pin.py') in closure
# New selector runtime prefix: refuse nonbool before Target, preserve absence/False keyword omission.
ct=ast.parse((S/'compact_mcm.py').read_text());producer=next(n for n in ct.body if isinstance(n,ast.FunctionDef) and n.name=='produce_imported');prefix=[]
for n in producer.body:
 if isinstance(n,ast.ImportFrom):continue
 prefix.append(n)
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='target' for t in n.targets):break
producer.body=prefix
calls=[]
def require(v,msg):
 if not v:raise ValueError(msg)
e={'require':require,'Target':lambda *a,**kw:calls.append(kw)};exec(compile(ast.Module([producer],[]),'<installed-producer-prefix>','exec'),e)
for val in [None,0,1,'true',[],{}]:
 try:e['produce_imported'](None,None,graph_hash='x',input_name='i',output_input='o',weekly_digest_pin=val)
 except ValueError:pass
 else:raise AssertionError(val)
assert calls==[]
for kw in [{},{'weekly_digest_pin':False},{'weekly_digest_pin':True}]:e['produce_imported'](None,None,graph_hash='x',input_name='i',output_input='o',**kw)
assert calls==[{},{},{'weekly_digest_pin':True}]
# Validate actual installed pure plan validator using public schema metadata.
import sys
sys.path.insert(0,str(Path.cwd()))
from tradingagents.research.onchain_replication import real_pilot_import_caller as caller
p=json.loads((F/'real-data-pilot-full39-binding-preparation01-2026-10-12/public01/pilot.json').read_text())
for kw in [{},{'weekly_graph_digest_pin':False},{'weekly_graph_digest_pin':True}]:q=p|kw;assert caller.validate_plan(q) is q
q=p|{'weekly_graph_digest_pin':True,'schema_version':1}
try:caller.validate_plan(q)
except ValueError:pass
else:raise AssertionError('schema1 selector accepted')
# Module-scope pin import and original caller import precede activate.
ic=(S/'imported_mcm_identity.py').read_text();cs=(S/'real_pilot_import_caller.py').read_text();assert 'from . import weekly_graph_digest_pin' in ic and cs.index('from .imported_mcm_identity import Target',cs.index('def execute('))<cs.index("activate(execution,p['imported_authority_lease_input'])")
# Tiny composed installed serializer + weekly pin, never original worker/Owner.
ns=runpy.run_path(str(F/'pilot-graph-hash-serialization-candidate-2026-10-12/check_serialization01.py'));newhash=ns['hashes'](S/'neighborhoods.py')['graph_hash'];g=ns['graph'](4);t=ast.parse((S/'weekly_graph_digest_pin.py').read_text());t.body=[n for n in t.body if not(isinstance(n,ast.ImportFrom) and n.level)];e={'np':ns['np'],'GraphSnapshot':ns['ctx']['GraphSnapshot'],'validate_graph':ns['ctx']['validate_graph'],'graph_hash':newhash};exec(compile(t,str(S/'weekly_graph_digest_pin.py'),'exec'),e)
expected=ns['base']['graph_hash'](g);assert newhash(g)==expected;state=e['create'](g,original_digest=expected);assert state is not None and e['verify'](g,state)[0]==expected
object.__setattr__(g,'asset','BTC');digest,state=e['verify'](g,state);assert state is None and digest==ns['base']['graph_hash'](g)==newhash(g)!=expected
print(json.dumps({'status':'PASS','exact_installs':10,'selector_seams':2,'required_source_count':206,'full_patch_inverse_and_selector_diff':True,'producer_default_false_and_nonbool_refusal':True,'schema2_only':True,'helper_import_before_activation':True,'tiny_composed_serializer_pin_and_mutation_fallback':True,'genuine_lease_admission_or_job_executed':False},indent=2))
