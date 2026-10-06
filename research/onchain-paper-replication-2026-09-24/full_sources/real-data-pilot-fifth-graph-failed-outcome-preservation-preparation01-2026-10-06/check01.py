from pathlib import Path
import ast,hashlib,importlib.util,json,sys
D=Path(__file__).resolve().parent;M=D.parents[3];h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,record in json.loads((D/'INVERSE01.json').read_bytes()).items():
 lines=(D/name).read_text().splitlines(True);assert h(D/name)==record['candidate_sha256']
 for step in reversed(record['hunks']):
  a,b=step['candidate_start'],step['candidate_end'];assert lines[a:b]==step['candidate'];lines[a:b]=step['original']
 assert ''.join(lines).encode()==(M/record['baseline']).read_bytes() and h(M/record['baseline'])==record['baseline_sha256'];ast.parse((D/name).read_bytes())
spec=importlib.util.spec_from_file_location('failed_preservation_metadata',D/'prepare01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert m.ID=='real-pilot-fifth-graph-failed-preservation-20261006-01' and sum(m.OPAQUE_BYTES.values())==3278655680 and len(m.OPAQUE_BYTES)==3
empty=D/'empty-scope';empty.mkdir()
try:m.select(empty,None,None)
except ValueError as exc:assert 'genuine FAILED original required' in str(exc)
else:raise AssertionError('missing failed original accepted')
# Actual terminal path existence only; no body/proof/current payload access occurs.
try:m.select(M,None,None)
except ValueError as exc:assert 'actual independent outcome and body references required' in str(exc)
else:raise AssertionError('null future proofs accepted')
# Failed native/source selection must explicitly preserve original distinctions.
source=(D/'prepare01.py').read_text()
assert "terminal['source']" not in source and "guard['child_exit_code'] == 125" in source and "guard['cleanup_stop_returncode'] == 0" in source
assert "cells[1]['status'] == 'unavailable'" in source and "cells[0]['rows'] == 7507236" in source
assert "set(payloads) == set(OPAQUE_BYTES)" in source
assert all(n not in sys.modules for n in ('numpy','torch','scipy','pyarrow'))
print(json.dumps({'status':'pass-source-only','exact_inverses':3,'missing_failed_and_null_proof_refusals':2,'opaque_body_count':3,'declared_opaque_bytes':3278655680,'actual_payload_reads':0,'authority_or_future_success_constructed':False,'native_network_calls':0}))
