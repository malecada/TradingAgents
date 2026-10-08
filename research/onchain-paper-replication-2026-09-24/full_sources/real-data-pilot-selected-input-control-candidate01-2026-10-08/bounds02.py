import importlib.util,json,pathlib,types
from unittest.mock import patch
H=pathlib.Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('tradingagents.research.onchain_replication._input_bounds',H/'stage_retention.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
from tests.research.onchain_replication.test_restart_retention_integration import retention_policy
checks=[]
def refuse(name,fn):
 try:fn()
 except ValueError:checks.append(name);return
 raise AssertionError(name)
refuse('physical JSON ceiling strictly under1GiB',lambda:m.validate(retention_policy()|{m.INPUT_JSON_FIELD:1024**3}))
# Worst case UTF16 escaped bounds for a declared future ID length; this is
# metadata arithmetic, not decoding real identifiers or numeric arrays.
records=[{'node_ids':('0','1'+'\U0001f600'*6000),'parent_hash':'a'*64,'center_id':'0','numeric_bytes':{'node_features':32,'edge_index':16,'edge_features':8}}]*2
bound=m.selected_input_bound(0,records)
assert bound>131072
obj=object.__new__(m.Controller);obj.policy={m.INPUT_JSON_FIELD:8192}
a=types.SimpleNamespace(node_ids=records[0]['node_ids'],parent_hash='a'*64,center_id='0',node_features=types.SimpleNamespace(nbytes=32),edge_index=types.SimpleNamespace(nbytes=16),edge_features=types.SimpleNamespace(nbytes=8))
with patch.object(m.Controller,'_reserve',side_effect=AssertionError('reserved before extent refusal')),patch.object(m.np,'save',side_effect=AssertionError('numeric serialization before refusal')):
 refuse('oversized metadata refuses before reserve/array encoding',lambda:obj._inputs_bounded(0,a,a))
print(json.dumps({'status':'PASS','checks':checks,'count':len(checks),'large_escaped_fixture_bound':bound,'maximum_selected_json_bytes':m.INPUT_JSON_MAX},indent=2))
