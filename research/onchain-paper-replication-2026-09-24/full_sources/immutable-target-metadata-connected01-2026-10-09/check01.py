import os,resource,signal,json,sys,time,ast,types,copy,statistics
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[3];S=R/'tradingagents/research/onchain_replication'
os.sched_setaffinity(0,{3});os.nice(10)
for r,v in [(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_FSIZE,4*1024**2),(resource.RLIMIT_CPU,30)]:resource.setrlimit(r,(v,v))
signal.setitimer(signal.ITIMER_REAL,30)
limits={'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'as':resource.getrlimit(resource.RLIMIT_AS),'fsize':resource.getrlimit(resource.RLIMIT_FSIZE),'cpu':resource.getrlimit(resource.RLIMIT_CPU),'wall':signal.getitimer(signal.ITIMER_REAL)}
assert limits['affinity']==[3] and limits['nice']==10 and limits['as']==(536870912,)*2 and limits['fsize']==(4194304,)*2
(D/'LIMITER01.json').write_text(json.dumps(limits,indent=2)+'\n');started=time.perf_counter()
# Actual canonical implementation only, stdlib; no research runtime import.
t=ast.parse((S/'provenance.py').read_text());n={'json':json};exec(compile(ast.Module(body=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name in ('canonical_bytes','thaw')],type_ignores=[]),'actual_canonical','exec'),n);canonical=n['canonical_bytes']
t=ast.parse((D/'immutable_target_metadata.py').read_text());t.body=[x for x in t.body if not isinstance(x,ast.ImportFrom) or not x.level];ns={'canonical_bytes':canonical};exec(compile(t,'actual_snapshot','exec'),ns);helper=types.SimpleNamespace(**ns)
changes=json.loads((D/'CHANGES01.json').read_text())
for name,edits in changes.items():
 text=(D/name).read_text()
 for old,new in reversed(edits):assert text.count(new)==1;text=text.replace(new,old)
 assert text==(S/name).read_text();assert ast.dump(ast.parse(text))==ast.dump(ast.parse((S/name).read_text()))
checks=['three modules literal/AST inverse']
def extract(path):
 cl=next(x for x in ast.parse(path.read_text()).body if isinstance(x,ast.ClassDef) and x.name=='Target');methods=[x for x in cl.body if isinstance(x,ast.FunctionDef) and x.name in ('_arrays','_pins')];cl.body=methods;n={'require':helper.require,'canonical_bytes':canonical,'immutable_target_metadata':helper};exec(compile(ast.Module(body=[cl],type_ignores=[]),'actual_Target_pins','exec'),n);return n['Target']
Old=extract(S/'imported_mcm_identity.py');New=extract(D/'imported_mcm_identity.py')
value={'execution_identity':'a'*64,'current':{'fields':{f'k{i:03d}':'v'*64 for i in range(48)},'arrays':[{'shape':[16,4],'dtype':'float64','sha256':'b'*64} for _ in range(8)]},'original':{'ordered_motifs':['c'*64]*4},'financial_representation_admitted':False}

def target(cls,selected):
 x=cls();x.graph=types.SimpleNamespace(**{k:object() for k in ('node_ids','node_features','edge_index','edge_features','edge_aggregates')});x.owner=object();x.dictionary=object();x.key='key';x.receipt_sha256='r';mapping={'key':'manifest'};x.execution=types.SimpleNamespace(_owner=x.owner,_materialized=types.SimpleNamespace(_dictionary=x.dictionary),_stage=types.SimpleNamespace(reference='r',prepared=types.SimpleNamespace(_selection={'selected':{'descriptor':{'resource_graph_inputs':mapping}}})))
 x._objects=(id(x.execution),id(x.graph),id(x.owner),id(x.dictionary),x._arrays());x._input='manifest';x._mapping=canonical(mapping);x.scope={'workflow':'f'*64};x._scope_pin=canonical(x.scope);x._execution=copy.deepcopy(value);x._execution_pin=canonical(x._execution);x._immutable_execution=x._immutable_execution_pin=selected
 alias=x._execution
 if selected:x._execution_anchor=helper.snapshot(alias);x._execution_anchor_pin=x._execution_anchor;x._execution,x._execution_pin=x._execution_anchor
 return x,alias
for selected in (False,True):
 x,alias=target(New,selected);x._pins();assert canonical(x._execution)==canonical(alias)
 if selected:
  alias['current']['arrays'][0]['shape'][0]=999;x._pins();assert x._execution['current']['arrays'][0]['shape'][0]==16
  try:x._execution['current']['fields']['k000']='change'
  except TypeError:pass
  else:raise AssertionError('mutable frozen tree')
 else:
  alias['current']['fields']['k000']='change'
  try:x._pins()
  except ValueError:pass
  else:raise AssertionError('legacy alias mutation missed')
checks.append('no mutable caller alias; original alias mutation cannot change frozen snapshot; legacy mutation refuses')
for field,replace in [('field',lambda x:setattr(x,'_execution',dict(x._execution))),('anchor',lambda x:setattr(x,'_execution_anchor',tuple(list(x._execution_anchor)))),('pin',lambda x:setattr(x,'_execution_pin',bytes(bytearray(x._execution_pin)))),('selection',lambda x:setattr(x,'_immutable_execution',False)),('mapping',lambda x:x.execution._stage.prepared._selection['selected']['descriptor']['resource_graph_inputs'].update(key='other')),('scope',lambda x:x.scope.update(workflow='other')),('chain',lambda x:setattr(x.execution,'_owner',object())),('arrays',lambda x:setattr(x.graph,'node_ids',object()))]:
 x,_=target(New,True);replace(x)
 try:x._pins()
 except ValueError:pass
 else:raise AssertionError(field+' mutation missed')
checks.append('field/anchor/byte-pin/selection/mutable mapping/scope/authority-chain/array identity replacements refuse')
# Exact helper-supported JSON and refusals.
for v in ({'x':float('nan')},{'x':2**63},{'x':(1,2)},{1:'x'},{'x':'a'*65537},{'x':[0]*8192}):
 try:helper.snapshot(v)
 except ValueError:pass
 else:raise AssertionError('unsupported accepted')
deep=0
for _ in range(26):deep=[deep]
try:helper.snapshot(deep)
except ValueError:pass
else:raise AssertionError('depth accepted')
for p in (None,False):assert helper.selected(p) is False
assert helper.selected(dict(helper.POLICY)) is True
try:helper.selected(True)
except ValueError:pass
else:raise AssertionError('nonpolicy true accepted')
checks.append('exact JSON types, finite values and selected bytes/nodes/depth policy bounds')
# Actual unchanged lease check method: no authority fabricated; scheduler doubles.
lt=ast.parse((S/'imported_authority_lease.py').read_text());cl=next(x for x in lt.body if isinstance(x,ast.ClassDef) and x.name=='Lease');check=next(x for x in cl.body if isinstance(x,ast.FunctionDef) and x.name=='check');check.body=[x for x in check.body if not isinstance(x,ast.ImportFrom)];ln={'require':helper.require};exec(compile(ast.Module(body=[check],type_ignores=[]),'actual_lease_check','exec'),ln)
x,_=target(New,True);trace=[];clock_error=RuntimeError('synthetic scheduler clock replaced')
def validate(*args,**kwargs):trace.append('scheduler');raise clock_error
lease=types.SimpleNamespace(_identity=lambda:trace.append('identity'),target=x,value=b'value',_full=lambda:None,_finger=lambda:None,_live=lambda:None,scheduler=types.SimpleNamespace(validate=validate,closed=False),closed=False)
try:ln['check'](lease)
except RuntimeError as error:assert error is clock_error
else:raise AssertionError('clock failure lost')
assert trace==['identity','scheduler'] and lease.closed and lease.scheduler.closed
checks.append('unchanged actual lease scheduler failure/clock seam preserves primary and closes lease; metadata-only doubles')
# Actual same-boundary checked-value decoder makes a fresh JSON tree.
node=next(z for z in lt.body if isinstance(z,ast.FunctionDef) and z.name=='_checked_value');node.body=[z for z in node.body if not isinstance(z,ast.ImportFrom)]
ns={'require':helper.require,'canonical_bytes':canonical,'json':json};exec(compile(ast.Module(body=[node],type_ignores=[]),'actual_checked_value','exec'),ns)
current={'live':[1]};original={'original':[2]};body=canonical({'current':current,'original':original});pin=canonical(current)
fresh=ns['_checked_value'](body,body,current,pin,original);frozen=helper.snapshot(fresh)
current['live'][0]=999
try:ns['_checked_value'](body,body,current,pin,original)
except ValueError:pass
else:raise AssertionError('mutable live root revocation lost')
assert frozen[0]['current']['live'][0]==1
checks.append('actual checked-value fresh tree; mutable execution root rejoin refuses after mutation')
ct=ast.parse((D/'real_pilot_import_caller.py').read_text());fun=next(z for z in ct.body if isinstance(z,ast.FunctionDef) and z.name=='validate_plan')
ns={'require':helper.require,'immutable_target_metadata':helper,'KIND':'real-data-import-training-pilot-v1','FILE_MAX':4*1024**2,'Path':Path,'_finite_resources':lambda p:None}
exec(compile(ast.Module(body=[fun],type_ignores=[]),'actual_validate_plan','exec'),ns)
plan=json.loads((R/'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full29-input-draft01-2026-10-09/public01/pilot.json').read_bytes())
for option in ('absent',None,False,dict(helper.POLICY)):
 q=copy.deepcopy(plan)
 if option!='absent':q['immutable_target_execution']=option
 assert ns['validate_plan'](q) is q
q=copy.deepcopy(plan);q['immutable_target_execution']=dict(helper.POLICY);del q['imported_authority_lease_input']
try:ns['validate_plan'](q)
except ValueError:pass
else:raise AssertionError('unsampled selected plan accepted')
q=copy.deepcopy(plan);q['immutable_target_execution']=dict(helper.POLICY,max_nodes=8193)
try:ns['validate_plan'](q)
except ValueError:pass
else:raise AssertionError('noncanonical selection accepted')
# Check all three concrete Target/production callsites forward the exact plan value.
calls=[z for z in ast.walk(ct) if isinstance(z,ast.Call) and ((isinstance(z.func,ast.Name) and z.func.id=='Target') or (isinstance(z.func,ast.Attribute) and z.func.attr=='produce_imported'))]
assert len(calls)==3 and all(any(k.arg is None and 'immutable_execution' in ast.unparse(k.value) and "p['immutable_target_execution']" in ast.unparse(k.value) for k in z.keywords) for z in calls)
checks.append('actual plan validator/defaults/refusals; three actual forwarding callsites; resource validator stubbed, no authority instantiated')
# Deterministic repeated actual _pins, includes unchanged mapping/scope checks.
old,_=target(Old,False);new,_=target(New,True);raw=[];iterations=2048
for repeat in range(4):
 row={}
 for label,obj in ([('old',old),('selected',new)] if repeat%2==0 else [('selected',new),('old',old)]):
  begin=time.perf_counter_ns()
  for _ in range(iterations):obj._pins()
  row[label]=time.perf_counter_ns()-begin
 raw.append(row)
out={'status':'PASS_STDLIB_SYNTHETIC_NO_AUTHORITY','checks':checks,'fixture_canonical_bytes':len(canonical(value)),'timing_iterations_per_repetition':iterations,'timing_raw_ns':raw,'median_old_ns':statistics.median(x['old'] for x in raw),'median_selected_ns':statistics.median(x['selected'] for x in raw),'limits':limits,'elapsed_seconds':time.perf_counter()-started,'qualification':'Exact _pins source, fixed synthetic JSON. No actual causal lease share or real speed inferred. Actual original full boundaries/source/clock code unchanged.'}
(D/'RESULT01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
