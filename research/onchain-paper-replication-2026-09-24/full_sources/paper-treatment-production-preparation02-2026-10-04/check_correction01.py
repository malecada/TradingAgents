"""Owned opaque metadata controls. No ResearchRun/Owner/claim creation or arrays."""
import ast,copy,hashlib,json,os,re,sys
from pathlib import Path
from types import SimpleNamespace
from datetime import timedelta
BASE=Path(__file__).resolve().parent
MOD=BASE/'overlay/tradingagents/research/onchain_replication'
checks=[]
def ok(value,label):
 if not value:raise AssertionError(label)
 checks.append(label)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def put(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True);raw=(json.dumps(obj,sort_keys=True,indent=2)+'\n').encode();path.write_bytes(raw);return digest(raw)
class PureImports(ast.NodeTransformer):
 def visit_ImportFrom(self,node):return None if node.level else node
# Bind actual pure contract/admission functions instead of executing package imports.
ns={'Path':Path,'json':json,'digest':digest,'re':re}
exec(compile((MOD/'treatment_contract.py').read_text(),str(MOD/'treatment_contract.py'),'exec'),ns)
admission=ast.parse((BASE/'origins/admission.py').read_text())
exec(compile(ast.Module(body=[n for n in admission.body if isinstance(n,ast.FunctionDef) and n.name in ('identity','local_path')],type_ignores=[]),'actual-admission-extracted','exec'),ns)
names=('_close','_finalize_pending','_retained_bytes','recover_treatment_rows')
tree=ast.parse((MOD/'treatment_production.py').read_text())
body=[PureImports().visit(copy.deepcopy(n)) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
exec(compile(ast.fix_missing_locations(ast.Module(body=body,type_ignores=[])),'actual-successor-extracted','exec'),ns)
oldtree=ast.parse((BASE/'baseline-treatment_production01.py').read_text())
oldns={}
exec(compile(ast.Module(body=[n for n in oldtree.body if isinstance(n,ast.FunctionDef) and n.name=='_close'],type_ignores=[]),'actual-old-close','exec'),oldns)
oldprod=next(n for n in oldtree.body if isinstance(n,ast.FunctionDef) and n.name=='produce_registered_treatments')
oldfinal=next(n for n in oldprod.body if isinstance(n,ast.Try)).finalbody
# RED actual old pending loop: first failure prevents later row attempts.
attempts=[];summaries=[];primary=KeyboardInterrupt('opaque primary')
def broken(row):attempts.append(row['id']);raise OSError('opaque writer')
red={'p':{'asset':'ETH','expected_weeks':['w0','w1','w2']},'ids':['c0','c1','c2'],'rows':{},'record':broken,'primary':primary,'_close':oldns['_close'],'_immutable':lambda *a: summaries.append(1),'directory':Path('opaque'),'graphs':{}}
try:exec(compile(ast.Module(body=oldfinal,type_ignores=[]),'actual-old-finally','exec'),red)
except BaseException as error:ok(error is primary,'RED old primary fatal retained')
ok(attempts==['c0'],'RED old pending skips two later cells')
# _close matrix with every fatal position and independent callbacks.
classes=(OSError,ValueError,MemoryError,KeyboardInterrupt,SystemExit)
fatal=lambda e:isinstance(e,MemoryError) or not isinstance(e,Exception)
for pcls in (None,)+classes:
 for acls in classes:
  for bcls in classes:
   errors=([pcls('primary')] if pcls else [])+[acls('first'),bcls('second')]
   primary=errors[0] if pcls else None;first,second=errors[-2:];calls=[]
   def one():calls.append(1);raise first
   def two():calls.append(2);raise second
   expected=next((e for e in errors if fatal(e)),errors[0])
   try:ns['_close']((one,two,lambda:calls.append(3)),primary)
   except BaseException as error:
    ok(error is expected,'first fatal/ordinary identity matrix')
    ok(set(id(e) for e in error.__cause__.exceptions)==set(id(e) for e in errors if e is not expected),'secondary actual error objects retained')
   else:raise AssertionError('errors swallowed')
   ok(calls==[1,2,3],'all cleanup callbacks attempted matrix')
# Every missing-row writer index, primary/failure types, summary and audit independent.
ids=['durable','c0','c1','c2'];p={'asset':'ETH','expected_weeks':['old','w0','w1','w2']}
for index in range(3):
 for pcls in (None,)+classes:
  for wcls in classes:
   durable={'id':'durable','status':'complete','opaque':'retained'};rows={'durable':durable};attempts=[];summary=[];audits=[]
   primary=None if pcls is None else pcls('primary');failure=wcls('writer')
   def record(row):
    attempts.append(row['id'])
    if row['id']=='c'+str(index):raise failure
    rows[row['id']]=row
   def summarize():summary.append(1);raise ValueError('incomplete summary')
   try:ns['_finalize_pending'](p,ids,rows,record,summarize,audits.append,primary)
   except BaseException as error:
    expected=primary if primary is not None else failure
    if fatal(failure) and not fatal(expected):expected=failure
    ok(error is expected,'pending earliest fatal identity')
   else:raise AssertionError('missing failure')
   ok(attempts==ids[1:] and summary==[1] and len(audits)==1,'GREEN all pending and final summary/audit attempted')
   audit=audits[0];ok(audit['unconfirmed_row_cells']==['c'+str(index)] and audit['attempted_pending_count']==3,'exact missing cells and attempted count')
   ok([e['phase'] for e in audit['publication_errors']]==['pending_row','summary'],'writer/summary failures exposed')
   ok(rows['durable'] is durable and len(rows)==3,'durable cell retained; failed unavailable write not fabricated')
# Simultaneous failures at all indexes, audit failure, no errors and empty pending.
for pcls in (None,)+classes:
 primary=None if pcls is None else pcls('primary');calls=[];summary=[];failure=MemoryError('audit');rows={'durable':{'id':'durable'}}
 def record(row):calls.append(row['id']);raise OSError(row['id'])
 def audit(value):summary.append(value);raise failure
 try:ns['_finalize_pending'](p,ids,rows,record,lambda:None,audit,primary)
 except BaseException as error:ok(error is (primary if primary is not None and fatal(primary) else failure),'audit fatal precedence')
 ok(calls==ids[1:] and summary[0]['unconfirmed_row_cells']==ids[1:],'all failed indices retained')
rows={};audits=[]
ns['_finalize_pending']({'asset':'ETH','expected_weeks':['w']},['c'],rows,lambda row:rows.update({row['id']:row}),lambda:None,audits.append,None)
ok(rows['c']['status']=='unavailable' and audits[0]['unconfirmed_row_cells']==[],'successful unavailable row confirmed')
# Tiny owned metadata namespace: hashes are opaque, not real claims or graph data.
root=BASE/'opaque-recovery01';root.mkdir(exist_ok=False)
source_dir=root/'source';source_dir.mkdir();source_files={}
for name in ('treatment_contract.py','treatment_production.py'):
 raw=(MOD/name).read_bytes();(source_dir/name).write_bytes(raw);source_files['source/'+name]=digest(raw)
ns['__file__']=str(source_dir/'treatment_production.py')
week='2020-01-06T00:00:00Z';end='2020-01-13T00:00:00Z'
parent={k:'opaque_'+k for k in ('manifest_input','coverage_input','claim_input','terminal_input','ledger_input')};parent['components']={'node_ids.npy':'opaque_component'}
plan={'schema_version':1,'kind':'paper-graph-treatment-v1','asset':'ETH','variant':'whale','coverage':[[week,end]],'expected_weeks':[week],'parents':{week:parent},'cohort_input':None,'cohort_review_input':None}
cell=ns['schema'](plan)[0];inputs={};planhash=put(root/'inputs/plan.json',plan);inputs['plan']={'path':'inputs/plan.json','sha256':planhash}
job={'kind':'treatments','payload':{'plan_input':'plan'}};inputs['execution_job']={'path':'inputs/job.json','sha256':put(root/'inputs/job.json',job)}
for role in parent.values():
 if isinstance(role,str):inputs[role]={'path':'unread-opaque-'+role,'sha256':digest(role.encode())}
experiment='opaque-utility-only';source='1'*40;claimhash='2'*64
args=(root,experiment,source,claimhash,[cell],inputs,source_files)
directory=root/'research_artifacts/onchain-paper-replication-2026-09-24/treatments'/experiment
ok(ns['recover_treatment_rows'](*args)=={},'absent namespace remains unavailable')
directory.mkdir(parents=True)
ok(ns['recover_treatment_rows'](*args)=={},'empty pre-intent namespace returns no rows')
intent={'plan_sha256':planhash,'claim_sha256':claimhash,'source':source,'cells':[cell],'financial_credit':0};put(directory/'intent.json',intent)
row={'id':cell,'status':'unavailable','asset':'ETH','week':week,'reason':'opaque unavailable'};rowpath=directory/(cell+'.json');put(rowpath,row)
ok(ns['recover_treatment_rows'](*args)=={cell:row},'durable unavailable retained')
output=directory/cell/'manifest.json';manifest={'opaque_utility':'no arrays or scientific authority'};mhash=put(output,manifest)
receipt={'schema_version':1,'kind':'registered-graph-treatment-receipt','asset':'ETH','variant':'whale','week':week,'end_utc':end,'claim_sha256':claimhash,'source':source,'plan_sha256':planhash,'manifest_sha256':mhash,'cohort_sha256':None,'cohort_review_sha256':None}
for field,key in (('parent_manifest_sha256','manifest_input'),('parent_coverage_sha256','coverage_input'),('parent_claim_sha256','claim_input'),('parent_terminal_sha256','terminal_input'),('parent_ledger_sha256','ledger_input')):receipt[field]=inputs[parent[key]]['sha256']
coverage={'asset':'ETH','week':week,'end_utc':end,'claim_sha256':claimhash,'plan_sha256':planhash,'graph_manifest_sha256':mhash}
row={'id':cell,'status':'complete','asset':'ETH','week':week,'manifest_path':str(output.relative_to(root)),'manifest_sha256':mhash,'treatment_receipt_sha256':put(output.parent/'treatment.json',receipt),'coverage_sha256':put(output.parent/'coverage.json',coverage)};put(rowpath,row)
recovered=ns['recover_treatment_rows'](*args);ok(recovered=={cell:row},'GREEN metadata-complete row retained')
# Actual old reconciliation's searched namespaces cannot see treatments.
oldjob=ast.parse((BASE/'baseline-overlay-job01.py').read_text());newjob=ast.parse((MOD/'job.py').read_text())
oldrec=next(n for n in oldjob.body if isinstance(n,ast.FunctionDef) and n.name=='_reconcile');newrec=next(n for n in newjob.body if isinstance(n,ast.FunctionDef) and n.name=='_reconcile')
ok(not any(isinstance(n,ast.Constant) and n.value=='treatments' for n in ast.walk(oldrec)),'RED original observer has no treatment route')
start=next(i for i,n in enumerate(newrec.body) if isinstance(n,ast.ImportFrom) and n.module=='treatment_production')
block=newrec.body[start+1:start+5]
# Opaque claim-shaped mapping here is solely function argument plumbing; no lifecycle file/object.
namespace={'root':root,'args':SimpleNamespace(experiment=experiment,source=source),'claim_path':None,'file_hash':lambda _:claimhash,'claim':{'inputs':inputs,'experiment':{'cells':[cell],'source_files':source_files,'inputs':{'deliberately_unresolved':'must not use'}}},'recorded':{},'recover_treatment_rows':ns['recover_treatment_rows']}
exec(compile(ast.Module(body=block,type_ignores=[]),'actual-observer-treatment-block','exec'),namespace)
ok(namespace['recorded']=={cell:row},'GREEN actual observer block uses resolved inputs and retains durable row')
# Independent source-level write contract: no replacement durable row operation in observer helper.
ok(not any(isinstance(n,ast.Attribute) and n.attr in ('write_bytes','write_text','unlink','replace') for n in ast.walk(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='recover_treatment_rows'))),'recovery helper read only')
def refuse(label,fn):
 try:fn()
 except (ValueError,KeyError,FileNotFoundError):checks.append(label);return
 raise AssertionError('accepted mutation '+label)
for field in intent:
 bad=copy.deepcopy(intent);bad[field]='wrong';put(directory/'intent.json',bad);refuse('intent '+field,lambda:ns['recover_treatment_rows'](*args))
put(directory/'intent.json',intent)
for field in receipt:
 bad=copy.deepcopy(receipt);bad[field]='wrong';changed=copy.deepcopy(row);changed['treatment_receipt_sha256']=put(output.parent/'treatment.json',bad);put(rowpath,changed);refuse('receipt '+field,lambda:ns['recover_treatment_rows'](*args))
put(output.parent/'treatment.json',receipt);put(rowpath,row)
for field in coverage:
 bad=copy.deepcopy(coverage);bad[field]='wrong';changed=copy.deepcopy(row);changed['coverage_sha256']=put(output.parent/'coverage.json',bad);put(rowpath,changed);refuse('coverage '+field,lambda:ns['recover_treatment_rows'](*args))
put(output.parent/'coverage.json',coverage);put(rowpath,row)
for field in row:
 bad=copy.deepcopy(row);bad[field]='wrong';put(rowpath,bad);refuse('row '+field,lambda:ns['recover_treatment_rows'](*args))
put(rowpath,row)
wrong=copy.deepcopy(inputs);wrong['plan']['sha256']='0'*64;refuse('registered plan hash',lambda:ns['recover_treatment_rows'](*args[:5],wrong,source_files))
wrong=copy.deepcopy(inputs);wrong['plan']['path']='../escape';refuse('registered traversal',lambda:ns['recover_treatment_rows'](*args[:5],wrong,source_files))
wrong=copy.deepcopy(inputs);wrong['plan']['path']='keys/no-read';refuse('credential path refused before read',lambda:ns['recover_treatment_rows'](*args[:5],wrong,source_files))
refuse('unadmitted current source',lambda:ns['recover_treatment_rows'](*args[:6],{}))
refuse('changed denominator',lambda:ns['recover_treatment_rows'](*args[:4],[],inputs,source_files))
namespace['recorded']={cell:row};refuse('duplicate other namespace row',lambda:exec(compile(ast.Module(body=block,type_ignores=[]),'actual-observer-treatment-block','exec'),namespace))
# Exact inverses: all old bytes and all unrelated AST restored.
old=(BASE/'baseline-treatment_production01.py').read_text();new=(MOD/'treatment_production.py').read_text()
a=old.index('def _close(');b=old.index('def produce_registered_treatments(');x=new.index('def _close(');y=new.index('def produce_registered_treatments(')
changes=[{'old':old[a:b],'new':new[x:y]}]
oldtail=old[old.index(' finally:\n  def pending():'):old.index(' return [rows[k] for k in ids]')]
newtail=new[new.index(' finally:\n  def summary():'):new.index(' return [rows[k] for k in ids]')]
changes.append({'old':oldtail,'new':newtail})
restored=new
for change in changes:ok(restored.count(change['new'])==1,'unique producer inverse seam');restored=restored.replace(change['new'],change['old'])
ok(restored==old,'complete producer byte inverse');ok(ast.dump(ast.parse(restored))==ast.dump(ast.parse(old)),'complete producer AST inverse')
oldj=(BASE/'baseline-overlay-job01.py').read_text();newj=(MOD/'job.py').read_text();lo=newj.index('    # Preserve authenticated treatment rows');hi=newj.index('    if not set(recorded) <=',lo);delta=newj[lo:hi]
ok(newj.replace(delta,'')==oldj,'complete job byte inverse')
restored=oldj
for change in json.loads((BASE/'JOB_INVERSE01.json').read_text())['changes']:restored=restored.replace(change['new'],change['old'])
ok(digest(restored.encode())==json.loads((BASE/'JOB_INVERSE01.json').read_text())['baseline_sha256'],'original four job substitutions inverse to Main pin')
put(BASE/'CORRECTION_INVERSE01.json',{'producer':changes,'job':[{'old':'','new':delta}],'scope':'source-only exact inverse to producer01; old four job inverse separately preserved'})
put(BASE/'CORRECTION_CHECKS01.json',{'status':'passed','checks':len(checks),'labels':checks,'scope':'stdlib actual AST-extracted methods and opaque owned metadata; no genuine lifecycle/native/numerical execution','red_witnesses':['old first pending writer aborts later writes','old reconcile ignores treatment namespace'],'not_tested':['genuine ResearchRun/Owner/claim or native recovery','array/component or numerical correctness','filesystem/process races and actual allocation exhaustion','publication impossible when all evidence writers fail']})
print(json.dumps({'status':'passed','checks':len(checks)}))
