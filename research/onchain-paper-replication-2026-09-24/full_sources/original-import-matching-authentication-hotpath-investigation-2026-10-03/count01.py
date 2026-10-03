"""Read-only source reconstruction; synthetic metadata only, no authority/timing."""
import ast
import hashlib
import json
import struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
PREP=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/original-import-native-successor-preparation05-2026-10-03'
CAP=PREP/'capsule03'
PREFIX='tradingagents/research/onchain_replication/'
inventory=json.loads((PREP/'source_inventory03.json').read_bytes())['source_inventory']
pins={v['target']:v for v in inventory}
checked={}
def source(name):
    name=PREFIX+name
    raw=(CAP/name).read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    assert digest==pins[name]['sha256']
    checked[name]=digest
    return ast.parse(raw)
def function(tree, cls, name):
    body=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==cls).body if cls else tree.body
    return next(n for n in body if isinstance(n,ast.FunctionDef) and n.name==name)
def calls(fn,name):
    return sum(isinstance(n,ast.Call) and ast.unparse(n.func)==name for n in ast.walk(fn))

stage=source('original_import_stage.py')
prep=source('original_import_preparation.py')
target=source('imported_mcm_identity.py')
matcher=source('compact_matcher.py')
log=source('compact_pair_log.py')
original=source('original_dictionary.py')
binding=source('matching_owner.py')
for n in ['compact_mcm.py','matching_checkpoint.py','matching_annealing.py','mcm_score_stream.py','compact_owner.py','environment.py']:
    source(n)
assert calls(function(target,'Target','lease'),'self.execution.check')==1
assert calls(function(stage,'ImportedExecution','check'),'stage.lease')==1
assert calls(function(stage,'ImportedExecution','check'),'stage.prepared.execution_contract')==1
assert calls(function(stage,'ImportStage','lease'),'self.prepared._check')==1
assert calls(function(prep,'PreparedImport','execution_contract'),'self._check')==2
assert calls(function(prep,'PreparedImport','execution_contract'),'self.stage_contract')==1
assert calls(function(prep,'PreparedImport','stage_contract'),'self._check')==1
assert calls(function(prep,'PreparedImport','_check'),'self._bound.check')==1
assert calls(function(prep,'PreparedImport','_check'),'self._cap.check')==1
assert calls(function(original,'ImportedOriginal','_check'),'validate')==1
assert calls(function(binding,'Binding','check'),'run._check_source')==1
assert calls(function(binding,'Binding','check'),'inventory')==1
assert calls(function(matcher,'CompactMatcher','_check'),'self.lease')==1
assert calls(function(matcher,'CompactMatcher','_check'),'self.log._check')==1
assert calls(function(log,'PairLog','_check'),'self.lease')==1

# Execute only the original representative-membership comprehension, using
# 512 scalar sentinel records and 32 representatives. No historical data read.
validate=function(original,None,'validate')
comp=next(n for n in ast.walk(validate) if isinstance(n,ast.ListComp) and ast.unparse(n).startswith('[j for j, x in enumerate(s['))
code=compile(ast.Expression(comp),'<exact-selected-representative-comprehension>','eval')
count=0
def canonical(value):
    global count
    count+=1
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
s={'graphs':[{'sentinel':i} for i in range(512)]}
for g in s['graphs'][:32]:
    result=eval(code,{'s':s,'g':g,'canonical':canonical})
    assert result==[g['sentinel']]
assert count==32768
report={
 'qualification':'Source call expansion and exact scalar-sentinel comprehension only; no genuine authority, numerical data, OS job, profiler or wall-time estimate.',
 'source_sha256':checked,
 'per_successful_Target_lease':{'PreparedImport_check':4,'Binding_check':4,'original_validate':4,
   'original_role_body_reads_excluding_other_controls':4*2*11,
   'representative_sample_comparisons':4*32*512,'membership_graph_canonical_calls':4*count},
 'per_successful_CompactMatcher_check':{'Target_lease':2,'Binding_check':8,'original_validate':8,
   'representative_sample_comparisons':8*32*512,'membership_graph_canonical_calls':8*count},
 'synthetic_one_validate':{'sample_records':512,'representatives':32,'canonical_calls':count},
 'local_once_per_validate_canonical_index_proposal':{'canonical_calls':512+32,'not_implemented':True,'not_wall_time_speedup':True},
 'event_record_bytes':struct.calcsize('<QB7xQdQ32s32s32s')+32,
 'registered_schedule':json.loads((CAP/'fixture_inputs/success/compact_policy.json').read_bytes())['stage_policy']['schedule'],
}
print(json.dumps(report,indent=2,sort_keys=True))
