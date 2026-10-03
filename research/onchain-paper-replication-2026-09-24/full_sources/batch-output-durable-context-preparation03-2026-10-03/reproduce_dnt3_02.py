"""Independent source-prefix counterexample; all authority seams synthetic."""
import ast,hashlib,json,os,pathlib,threading,types,importlib.util
H=pathlib.Path(__file__).resolve().parent;P=H.parent/'batch-output-durable-context-preparation02-2026-10-03'
spec=importlib.util.spec_from_file_location('review_correction_helpers',H/'test_corrections02.py');t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
ns=t.load();tree=ast.parse((P/'archive_non_tail.py').read_bytes());ctx=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='Context')
init=next(x for x in ctx.body if isinstance(x,ast.FunctionDef) and x.name=='__init__');cut=next(i for i,x in enumerate(init.body) if isinstance(x,ast.Expr) and isinstance(x.value,ast.Call) and ast.unparse(x.value.func)=='self.root.mkdir');init.body=init.body[:cut];init.name='prefix';ast.fix_missing_locations(init)
root=H/'large-job-synth02';source=root/'tradingagents/research/onchain_replication/archive_non_tail.py';source.parent.mkdir(parents=True);source.write_bytes((P/'archive_non_tail.py').read_bytes());(root/'research_artifacts').mkdir()
policy=dict(schema_version=1,kind='non-tail-durable-population-v1',category='non-tail-original-members',namespace='no-birth',deadline_seconds=60,max_rounded_bytes=1000000,max_commands=64,max_parts=32,max_control_bytes=33554432,part_bytes=128,receipt_output='receipt.json',terminal_output='terminal.json',slots=[dict(graph='a'*64,role='score-batches',max_bytes=10000,max_members=32)])
jobs={};producers={};outputs=['receipt.json','terminal.json']
for i in range(40):
 name='p%02d'%i;selected=dict(operation='produce',plan_input='plan',producer=name,descriptor={'dictionary_origin':'imported-original-v1','required_graphs':['a'*64]},pair_checkpoint_input='pair',non_tail_transport_input='policy');jobs[name]=selected
 producers[name]=selected|dict(binding_output=name+'-binding.json',journal_output=name+'-journal.json');outputs.extend([name+'-binding.json',name+'-journal.json'])
plan=dict(schema_version=2,producers=producers)
execution=dict(schema_version=1,kind='compact_resource',environment_input='environment',payload={'representation_jobs':jobs},resources={'storage_budget':{'root':str(root)}})
class SyntheticRun:
 def __init__(self):
  self.admission=types.SimpleNamespace(root=root,experiment_id='synthetic-not-authority',source='1'*40,inputs={x:{} for x in ('policy','job','plan','pair','environment')},experiment={'outputs':outputs,'source_files':{'tradingagents/research/onchain_replication/archive_non_tail.py':hashlib.sha256(source.read_bytes()).hexdigest()}});self._claim_sha256='2'*64
 def _active(self):pass
 def _check_source(self):pass
 def _check_inputs(self):pass
 def read_input(self,name):return json.dumps(dict(policy=policy,job=execution,plan=plan)[name]).encode()
launch=dict(experiment='synthetic-not-authority',source_commit='1'*40)
ns.update(ResearchRun=SyntheticRun,__file__=str(source),get_ident=threading.get_ident,job=types.SimpleNamespace(PREFIX=pathlib.Path('synthetic')),matching_owner=types.SimpleNamespace(metadata=lambda *a:(launch,'3'*64),_guard=lambda *a:None))
exec(compile(ast.Module(body=[init],type_ignores=[]),'actual-constructor-prebirth-prefix','exec'),ns)
obj=types.SimpleNamespace();run=SyntheticRun();ns['prefix'](obj,run,policy_input='policy',job_input='job');assert not obj.root.exists()
canonical=(json.dumps(execution,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode();assert len(canonical)>8192
# Extract exactly the affected real check() statement, with all prior authority
# checks excluded rather than forged as genuine evidence. No namespace birth.
check=next(x for x in ctx.body if isinstance(x,ast.FunctionDef) and x.name=='check')
line=next(x for x in check.body if isinstance(x,ast.Expr) and 'encode(self.execution)' in ast.unparse(x))
ns['self']=obj
try:exec(compile(ast.Module(body=[line],type_ignores=[]),'actual-check-job-encoding-line','exec'),ns)
except ValueError as e:assert str(e)=='non-tail control metadata cap';print('DNT3 REPRODUCED: constructor prebirth passes complete selected40-producer metadata; unchanged check() later refuses canonical job bytes',len(canonical),'at8KiB; namespace absent',not obj.root.exists())
else:raise AssertionError('expected full-job cap refusal')
# Independently establish exact source-body helper parity with accepted consumer02.
accepted=H.parent/'neural-cold-feature-handoff-held-consumer-wiring-preparation02-2026-10-03/held_score_consumer.py'
baseline=next(x for x in ast.parse(accepted.read_bytes()).body if isinstance(x,ast.FunctionDef) and x.name=='_body')
helper=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='_source_body');helper.name='_body';assert ast.dump(helper)==ast.dump(baseline)
print('CONTROL source bootstrap is AST-identical to accepted bounded owned-FD helper; no numerical imports, actual claims, guard or source activation')
