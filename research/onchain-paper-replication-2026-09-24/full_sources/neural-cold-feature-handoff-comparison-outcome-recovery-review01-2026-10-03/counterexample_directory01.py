"""Exact helper02 directory branch against genuine pinned archive metadata."""
import ast,hashlib,json,tarfile,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'neural-cold-feature-handoff-comparison-outcome01-2026-10-03'
source=OUT/'recover_comparison_outcome02.py';raw=source.read_bytes();assert hashlib.sha256(raw).hexdigest()=='ed851881af69b0055ffd3f0c4e0aa15fc272742be1de3985ac9615375eb830dc'
tree=ast.parse(raw);branch=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=="row['kind'] == 'directory'" and any(isinstance(x,ast.Assert) and 'member.isdir()' in ast.unparse(x.test) for x in n.body))
r=json.loads((OUT/'OUTCOME_RETENTION01.json').read_bytes());expected={x['path']:x for x in r['members']};row=expected['data'];assert row=={'kind':'directory','mode':509,'path':'data'}
with tarfile.open(OUT/'comparison-outcome01.tar.gz','r:gz') as tf:member=tf.getmember('collection/data')
assert member.isdir() and member.size==0
with tempfile.TemporaryDirectory(dir=HERE,prefix='directory-counterexample-') as tmp:
 owned=Path(tmp);ns={'row':row,'member':member,'dest':owned/'data','owned':owned,'directories':0}
 try:exec(compile(ast.Module(body=[branch],type_ignores=[]),str(source),'exec'),ns)
 except KeyError as error:
  assert error.args==('bytes',) and not (owned/'data').exists()
 else:raise AssertionError('actual schema mismatch did not reproduce')
result={'schema_version':1,'finding':'RCO2','source_sha256':hashlib.sha256(raw).hexdigest(),'exact_error':'KeyError(bytes)','actual_directory_record':row,'actual_tar_directory_bytes':member.size,'actual_partial_recovery_members_observed':['collection.json'],'original_tool_terminal':'not yet supplied to reviewer','claim_or_numeric_or_network_invocation':False,'prior_source02_acceptance_superseded_for_this_new_actual_schema_mismatch':True}
(HERE/'COUNTEREXAMPLE_DIRECTORY01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
