from pathlib import Path
import hashlib,json,runpy
C=Path('research/onchain-paper-replication-2026-09-24/full_sources/pilot-verification-history-policy-candidate-2026-10-12');D=Path(__file__).resolve().parent;h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert h(C/'SOURCE_MANIFEST04.json')=='2aa442da0684b19320afa8063c0360c749a616c0a7ddfb1c35039281b1188fa3';m=json.loads((C/'SOURCE_MANIFEST04.json').read_text())
for row in m['files']:
 p=Path(row['path']);assert p.stat().st_size==row['bytes'] and h(p)==row['sha256']
for row in m['targets']:
 p=C/Path(row['target']).name;assert h(p)==row['candidate_sha256'];assert h(C/('BASELINE_'+p.name))==row['baseline_sha256']
runpy.run_path(str(D/'check_frontier01.py'));runpy.run_path(str(D/'check_binding01.py'))
ns=runpy.run_path(str(C/'check01.py'));f=ns['Fixture'](2)
try:
 f.env['_HISTORY_MAX_RUNS']=1
 try:f.env['_history_prior'](None,f.root,'gate','own','source','source',f.raw,f.policy,False)
 except ValueError as e:assert 'roster exceeded' in str(e) and not f.events
 else:raise AssertionError('startup bound bypass')
 assert not f.env['_HISTORY'] and not f.env['_HISTORY_BUSY']
finally:f.close()
print(json.dumps({'status':'PASS_three_amendments_only','manifest04_and_all_candidate_files':True,'nonblocking_FIFO_refusal':True,'same_claim_different_run_transplant_refusal':True,'startup_cap_refusal_before_verifier_no_seed':True,'admission_sha256':h(C/'admission.py'),'benchmark_sha256':h(C/'benchmark01.py')},indent=2))
