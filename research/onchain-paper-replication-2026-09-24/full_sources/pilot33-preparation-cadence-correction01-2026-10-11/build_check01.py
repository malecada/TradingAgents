"""Bounded source candidate plus synthetic full-_prepare fixture; no real authority."""
import ast,copy,difflib,hashlib,json,resource,signal,types,builtins
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(268435456,268435456));resource.setrlimit(resource.RLIMIT_CPU,(20,20));resource.setrlimit(resource.RLIMIT_FSIZE,(4194304,4194304));signal.alarm(40)
H=Path(__file__).resolve().parent;R=H.parents[3];P=R/'tradingagents/research/onchain_replication';checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def ck(v,n):
 assert v,n
 checks.append(n)
old=(P/'compact_mcm.py').read_text();ck(sha(old.encode())=='becaab002648c440852553ebf1e662702affee96283a07bcb90bdfc2ca7379ca','exact preserved failed33 predecessor')
additions=[('    sources = dictionary._prepare_sources() if imported else _sources(dictionary)\n','    if imported:dictionary.check()  # Complete source-read segment before graph preparation.\n'),('    run = owner.bound._run; bound = owner.bound.record\n','    if imported:dictionary.check()  # Complete graph/scope segment before policy reads.\n'),("    kernel = _kernel(dictionary); kernel.validate_policy(policy['numeric'],pairs)\n",'    if imported:dictionary.check()  # Complete policy/kernel segment before output metadata.\n')]
new=old
for anchor,line in additions:
 ck(new.count(anchor)==1,'unique phase seam '+anchor.strip());new=new.replace(anchor,anchor+line) if 'run = ' not in anchor else new.replace(anchor,line+anchor)
back=new
for _,line in additions:back=back.replace(line,'',1)
ck(back==old,'exact whole-file literal inverse only three checks');ck(ast.dump(ast.parse(back))==ast.dump(ast.parse(old)),'full AST inverse')
(H/'compact_mcm.py').write_text(new)
for name,a,b,pa,pb in [('forward.patch',old,new,str((P/'compact_mcm.py').relative_to(R)),str((H/'compact_mcm.py').relative_to(R))),('inverse.patch',new,old,str((H/'compact_mcm.py').relative_to(R)),str((P/'compact_mcm.py').relative_to(R)))]:
 (H/name).write_text(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=pa,tofile=pb)))
interval=(P/'imported_authority_interval.py').read_bytes();ck(sha(interval)=='e61ef97f883ed9d27107f6316b774697b8949d83c313928150a0ae717b283f6f','unchanged actual Interval source');iv={};exec(compile(interval,'actual stdlib Interval','exec'),iv)
policy_clock={'schema_version':1,'kind':iv['KIND'],'live_interval_ms':1000,'fingerprint_interval_ms':2000,'full_interval_ms':30000,'max_stale_ms':60000,'max_calls_between_full':100000,'assumption':iv['ASSUMPTION']}
AGE=51.80366844699893;COST=11.354144623001048
# Four synthetic phase durations sum to actual aggregate age; NOT observed phase timings.
DEFAULT=(12.,10.,18.,AGE-40.)
def run(text,imported=True,durations=DEFAULT,check_failure=None,mutate_final=False,cost=COST):
 events=[];clock=[0.];interval=iv['Interval'](policy_clock,clock=lambda:clock[0]);count=[0];ns=types.SimpleNamespace
 def require(ok,why):
  if not ok:raise ValueError(why)
 def delay(n,label):clock[0]+=n;events.append(label)
 matching={'x':1};scope={'graph':'g','dictionary':'dict','workflow':'scope'};graph=ns(node_ids=['a','b']);dictionary_data=ns(representatives=['m'],identity='dict',matching_config_hash='matching')
 descriptor={'representation_jobs':{'rep':{'plan_input':'plan','producer':'producer','compact_mcm_input':'mcm'}}};plan={'producers':{'producer':{'compact_mcm_input':'mcm'}}};policy={'schema_version':1,'max_entries':100,'max_workflow_metadata_bytes':1000,'numeric':{}}
 docs={'execution_job':{'payload':descriptor},'plan':plan,'mcm':policy}
 def read_input(name):delay(durations[2]/3,'read:'+name);return json.dumps(docs[name])
 runobj=ns(read_input=read_input,admission=ns(inputs={'mcm':{'sha256':'policy'},'output':{'sha256':'out'}},root=H/'synthetic-no-output'))
 bound=ns(_run=runobj,record={'workflow_identity':'workflow','representation':'rep','producer':'producer','experiment':'synthetic'})
 owner=ns(bound=bound,matching=matching,policy={},required=['mcm-g'],reserved=0,maximum=1000,active=None,stages={},root=H/'synthetic-no-stage',identity='owner')
 dictionary=ns(dictionary=dictionary_data,owner=owner,graph=graph,key='g',receipt_sha256='receipt',scope=scope)
 def derive():delay(durations[1],'derive');return dict(scope)
 # Derivation occurs again after final callback; charge only initial preparation traversal.
 derived=[False]
 def derive_once():
  if not derived[0]:derived[0]=True;return derive()
  return dict(scope)
 dictionary.derive_scope=derive_once;dictionary._pins=lambda:events.append('pins')
 def sources():delay(durations[0],'sources');return {'source':'0'*64}
 dictionary._prepare_sources=sources;dictionary._prepare_graph=lambda key:graph
 def check():
  count[0]+=1;ordinal=count[0];events.append('check:'+str(ordinal))
  def full():
   delay(cost,'full:'+str(ordinal))
   if check_failure and ordinal==check_failure[0]:raise check_failure[1]
   # Candidate final callback is fifth, predecessor final callback second.
   final_ordinal=5 if text==new and imported else 2
   if mutate_final and ordinal==final_ordinal:graph.node_ids.append('changed')
  interval.validate(full,lambda:events.append('finger'),lambda:events.append('live'),boundary=True)
 dictionary.check=check
 kernel=ns(validate_policy=lambda p,n:events.append('kernel-policy'))
 def output_policy(*args):delay(durations[3],'output-policy');return {},0
 batch=ns(selected=lambda p:False,validate=lambda *a:None)
 def importer(name,globals=None,locals=None,fromlist=(),level=0):
  assert level==1 and fromlist==('compact_mcm_batched',),(name,fromlist,level)
  return ns(compact_mcm_batched=batch)
 env={'__builtins__':dict(vars(builtins),__import__=importer),'json':json,'_imported':lambda d:imported,'_sources':lambda d:sources(),'_owner':lambda d:owner,'_graph':lambda d,k:graph,'thaw':copy.deepcopy,'graph_identity':lambda g:g,'node_order_hash':lambda ids:'order','cache_key':lambda v:sha(json.dumps(v,sort_keys=True).encode()),'BACKEND':'b','require':require,'_kernel':lambda d:kernel,'publication':ns(_output_policy=output_policy),'compact_policy':ns(validate=lambda *a,**k:{'logical_reservation_bytes':1}),'compact_owner':ns(STAGE_BYTES=1,present=lambda p:False),'io':ns(META_LIMIT=1,_json=lambda v:json.dumps(v)),'_source_evidence':lambda d,s:s}
 fn=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='_prepare');exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual extracted _prepare synthetic dependencies','exec'),env)
 try:result=env['_prepare'](dictionary,'g','mcm','output');return {'result':result[2:],'error':None,'events':events,'count':count[0],'closed':interval.closed,'full':interval.full,'time':clock[0]}
 except BaseException as e:return {'result':None,'error':e,'events':events,'count':count[0],'closed':interval.closed,'full':interval.full,'time':clock[0]}
a=run(old);ck(isinstance(a['error'],ValueError) and 'stale interval cannot refresh' in str(a['error']),'RED original actual aggregate63.157813069999975s reproduced')
ck(a['count']==2 and a['closed'] and abs((a['time']-a['full'])-(AGE+COST))<1e-10,'RED final second callback poisons without timestamp refresh')
b=run(new);ck(b['error'] is None and b['count']==5 and not b['closed'],'GREEN segmented actual candidate runs all entry/mid/final checks')
ck([e for e in b['events'] if e.startswith('check:')]==['check:1','check:2','check:3','check:4','check:5'],'exact real candidate check cadence')
# Original and new full function both legacy-route execution match exactly.
x=run(old,False);y=run(new,False);ck(x==y and x['error'] is None and x['count']==1,'nonimported full function result/events unchanged')
for ordinal in (2,3,4,5):
 error=KeyboardInterrupt('synthetic fatal '+str(ordinal));v=run(new,check_failure=(ordinal,error));ck(v['error'] is error and v['closed'] and v['count']==ordinal,'fatal identity and poison at check '+str(ordinal))
v=run(new,check_failure=(3,ValueError('synthetic current source changed')));ck(str(v['error'])=='synthetic current source changed' and v['closed'] and v['count']==3,'genuine check seam propagates currentness refusal')
v=run(new,mutate_final=True);ck(str(v['error'])=='imported preparation dimensions/scope changed','final callback dimension mutation still rejected by actual original rejoin')
for phase in range(4):
 d=list(DEFAULT);d[phase]=50.;v=run(new,durations=tuple(d));ck(v['error'] is not None and 'stale interval cannot refresh' in str(v['error']) and v['closed'],'long indivisible phase refuses '+str(phase))
v=run(new,cost=61.);ck(v['error'] is not None and v['closed'] and v['count']==1,'single full callback over60 still refuses')
result={'classification':'SOURCE_AND_EXTRACTED_FULL_PREPARE_SYNTHETIC_DEPENDENCIES_ONLY','checks':checks,'predecessor_sha256':sha(old.encode()),'candidate_sha256':sha(new.encode()),'actual_interval_source_sha256':sha(interval),'observed_aggregate_age':AGE,'observed_full_callback_cost':COST,'observed_total':AGE+COST,'synthetic_segment_durations_not_measured':DEFAULT,'actual_speed_or_success':None,'added_imported_checks':3,'unchanged_legacy_route':True,'scope':'No real Target/Owner/Binding/claim or scientific imports; exact _prepare function under plain stdlib scalar stubs and real unchanged Interval.'}
(H/'RESULT01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result))
