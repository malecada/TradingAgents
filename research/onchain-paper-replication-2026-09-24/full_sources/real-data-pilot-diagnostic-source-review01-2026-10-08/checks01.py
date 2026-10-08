"""Independent diagnostic seam checks; only tiny synthetic matcher execution."""
import ast,hashlib,importlib.util,json,sys,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from tradingagents.research.onchain_replication.contracts import AttributedGraph
from tradingagents.research.onchain_replication.compact_pair_log import PairLog
from tradingagents.research.onchain_replication.matching_reference import match_reference
from tradingagents.research.onchain_replication.matching_identity import graph_identity
from tradingagents.research.onchain_replication import resource_fixture
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];C=HERE.parent/'real-data-pilot-diagnostic-composition01-2026-10-08';MAIN=ROOT/'tradingagents/research/onchain_replication'
PREFIX='tradingagents.research.onchain_replication.'
checks=[];refusals=[]
def check(name,value):
 if not value:raise AssertionError(name)
 checks.append(name)
def refuse(name,call,exception=ValueError):
 try:call()
 except exception as error:refusals.append({'case':name,'exception':type(error).__name__,'message':str(error)});return error
 raise AssertionError(name+' accepted')
def load(name):
 spec=importlib.util.spec_from_file_location(PREFIX+'_independent_'+name,C/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
telemetry=load('real_pilot_partial_progress');matcher=load('compact_matcher');caller=load('real_pilot_import_caller')
for name,sha in [('COMPOSITION02.json','a5eee4dd6b215174f146cb9e952984090043f414674e1761cfdfb45b3d9fffd7'),('COMPOSITION03.json','b7a6de374afe611a41ba73af0d84082262b61f9753ae8662555929f84b5e25e2')]:
 check(name+' exact',hashlib.sha256((C/name).read_bytes()).hexdigest()==sha)
composition=json.loads((C/'COMPOSITION03.json').read_text());previous=json.loads((C/'COMPOSITION02.json').read_text())
check('source roster unchanged02to03',composition['files']==previous['files'])
reviewed=['compact_matcher.py','compact_mcm.py','real_pilot_import_caller.py','real_pilot_partial_progress.py']
for name in reviewed:
 pin=composition['files'][name]
 check(name+' current candidate',hashlib.sha256((C/name).read_bytes()).hexdigest()==pin['candidate']['sha256'])
 check(name+' current Main baseline',hashlib.sha256((MAIN/name).read_bytes()).hexdigest()==pin['main_before_sha256'])
with patch.dict(sys.modules,{PREFIX+'real_pilot_partial_progress':telemetry}):
 old=json.loads((C/'pilot_draft01.json').read_text())
 refuse('actual unfilled01 plan',lambda:caller.validate_plan(old))
 plan=json.loads((C/'pilot_draft02.json').read_text());check('actual filled02 schema',caller.validate_plan(plan)==plan)
 refuse('missing fifth output',lambda:caller.validate_plan(plan|{'outputs':{k:v for k,v in plan['outputs'].items() if k!='diagnostic'}}))
 refuse('duplicated fifth output',lambda:caller.validate_plan(plan|{'outputs':plan['outputs']|{'diagnostic':plan['outputs']['summary']}}))
 refuse('1025 cap',lambda:caller.validate_plan(plan|{'scoring_diagnostic':plan['scoring_diagnostic']|{'max_completed_pairs':1025}}))
 baseline=json.loads((HERE.parent/'real-data-pilot-final19-2026-10-08/PREPARATION_RESULT01.json').read_text())['builder03_result']['inputs']['pilot']
 check('original population membership unchanged',all(plan[k]==baseline[k] for k in ['graph_inputs','graph_sequences','indices','decisions','seed','batch_size','lookback_days','model_execution']))
 check('exact1024with64checkpoints',plan['scoring_diagnostic']==dict(schema_version=1,max_completed_pairs=1024,checkpoint_every_pairs=64,checkpoint_relative='scoring-diagnostic/progress.json'))
charter=(ROOT/composition['charter']['path']).read_text()
check('charter exact',hashlib.sha256(charter.encode()).hexdigest()==composition['charter']['sha256'])
check('charter dispositions disclosed',all(s in charter for s in ['after1024','every64','permanently FAILED','not a representative estimate']))
# Exact numerical call expressions, unwrapping the timing-only dispatcher.
def engine_calls(path,unwrap):
 tree=ast.parse(path.read_text());result=[]
 for n in ast.walk(tree):
  if isinstance(n,ast.Call):
   if unwrap and isinstance(n.func,ast.Attribute) and n.func.attr=='_timed' and len(n.args)>1:
    n=ast.Call(func=n.args[1],args=n.args[2:],keywords=n.keywords)
   if isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='engine' and n.func.attr in ('create','advance','score_only','close'):
    result.append(ast.dump(n,include_attributes=False))
 return sorted(result)
check('original numerical call expressions unchanged',engine_calls(MAIN/'compact_matcher.py',False)==engine_calls(C/'compact_matcher.py',True))
# Literal caller kernel admission roster must equal Target's selected kernel.
tree=ast.parse((C/'imported_mcm_identity.py').read_text());kernel=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='KERNEL' for t in n.targets))
check('caller kernel literal join',kernel in [n.value for n in ast.walk(ast.parse((C/'real_pilot_import_caller.py').read_text())) if isinstance(n,ast.Constant) and isinstance(n.value,str)])
check('selected kernel reference',kernel==composition['kernel']['path'])
text=(C/'real_pilot_import_caller.py').read_text()
check('roster before actual activate',text.index('            _prepare_lease_modules()')<text.index("            activate(execution,p['imported_authority_lease_input'])"))
roster=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='_prepare_lease_modules')
check('diagnostic module preloaded',any(isinstance(n,ast.ImportFrom) and any(v.name=='real_pilot_partial_progress' for v in n.names) for n in ast.walk(roster)))
check('all five outputs admitted',"set(p['outputs'].values()) <= set(ad.experiment['outputs'])" in text)
# Metadata-only reader compatibility: same optional field and bound helper.
writer=(C/'stage_retention.py').read_text();reader=(C/'stage_retention_reader.py').read_text()
check('selected writer reader policy join',"INPUT_JSON_FIELD='max_selected_input_json_bytes'" in writer and 'retention.selected_input_limit(policy)' in reader and 'retention.selected_input_bound(index,numeric_records)' in reader)
config=dict(alpha=1.,beta0=1.,beta_final=1.,beta_rate=.5,max_iterations=2,max_pair_entries=100,normalization_iterations=1,solver='algorithm1_literal')
a=AttributedGraph(('a','b'),np.array([[0.],[.2]]),np.array([[0],[1]],dtype=np.int64),np.array([[.1]]),'a'*64,'a')
b=AttributedGraph(('c','d'),np.array([[.3],[.6]]),np.array([[1],[0]],dtype=np.int64),np.array([[.4]]),'b'*64,'c')
policy=dict(max_state_bytes=100000,normalization_chunk_entries=4,hardening_chunk_entries=2,hardening_buffer_bytes=4096,max_score_buffer_bytes=4096,chunk_edges=2,max_checkpoint_bytes=400000,max_publications=10,total_checkpoint_bytes=5000000)
schedule=dict(operations_per_call=10000,calls_per_checkpoint=64,max_checkpoints=4,max_total_checkpoints=10,max_total_checkpoint_bytes=6000000)
context=dict(namespace='a'*64,source_commit='b'*40,runtime_hash='c'*64)
selection=plan['scoring_diagnostic']|{'max_completed_pairs':2,'checkpoint_every_pairs':1}
for selected in (None,selection):
 with tempfile.TemporaryDirectory(prefix='diagnostic-independent-') as temporary:
  root=Path(temporary);d=None if selected is None else telemetry.ScoringDiagnostic(selected,root,claim_sha256='d'*64,source='e'*40)
  log=PairLog(root/'pairs',owner='a'*64,scope=matcher.scope(config,context,policy,'f'*64,schedule),limits=dict(chunk_events=16,max_events=100,max_pairs=10,max_logical_bytes=40000),max_iterations=2,lease=lambda:None)
  with patch.dict(sys.modules,{PREFIX+'real_pilot_partial_progress':telemetry}):
   m=matcher.CompactMatcher(log,config=config,context=context,policy=policy,workload_sha256='f'*64,schedule=schedule,lease=lambda:None,diagnostic=d)
  purpose=dict(schema_version=1,kind='mcm',workload_sha256='f'*64,typed_graphs=[graph_identity(a),graph_identity(b)],center_index=0,motif_index=0)
  try:
   if d:d.begin('a'*64,log)
   score=m(purpose,a,b)['score'];check('tiny scalar exact '+str(selected is not None),score==match_reference(a,b,config).score)
   if d:
    refuse('second acknowledgement planned failure',lambda:m(purpose|{'motif_index':1},a,b),telemetry.PlannedScoringStop)
    check('log acknowledged before tail return',log.state['completed_pairs']==2 and log.state['pending'] is None and d.completed==2 and m.poisoned)
    d.observe_tail(log,SimpleNamespace(cells=1,batches=SimpleNamespace(cells=0),active=None))
    row=json.loads((root/'scoring-diagnostic/progress.json').read_text())
    check('tail/log distinction',row['completed_scalar_pairs']==2 and row['tail_observation']['acknowledged_tail_cells']==1 and row['tail_observation']['completed_batch_cells']==0)
    check('finite diagnostics no credits',len((root/'scoring-diagnostic/progress.json').read_bytes())<=8192 and row['full_mcm_complete'] is False and row['representation_credit']==0 and row['paper_financial_fits']==0)
    check('actual scoring timing count',row['phase_timings']['score_only']['calls']==2)
    def fail():raise RuntimeError('original scalar failure')
    with patch.object(d,'_record',side_effect=ValueError('later timing failure')):
     failure=refuse('original failure survives timing error',lambda:d.measure('score_only',fail),RuntimeError)
    check('later timing preserved as note',any('later timing failure' in n for n in failure.__notes__))
   else:check('default no diagnostic artifacts',not (root/'scoring-diagnostic').exists())
  finally:
   if d:log.fail('synthetic diagnostic termination');d.close()
   else:log.close()
with tempfile.TemporaryDirectory(prefix='diagnostic-counter-independent-') as temporary:
 root=Path(temporary);d=telemetry.ScoringDiagnostic(plan['scoring_diagnostic'],root,claim_sha256='a'*64,source='b'*40)
 log=SimpleNamespace(state={'completed_pairs':0,'pending':None})
 try:
  d.begin('a'*64,log)
  for count in range(1,1024):
   log.state['completed_pairs']=count;d.completed_pair(log)
  check('before cap1023 finite checkpoints',d.completed==1023 and d.writes==16 and not d.stopped)
  log.state['completed_pairs']=1024
  refuse('exact1024 terminal stop',lambda:d.completed_pair(log),telemetry.PlannedScoringStop)
  check('cap checkpoint durable bounded',d.writes==17 and not (root/'scoring-diagnostic/progress.tmp').exists() and (root/'scoring-diagnostic/progress.json').stat().st_size<=8192)
  refuse('closed diagnostic cannot continue',lambda:d.completed_pair(log))
 finally:d.close()
result={'status':'SOURCE_ACCEPTED_PLAN03_SCHEMA_ACCEPTED_NOT_RELEASED','checks':checks,'check_count':len(checks),'refusals':refusals,'reviewed_sources':reviewed,'excluded_self_authored':['real_pilot_reservations.py','capacity_selection'],'genuine_Owner_or_entry_admission':False,'numerical_scope':'one tiny synthetic matching pair, default anddiagnostic; no real data or native job'}
print(json.dumps(result,indent=2))
