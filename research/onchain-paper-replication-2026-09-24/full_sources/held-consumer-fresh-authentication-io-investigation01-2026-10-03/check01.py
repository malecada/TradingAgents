from pathlib import Path
import ast,hashlib,json
H=Path(__file__).resolve().parent;F=H.parent;R=H.parents[3];S=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-03/source');P=S/'tradingagents/research/onchain_replication'
def read(p):assert p.stat().st_size<=4*1024**2;return p.read_bytes()
def sha(b):return hashlib.sha256(b).hexdigest()
paths=[S/'tradingagents/research'/n for n in ['verify.py','admission.py','budget_extensions.py','lifecycle.py']]+[P/n for n in ['matching_owner.py','compact_owner.py','original_import_preparation.py','original_import_stage.py','imported_mcm_identity.py','compact_matcher.py','held_score_consumer.py','environment.py','compact_terminal.py','compact_native_features.py']]
refs=[]
for p in paths:
 raw=read(p);t=ast.parse(raw);calls=[{'line':n.lineno,'call':ast.unparse(n)} for n in ast.walk(t) if isinstance(n,ast.Call) and any(w in ast.unparse(n.func) for w in ['_blob','_git','_committed','_check_source','_check_inputs','inventory','_anchor_read','verify_claim'])];refs.append({'path':str(p),'sha256':sha(raw),'bytes':len(raw),'calls':calls})
assert read(S/'tradingagents/research/verify.py')==read(R/'tradingagents/research/verify.py')
v=ast.parse(read(R/'tradingagents/research/verify.py'));assert any(isinstance(n,ast.FunctionDef) and n.name=='_registration_pair' for n in v.body)
function=next(n for n in v.body if isinstance(n,ast.FunctionDef) and n.name=='verify_claim');extensionloop=next(n for n in ast.walk(function) if isinstance(n,ast.For) and isinstance(n.iter,ast.Tuple) and [x.value for x in n.iter.elts if isinstance(x,ast.Constant)]==['extension','review']);assert any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_blob' for n in ast.walk(extensionloop))
claims=[]
for i in range(1,5):
 p=F/'held-consumer-cumulative-admission-preparation02-2026-10-03/prior_claims'/('original-import-native-success-20261003-%02d'%i)/'claim.json';c=json.loads(read(p));claims.append({'identity':c['experiment_id'],'claim_sha256':sha(read(p)),'extension':c['experiment'].get('cumulative_budget_extension') is not None})
assert sum(x['extension'] for x in claims)==3
outcome=F/'neural-cold-feature-handoff-comparison-outcome-local-review01-2026-10-03/READBACK01.json';e=json.loads(read(outcome));assert abs(e['native_elapsed_seconds']-1800.8358598740015)<1e-6
prior=F/'neural-cold-feature-handoff-authority-io-cost-investigation01-2026-10-03/INVESTIGATION01.md'
result={'scope':'source-only-fresh-per-call-transport-investigation','sources':refs,'main_verify_matches_source03':True,'historical_import_claims':claims,'conditional_extension_plain_git_calls_per_scan':6,'conditional_batched_pair_calls_per_scan':3,'qualification':'Static three extension-bearing historical claims only; no actual future admission namespace or measured wall share asserted.','closed_comparison_metadata':{'path':str(outcome),'sha256':sha(read(outcome)),'native_elapsed_seconds':e['native_elapsed_seconds']},'prior_investigation':{'path':str(prior),'sha256':sha(read(prior))},'jobs':0,'numerical_imports':0,'observed_speed_gain':None}
(H/'READBACK01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print('PASS selected source hashes/AST; Main=Source03 verify registration pair already batched;3historical extension-bearing claims still2plainblobcalls each; no runtime measurement')
