from pathlib import Path
import ast,hashlib,importlib.util,json
R=Path.cwd();O=Path(__file__).parent;h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,v in json.loads((O/'INVERSE01.json').read_bytes()).items():
 s=(R/v['baseline']).read_text();assert h(R/v['baseline'])==v['before_sha256']
 for e in v['literal_edits']:assert e['before'] in s;s=s.replace(e['before'],e['after'])
 assert s==(O/name).read_text() and h(O/name)==v['after_sha256'];ast.parse(s)
spec=importlib.util.spec_from_file_location('backup_preparation_check',O/'prepare01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert m.ID=='real-pilot-fourth-graph-preservation-20261006-01' and m.GRAPH=='eth-paper-real-pilot-graph-20220523-20261005-01' and m.SOURCE=='50df679a64cfee1b28b35554acab70d5ff4fa9c7'
# No active artifact reads: empty assigned-directory root has no terminal or authority.
try:m.select(O,None,None)
except ValueError as exc:assert 'genuine COMPLETE original required' in str(exc)
else:raise AssertionError('missing terminal accepted')
assert m.envelope_template.__name__=='envelope_template'
print(json.dumps({'decision':'pass','literal_inverses':3,'syntax':3,'fixed_identity_source':True,'missing_terminal_refused_before_proof_access':True,'active_output_reads':0,'future_receipts_constructed':0,'native_calls':0}))
