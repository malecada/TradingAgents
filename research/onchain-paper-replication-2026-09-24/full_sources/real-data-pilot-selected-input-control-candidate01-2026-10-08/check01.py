import ast,hashlib,importlib,importlib.util,json,pathlib,sys,tempfile,types
from unittest.mock import patch
H=pathlib.Path(__file__).resolve().parent
import tradingagents.research.onchain_replication as package
from tradingagents.research.onchain_replication import stage_retention as old, stage_retention_reader as oldreader
from tradingagents.research.onchain_replication import compact_matcher as matcher, archive_pair_reader
from tests.research.onchain_replication import test_compact_matcher as tiny,test_restart_retention_integration as retained
from tradingagents.research.onchain_replication.provenance import thaw
spec=importlib.util.spec_from_file_location('tradingagents.research.onchain_replication._selected_stage',H/'stage_retention.py');stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage)
spec=importlib.util.spec_from_file_location('tradingagents.research.onchain_replication._selected_reader',H/'stage_retention_reader.py');reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader);reader.retention=stage
checks=[]
def check(n,x):assert x,n;checks.append(n)
def refuse(n,fn):
 try:fn()
 except (ValueError,TypeError):checks.append(n);return
 raise AssertionError(n+' accepted')
# Cover all ASCII escape classes, BMP, astral characters and escaped lone surrogate.
values=[''.join(map(chr,range(128))), 'quote"slash\\line\n', '\u00e9\u2028\U0001f600\ud800', ['x','y'], {'a':['z',123456]}]
for v in values:check('exact JSON extent',stage._json_extent(v)==len(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()))
base=retained.retention_policy();selected=base|{stage.INPUT_JSON_FIELD:131072}
check('default policy output',stage.validate(base)==old.validate(base))
for value in (True,0,-1,2**30+1,1.5):refuse('invalid JSON cap '+repr(value),lambda value=value:stage.validate(base|{stage.INPUT_JSON_FIELD:value}))
small={'schema_version':1,'graphs':[{'node_ids':['a','b']} ]}
check('default compatible JSON encoding',stage._selected_raw(small,selected)==stage.store._raw(small))
with patch.object(stage.json,'dumps',side_effect=AssertionError('encoding before refusal')):
 refuse('extent refuses before encoding',lambda:stage._selected_raw({'x':'y'*9000},base|{stage.INPUT_JSON_FIELD:8192}))
orig_graph=tiny.graph
long_id='1'+('"\\\n\U0001f600'*1000)
def graph(*a,**kw):
 g=orig_graph(*a,**kw);return types.SimpleNamespace(node_ids=(g.node_ids[0],long_id),node_features=g.node_features,edge_index=g.edge_index,edge_features=g.edge_features)
layout={'format':'sharded-npy-v1','chunk_entries':2}
for variant in ('default','sharded','selected_sharded'):
 with tempfile.TemporaryDirectory(prefix='selected-control-') as d:
  root=pathlib.Path(d);p=tiny.POLICY|({'checkpoint_layout':layout} if variant!='default' else {})
  rp=selected if variant=='selected_sharded' else base
  with patch.object(package,'stage_retention',stage),patch.dict(sys.modules,{'tradingagents.research.onchain_replication.stage_retention':stage}),patch.object(tiny,'POLICY',p),patch.object(retained,'retention_policy',return_value=rp),patch.object(tiny,'graph',graph if variant=='selected_sharded' else orig_graph):
   m,log,a,b,c,purpose,transport=retained.fixture(root,progress=True,schedule_override={'operations_per_call':1,'calls_per_checkpoint':4,'max_checkpoints':10})
  try:
   result=m(purpose,a,b);check(variant+' bitwise score',result['score'].hex()==retained.match_reference(a,b,c).score.hex())
   ref=m.retention.finish_stage();log.finish()
   args=dict(policy=rp,selection=thaw(m.retention.selection),expected_sha256=ref,start_sha256=log.start_sha)
   if variant=='sharded':refuse('RED original reader sharded aggregate',lambda:oldreader.check(root/'checkpoints',**args))
   seal=reader.check(root/'checkpoints',**args);check(variant+' full selected-input reader',seal['completed_pairs']==1 and seal['progress_events']>0)
   visitor=reader.Visitor(root/'checkpoints',**args)
   terminal=root/'log/archive-complete.json'
   archive_pair_reader.verify(root/'log',expected_sha256=hashlib.sha256(terminal.read_bytes()).hexdigest(),owner=log.start['owner'],scope=log.start['scope'],archive_policy=log.policy,attempt=root/'read',transport=transport,lease=lambda:None,max_read_metadata_bytes=1000000,on_event=visitor.visit)
   check(variant+' actual archive Visitor',visitor.finish()==seal)
   meta=root/'checkpoints/inputs/input-000000000000.json'
   if variant=='selected_sharded':
    check('oversized escaped IDs retained',16384<meta.stat().st_size<=rp[stage.INPUT_JSON_FIELD])
    reserve=json.loads((root/'checkpoints/reserve-000000000000.json').read_bytes())
    upper=stage.selected_input_bound(0,stage._input_records((a,b)))+sum(getattr(g,n).nbytes+256 for g in (a,b) for n in ('node_features','edge_index','edge_features'))
    check('exact prospective input reservation',reserve['delta']['input_bytes']==upper)
    refuse('wrong policy cannot read sealed stage',lambda:reader.check(root/'checkpoints',**(args|{'policy':base})))
  finally:log.close()
# Legacy body remains byte-for-byte except explicit dispatch preceding it.
a=ast.parse((H/'original_stage_retention.py').read_text());b=ast.parse((H/'stage_retention.py').read_text())
get=lambda t:next(n for c in t.body if isinstance(c,ast.ClassDef) and c.name=='Controller' for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='_inputs')
x,y=get(a),get(b);y.body.pop(0);check('legacy inputs AST unchanged',ast.dump(x,include_attributes=False)==ast.dump(y,include_attributes=False))
print(json.dumps({'status':'PASS','checks':checks,'count':len(checks),'scope':'synthetic actual Controller Store stage reader archived Visitor only; no genuine Owner/claim/native'},indent=2))
