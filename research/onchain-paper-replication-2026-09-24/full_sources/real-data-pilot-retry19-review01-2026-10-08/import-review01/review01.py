"""Exact import-placement inverse and bounded independent boundary check."""
from pathlib import Path
import ast,datetime,difflib,hashlib,json,os,statistics,subprocess,sys
H=Path(__file__).resolve().parent;R=H.parents[4];D=H.parent.parent/'real-data-pilot-startup-lazy-engine-correction01-2026-10-08'
evidence={}
def raw(p):
 b=p.read_bytes();assert p.resolve(strict=True)==p and p.stat().st_size==len(b)<1024**2;evidence[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def read(p):return json.loads(raw(p))
def ref(p):return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(raw(p)).hexdigest()}
manifest=read(D/'MANIFEST01.json');rows=manifest['candidate_sources']['files'];assert len(rows)==4
for name,pin in manifest['files'].items():assert hashlib.sha256(raw(D/name)).hexdigest()==pin['sha256'] and len(raw(D/name))==pin['bytes']
for path,digest in manifest['inspected_dependency_sha256'].items():assert hashlib.sha256(raw(R/path)).hexdigest()==digest
expected_functions={'write','identity','policy_check','_reserve','create','resume','step','save','close'}
for row in rows:
 before=raw(D/('baseline_'+row['candidate']));after=raw(D/row['candidate'])
 assert raw(R/row['target'])==before and hashlib.sha256(before).hexdigest()==row['before_sha256'] and hashlib.sha256(after).hexdigest()==row['after_sha256']
 compile(after,str(D/row['candidate']),'exec')
 if row['candidate']=='matching_pair.py':
  line=b'    from . import matching_checkpoint as engine\n';assert after.splitlines(keepends=True).count(line)==3
  # Three module functions plus six indented methods.
  assert after.count(b'        from . import matching_checkpoint as engine\n')==6
  inverse=after.replace(b'        from . import matching_checkpoint as engine\n',b'').replace(line,b'').replace(b'LIMIT = 65536',b'from . import matching_checkpoint as engine\nLIMIT = 65536',1)
  assert inverse==before
  funcs=[n for n in ast.walk(ast.parse(after)) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
  moved={n.name for n in funcs if n.body and isinstance(n.body[0],ast.ImportFrom) and any(a.name=='matching_checkpoint' and a.asname=='engine' for a in n.body[0].names)}
  assert moved==expected_functions
 elif row['candidate']=='compact_matcher.py':assert after.replace(b'from . import matching_checkpoint as engine\n',b'engine = pair.engine\n')==before
 else:
  alias=b'm.engine' if row['candidate']=='test_matching_pair_checkpoints.py' else b'pair.engine'
  assert b'from tradingagents.research.onchain_replication import matching_checkpoint as engine\n'+before.replace(alias,b'engine')==after
# Patches are independently reconstructed exactly, with original target labels.
for name,inverse in [('FORWARD01.patch',False),('INVERSE01.patch',True)]:
 body=''
 for row in rows:
  a=raw(D/('baseline_'+row['candidate'])).decode();b=raw(D/row['candidate']).decode()
  if inverse:a,b=b,a
  body+=''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+row['target'],tofile='b/'+row['target']))
 assert body.encode()==raw(D/name)
# Search active production consumers; keep removed alias compatibility explicitly scoped.
search=subprocess.run(['rg','-n',r'(pair|matching_pair)\.engine|from .*matching_pair import.*engine','tradingagents/research/onchain_replication','--glob','*.py'],cwd=R,capture_output=True,text=True,check=True)
assert search.stdout.strip()=='tradingagents/research/onchain_replication/compact_matcher.py:23:engine = pair.engine'
# Reconstruct final observed differences; no cold measurements or42 tests rerun.
measurement=read(D/'FINAL_MEASUREMENT01.json');diff=[]
for i in (0,2,4):
 a=read(D/f'final-{i:02d}-baseline.json');b=read(D/f'final-{i+1:02d}-candidate.json');diff.append(a['after']['Pss_bytes']-b['after']['Pss_bytes'])
 assert not b['engine_loaded'] and not b['scipy_special_loaded'] and b['numpy_loaded'] and a['engine_loaded']
assert statistics.median(diff)==measurement['median_Pss_reduction_bytes']==18693120
checks=read(D/'CHECK_RESULTS01.json');assert all(c['returncode']==0 for c in checks);assert '42 passed' in raw(D/'FUNCTIONAL01.stdout').decode()
# One fresh independent process: engine absence fail-closed across every moved boundary.
env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
run=subprocess.run([str(R/'.venv/bin/python'),'-B',str(H/'boundaries01.py')],cwd=R,env=env,capture_output=True,text=True,timeout=20)
for suffix,data in [('stdout',run.stdout),('stderr',run.stderr)]:
 with (H/('BOUNDARIES01.'+suffix)).open('x') as f:f.write(data)
assert run.returncode==0,run.stderr
actual=json.loads(run.stdout);assert actual['decision']=='passed' and set(actual['all_nine_deferred_engine_refusals'])==expected_functions
for p in [H/'boundaries01.py',H/'BOUNDARIES01.stdout',H/'BOUNDARIES01.stderr',Path(__file__)]:raw(p)
result={'schema_version':1,'decision':'accepted-source-adoption-only','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Exact two production imports and two corresponding test-reference copies only','candidate_sources':rows,'evidence':dict(sorted(evidence.items())),'exact_inverse_bytes':True,'all_nine_first_engine_boundaries_fail_closed':True,'independent_boundary_result':actual,'production_alias_consumer_search':search.stdout.strip(),'worker_checks_reused':checks,'measurement_reconstructed_median_pss_difference_bytes':18693120,
'compatibility':'The undocumented matching_pair.engine alias is intentionally removed. The sole active production consumer compact_matcher is switched to the same original matching_checkpoint module; two active test consumers use that exact module directly. Other preserved historical copies are unchanged. Root must adopt all four candidate copies together.',
'qualification':'All non-import production bytes invert exactly; constants, operation order, source/context identity, algorithms, numerical engine, checkpoint/fsync/cleanup, resource predicates and native ownership are unchanged. One fresh bounded independent import process verified metadata without engine availability; every one of nine moved first-use imports propagates genuine import refusal before work; later compact_matcher resolves exact original engine and invalid workflow context remains refused. No graph/array matching operations were executed. Earlier42 synthetic tests/four boundary checks reused, not repeated.',
'not_tested':['No new empirical/native run, historical data/private transport, full runtime admission or scientific method-performance check.','Per-process cold PSS observations do not measure aggregate host saving, explain pilot18 host decline or prove future startup/whole capacity.','Startup-reserve amendment, strict19 metadata, proposed90 and future exact entry require their own explicit accepted joins; this source review does not release19.']}
p=H/'SOURCE_REVIEW01.json'
with p.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'decision':result['decision'],'review':ref(p)}))
