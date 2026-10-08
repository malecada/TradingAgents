import ast,hashlib,importlib.util,json,sys,tempfile,types
from pathlib import Path
from unittest.mock import patch
import tradingagents.research.onchain_replication as package
from tradingagents.research.onchain_replication import archive_pair_reader
from tradingagents.research.onchain_replication.provenance import thaw
from tests.research.onchain_replication import test_compact_matcher as tiny,test_restart_retention_integration as fixture
H=Path(__file__).resolve().parent;F=H.parent
C=F/'real-data-pilot-selected-input-control-candidate01-2026-10-08';R=F/'real-data-pilot-diagnostic-composition01-2026-10-08'
checks=[]
def ok(name,condition):
 assert condition,name
 checks.append(name)
def refuse(name,fn):
 try:fn()
 except (ValueError,TypeError):checks.append(name);return
 raise AssertionError(name+' accepted')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
ok('frozen author manifest',sha(C/'MANIFEST01.json')=='9941144e8dbabfe67d77eb781497edc9eed679f0311f89df503d72f1a4b1dd29')
manifest=json.loads((C/'MANIFEST01.json').read_bytes());composition=json.loads((R/'COMPOSITION02.json').read_bytes())
for name,row in manifest['sources'].items():
 ok(name+' author body',sha(C/name)==row['sha256'])
 ok(name+' exact Root composition body',sha(R/name)==row['sha256']==composition['files'][name]['candidate']['sha256'])
for name,digest in manifest['evidence'].items():ok('retained evidence '+name,sha(C/name)==digest)
def load(name,file):
 spec=importlib.util.spec_from_file_location('tradingagents.research.onchain_replication.'+name,R/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
stage=load('_review_stage','stage_retention.py');reader=load('_review_reader','stage_retention_reader.py');reader.retention=stage
# Independent standard encoder is the oracle, across every ASCII code plus escape classes.
for cp in list(range(128))+[128,255,2048,0xd800,0xdfff,0xffff,0x10000,0x10ffff]:
 v={'node_ids':['A'+chr(cp)+'Z','\\"\n'],'numeric':123456}
 ok('encoder extent '+str(cp),stage._json_extent(v)==len(json.dumps(v,sort_keys=True,separators=(',',':')).encode()))
base=fixture.retention_policy();selected=base|{stage.INPUT_JSON_FIELD:131072}
for v in [True,0,-1,1.2,2**30,2**30+1]:refuse('invalid finite bound '+str(v),lambda v=v:stage.validate(base|{stage.INPUT_JSON_FIELD:v}))
ok('legacy limit',stage.selected_input_limit(base)==stage.store.CONTROL)
with patch.object(stage.json,'dumps',side_effect=AssertionError('encoded too early')):
 refuse('pre-encoding bound',lambda:stage._selected_raw({'node_ids':['\\"\U00010000'*100]},base|{stage.INPUT_JSON_FIELD:100}))
# Legacy _inputs body is literally the original AST once the opt-in dispatch is removed.
def inputs_ast(path):
 tree=ast.parse(path.read_text());return next(m for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Controller' for m in n.body if isinstance(m,ast.FunctionDef) and m.name=='_inputs')
a=inputs_ast(C/'original_stage_retention.py');b=inputs_ast(R/'stage_retention.py');b.body.pop(0)
ok('legacy inputs AST',ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False))
# One actual tiny sharded Controller→Store→reader→archive Visitor path, not a repeated numerical matrix suite.
orig_graph=tiny.graph
long_id='second'+('"\\\n\U0001f600'*1000)
def graph(*args,**kwargs):
 g=orig_graph(*args,**kwargs)
 return types.SimpleNamespace(node_ids=(g.node_ids[0],long_id),node_features=g.node_features,edge_index=g.edge_index,edge_features=g.edge_features)
with tempfile.TemporaryDirectory(prefix='independent-selected-reader-') as d:
 root=Path(d);p=tiny.POLICY|{'checkpoint_layout':{'format':'sharded-npy-v1','chunk_entries':2}}
 with patch.object(package,'stage_retention',stage),patch.dict(sys.modules,{'tradingagents.research.onchain_replication.stage_retention':stage}),patch.object(tiny,'POLICY',p),patch.object(fixture,'retention_policy',return_value=selected),patch.object(tiny,'graph',graph):
  m,log,a,b,c,purpose,transport=fixture.fixture(root,progress=True,schedule_override={'operations_per_call':1,'calls_per_checkpoint':4,'max_checkpoints':10})
 try:
  m(purpose,a,b);ok('actual pair completion',log.state['completed_pairs']==1)
  ok('selected sharded Store64KiB',stage.store.control_limit(m.policy)==65536)
  ref=m.retention.finish_stage();log.finish();args=dict(policy=selected,selection=thaw(m.retention.selection),expected_sha256=ref,start_sha256=log.start_sha)
  seal=reader.check(root/'checkpoints',**args);ok('complete reader accounting',seal['completed_pairs']==1 and seal['progress_events']>0)
  visitor=reader.Visitor(root/'checkpoints',**args);terminal=root/'log/archive-complete.json'
  archive_pair_reader.verify(root/'log',expected_sha256=sha(terminal),owner=log.start['owner'],scope=log.start['scope'],archive_policy=log.policy,attempt=root/'review-read',transport=transport,lease=lambda:None,max_read_metadata_bytes=1000000,on_event=visitor.visit)
  ok('full actual archived Visitor',visitor.finish()==seal)
  meta=root/'checkpoints/inputs/input-000000000000.json';raw=meta.read_bytes()
  ok('oversized escaped IDs real body',16384<len(raw)<selected[stage.INPUT_JSON_FIELD])
  bound=stage.selected_input_bound(0,stage._input_records((a,b)))
  ok('actual metadata conservatively covered',len(raw)<=bound)
  numeric=sum(getattr(g,n).nbytes+256 for g in (a,b) for n in ('node_features','edge_index','edge_features'))
  reserve=json.loads((root/'checkpoints/reserve-000000000000.json').read_bytes())
  ok('writer exact reserved upper',reserve['delta']['input_bytes']==numeric+bound)
  refuse('changed selected policy',lambda:reader.check(root/'checkpoints',**(args|{'policy':base})))
  meta.write_bytes(raw.replace(b'second',b'changed',1))
  refuse('late changed JSON reader',lambda:reader.check(root/'checkpoints',**args))
  refuse('late changed JSON Visitor',visitor.finish)
  meta.write_bytes(raw)
  ok('restored original full reader',reader.check(root/'checkpoints',**args)==seal)
  stray=root/'checkpoints/inputs/input-foreign.json';stray.write_text('{}\n')
  refuse('foreign input inventory',lambda:reader.check(root/'checkpoints',**args))
 finally:log.close()
print(json.dumps({'status':'PASS','checks':checks,'count':len(checks),'source_only':True,'genuine_scientific_authority':False},indent=2))
