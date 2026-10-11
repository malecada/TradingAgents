"""Exact actual admission reference guard only; no admission/Git/claims."""
import ast,hashlib,json,re
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];D=F/'real-data-pilot-full31-entry-preparation02-2026-10-11'
gateb=(D/'gate01.json').read_bytes();gate=json.loads(gateb);exp=gate['experiments']['eth-paper-real-data-end-to-end-resource-20261011-31'];draft=json.loads((D/'BINDING_DRAFT01.json').read_bytes())
tree=ast.parse((R/'tradingagents/research/admission.py').read_bytes());fn=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='extension_metadata');ns={'re':re,'exp':exp};exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual-extension-metadata-guard','exec'),ns)
failures={}
for role,ref in exp['cumulative_budget_extension'].items():
    try:ns['extension_metadata'](ref)
    except ValueError as error:failures[role]={'error':str(error),'actual_keys':sorted(ref)}
    else:raise AssertionError('expected concrete reference refusal')
assert set(failures)=={'extension','review'} and all(x['error']=='budget extension metadata must be source-pinned' for x in failures.values())
out={'decision':'WITHHOLD_ORIGINAL_GATE01_CONCRETE_METADATA_DEFECT','gate_sha256':hashlib.sha256(gateb).hexdigest(),'actual_guard_failures':failures,'binding_budget_review_keys':sorted(draft['budget_review']),'required_correction':'New successor gate uses exact path/sha256 budget refs, and matching Binding budget_review matches the two-key review ref. Preserve gate01/draft01.','charter_finding':'CHARTER01 paragraph2 names redundant serializer traversal although serializer remains uninstalled; publish accurate successor charter for reused compiled route plus new three genuine lease boundaries.','no_genuine_admission_or_network':True}
with (P/'REFUSAL01.json').open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps(out,sort_keys=True))
