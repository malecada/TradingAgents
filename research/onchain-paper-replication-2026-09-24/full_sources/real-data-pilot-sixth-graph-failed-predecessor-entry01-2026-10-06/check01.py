from pathlib import Path
import ast,hashlib,json
D=Path(__file__).resolve().parent;M=D.parents[3];inv=json.loads((D/'INVERSE01.json').read_bytes());new=(D/'preflight01.py').read_text();old=(M/inv['baseline']).read_text();lines=new.splitlines(True)
for h in reversed(inv['hunks']):assert lines[h['candidate_start']:h['candidate_end']]==h['candidate'];lines[h['candidate_start']:h['candidate_end']]=h['original']
assert ''.join(lines)==old and hashlib.sha256(old.encode()).hexdigest()==inv['baseline_sha256']
node=next(n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef) and n.name=='preceding_storage');ns={'ROOT':M,'Path':Path,'json':json,'file_hash':lambda p:hashlib.sha256(p.read_bytes()).hexdigest()};exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-predecessor-check','exec'),ns)
for bad in ({},{'storage_closure_review':None}):
 try:ns['preceding_storage'](bad)
 except ValueError as e:assert 'null drafts refuse' in str(e)
 else:raise AssertionError('missing future proof accepted')
# Deliberately invalid negative fixture: not a future success/claim or authority.
p=D/'invalid-disposition.json';p.write_text('{"decision":"failed"}\n');ref={'path':str(p.relative_to(M)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
try:ns['preceding_storage']({'storage_closure_review':ref})
except ValueError as e:assert 'actual failed-scope full BYTE recovery required' in str(e)
else:raise AssertionError('failed preservation incorrectly admitted')
assert "NAME='eth-paper-real-pilot-graph-20220606-20261005-01'" in new
assert "admission.effective_attempt_budget!=71" in new
assert "policy.get('failed_predecessor_retained')!=predecessor" in new
assert "free<policy['startup_free_requirement_bytes']" in new and "available<job['resources']['start_reserve_bytes']" in new
assert 'storage_retirement_complete' not in new and 'PREDECESSOR_LEDGER_BYTES' not in new
result={'status':'pass-source-only','exact_inverse':True,'missing_null_wrong_disposition_refusals':3,'original_unused_june6_identity_unchanged':True,'existing_budget71_and_fresh_storage_ram_checks_retained':True,'future_success_or_retirement_fabricated':False,'actual_body_reads':0,'native_network_git_calls':0}
(D/'CHECK01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
