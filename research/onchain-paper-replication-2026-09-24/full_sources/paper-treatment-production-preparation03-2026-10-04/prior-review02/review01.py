"""Independent exact correction review; stdlib metadata only, no authority objects."""
import ast,copy,hashlib,json,os,re,stat,sys
from pathlib import Path
D=Path(__file__).resolve().parent
S=D.parent/'paper-treatment-production-preparation02-2026-10-04'
OLD=D.parent/'paper-treatment-production-preparation01-2026-10-04'
P='overlay/tradingagents/research/onchain_replication/'
checks=[]
def h(raw):return hashlib.sha256(raw).hexdigest()
def check(label,condition):
 if not condition:raise AssertionError(label)
 checks.append(label)
def put(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True);raw=json.dumps(obj,sort_keys=True,separators=(',',':')).encode();p.write_bytes(raw);return h(raw)
def refusal(label,fn):
 try:fn()
 except (ValueError,KeyError,FileNotFoundError):checks.append(label);return
 raise AssertionError(label)
manifest=json.loads((S/'MANIFEST03.json').read_bytes())
check('exact received manifest',h((S/'MANIFEST03.json').read_bytes())=='7a9d8dbaf8ced852e80e89770b02d512715a0655f847d0db4a13450daa26e75b')
entries=manifest['entries'];actual={str(p.relative_to(S)) for p in S.rglob('*') if p!=S/'MANIFEST03.json'}
check('complete source tree names',actual=={r['path'] for r in entries})
for r in entries:
 p=S/r['path'];st=p.lstat();check('mode '+r['path'],stat.S_IMODE(st.st_mode)==r['mode'])
 if r['type']=='file':check('body '+r['path'],p.is_file() and not p.is_symlink() and st.st_size==r['bytes'] and h(p.read_bytes())==r['sha256'])
 else:check('directory '+r['path'],p.is_dir() and not p.is_symlink())
check('source cardinality',len(entries)==110 and sum(r['type']=='file' for r in entries)==86)
inv=json.loads((S/'CORRECTION_INVERSE02.json').read_text())
for name,key in [('job.py','job'),('treatment_production.py','producer')]:
 raw=(S/P/name).read_text();inverse=raw
 for e in reversed(inv[key]):check('single inverse '+name+str(len(e['new'])),inverse.count(e['new'])==1);inverse=inverse.replace(e['new'],e['old'])
 check('full bytes inverse '+name,inverse.encode()==(OLD/P/name).read_bytes())
 check('full AST inverse '+name,ast.dump(ast.parse(inverse))==ast.dump(ast.parse((OLD/P/name).read_text())))
 if name=='job.py':
  for e in reversed(json.loads((S/'JOB_INVERSE01.json').read_text())['changes']):check('inherited exact substitution',inverse.count(e['new'])==1);inverse=inverse.replace(e['new'],e['old'])
  check('inherited four substitutions inverse Main',inverse.encode()==(S/'baseline-job.py').read_bytes())
check('contract unchanged',(S/P/'treatment_contract.py').read_bytes()==(OLD/P/'treatment_contract.py').read_bytes())
# Run only exact helper AST and genuine pure path/name functions; package imports omitted.
ns={'Path':Path,'json':json,'re':re,'digest':h}
exec(compile((S/P/'treatment_contract.py').read_text(),'actual-contract','exec'),ns)
a=ast.parse((S/'origins/admission.py').read_text())
exec(compile(ast.Module(body=[n for n in a.body if isinstance(n,ast.FunctionDef) and n.name in ('local_path','identity')],type_ignores=[]),'actual-pure-admission','exec'),ns)
class RelativeImports(ast.NodeTransformer):
 def visit_ImportFrom(self,n):return None if n.level else n
actualtree=ast.parse((S/P/'treatment_production.py').read_text());names={'_close','_finalize_pending','_retained_bytes','recover_treatment_rows'}
subset=[RelativeImports().visit(copy.deepcopy(n)) for n in actualtree.body if isinstance(n,ast.FunctionDef) and n.name in names]
exec(compile(ast.fix_missing_locations(ast.Module(body=subset,type_ignores=[])),'actual-correction-helper-AST','exec'),ns)
oldtree=ast.parse((OLD/P/'treatment_production.py').read_text());oldns={}
exec(compile(ast.Module(body=[n for n in oldtree.body if isinstance(n,ast.FunctionDef) and n.name=='_close'],type_ignores=[]),'exact-predecessor-close','exec'),oldns)
# Independent T2 RED actual original finalbody, then new helper, same callbacks.
prod=next(n for n in oldtree.body if isinstance(n,ast.FunctionDef) and n.name=='produce_registered_treatments')
final=next(n for n in prod.body if isinstance(n,ast.Try)).finalbody
redcalls=[];redsummary=[];fatal=KeyboardInterrupt('opaque primary');secondary=OSError('opaque first row write')
def redwrite(row):redcalls.append(row['id']);raise secondary
oldscope={'p':{'asset':'ETH','expected_weeks':['w1','w2','w3']},'ids':['c1','c2','c3'],'rows':{},'record':redwrite,'primary':fatal,'_close':oldns['_close'],'directory':D/'not-published','graphs':{},'_immutable':lambda *a:redsummary.append(a)}
try:exec(compile(ast.Module(body=final,type_ignores=[]),'exact-old-finalbody','exec'),oldscope)
except BaseException as e:check('T2 RED original fatal preserved',e is fatal)
check('T2 RED original skipped later pending',redcalls==['c1'])
# Full three-callback Cartesian error domain; newly created objects for each case.
classes=(None,OSError,MemoryError,KeyboardInterrupt,SystemExit)
serial=0
for primary_type in classes:
 for row_type in classes:
  for summary_type in classes:
   for audit_type in classes:
    serial+=1;calls=[];rows={'retained':{'id':'retained','status':'complete'}};audits=[]
    primary=primary_type('primary') if primary_type else None
    errors={k:t(k) if t else None for k,t in [('row',row_type),('summary',summary_type),('audit',audit_type)]}
    def writer(row):
     calls.append(row['id'])
     if row['id']=='missing1' and errors['row'] is not None:raise errors['row']
     rows[row['id']]=row
    def summary():
     calls.append('summary')
     if errors['summary'] is not None:raise errors['summary']
    def audit(v):
     calls.append('audit');audits.append(copy.deepcopy(v))
     if errors['audit'] is not None:raise errors['audit']
    ordered=([primary] if primary else [])+[e for e in errors.values() if e is not None]
    expected=next((e for e in ordered if isinstance(e,MemoryError) or not isinstance(e,Exception)),ordered[0] if ordered else None)
    observed=None
    try:ns['_finalize_pending']({'asset':'ETH','expected_weeks':['old','w1','w2']},['retained','missing1','missing2'],rows,writer,summary,audit,primary)
    except BaseException as e:observed=e
    check('T2 selected first fatal/ordinary '+str(serial),observed is expected)
    check('T2 all independent publications '+str(serial),calls==['missing1','missing2','summary','audit'])
    check('T2 no failed-write row fabrication '+str(serial),('missing1' in rows)==(row_type is None) and rows['retained']['status']=='complete' and 'missing2' in rows)
    record=audits[0];check('T2 audit exact unavailable gap '+str(serial),record['unconfirmed_row_cells']==(['missing1'] if row_type else []) and record['attempted_pending_cells']==['missing1','missing2'])
    if expected is not None:
     others=[e for e in ordered if e is not expected]
     check('T2 retains actual secondary exception identities '+str(serial),not others or (isinstance(expected.__cause__,BaseExceptionGroup) and {id(e) for e in expected.__cause__.exceptions}=={id(e) for e in others}))
# Build independent opaque metadata fixture. These inputs are NOT claims/graphs.
# Actual corrected function is called only as metadata plumbing, without Run/Owner.
root=D/'opaque-root';mod=root/'tradingagents/research/onchain_replication';mod.mkdir(parents=True)
for name in ('treatment_contract.py','treatment_production.py'):(mod/name).write_bytes((S/P/name).read_bytes())
ns['__file__']=str(mod/'treatment_production.py')
sourcefiles={str(p.relative_to(root)):h(p.read_bytes()) for p in mod.iterdir()}
week='2024-01-01T00:00:00Z';end='2024-01-08T00:00:00Z';exp='opaque-review-only';cell='treatment-eth-whale-2024-01-01';source='1'*40;claimhash=h(b'opaque-not-a-claim')
parent={k:k for k in ('manifest_input','coverage_input','claim_input','terminal_input','ledger_input')};parent['components']={'node_ids.npy':'nodes'}
plan={'schema_version':1,'kind':'paper-graph-treatment-v1','asset':'ETH','variant':'whale','coverage':[[week,end]],'expected_weeks':[week],'parents':{week:parent},'cohort_input':None,'cohort_review_input':None}
inputs={}
for role in list(parent.values())[:-1]+['nodes']:
 path=root/'opaque-inputs'/(role+'.json');pin=put(path,{'opaque':role});inputs[role]={'path':str(path.relative_to(root)),'sha256':pin}
planpath=root/'opaque-inputs/plan.json';planhash=put(planpath,plan);inputs['late_plan']={'path':str(planpath.relative_to(root)),'sha256':planhash}
jobpath=root/'opaque-inputs/job.json';inputs['execution_job']={'path':str(jobpath.relative_to(root)),'sha256':put(jobpath,{'kind':'treatments','payload':{'plan_input':'late_plan'}})}
base=root/'research_artifacts/onchain-paper-replication-2026-09-24/treatments'/exp
put(base/'intent.json',{'plan_sha256':planhash,'claim_sha256':claimhash,'source':source,'cells':[cell],'financial_credit':0})
output=base/cell/'manifest.json';mh=put(output,{'opaque':'not graph components'})
receipt={'schema_version':1,'kind':'registered-graph-treatment-receipt','asset':'ETH','variant':'whale','week':week,'end_utc':end,'claim_sha256':claimhash,'source':source,'plan_sha256':planhash,'manifest_sha256':mh,'cohort_sha256':None,'cohort_review_sha256':None}
for field,k in [('parent_manifest_sha256','manifest_input'),('parent_coverage_sha256','coverage_input'),('parent_claim_sha256','claim_input'),('parent_terminal_sha256','terminal_input'),('parent_ledger_sha256','ledger_input')]:receipt[field]=inputs[k]['sha256']
coverage={k:receipt[k] for k in ('asset','week','end_utc','claim_sha256','plan_sha256')};coverage['graph_manifest_sha256']=mh
rh=put(output.parent/'treatment.json',receipt);ch=put(output.parent/'coverage.json',coverage)
row={'id':cell,'status':'complete','asset':'ETH','week':week,'manifest_path':str(output.relative_to(root)),'manifest_sha256':mh,'treatment_receipt_sha256':rh,'coverage_sha256':ch};rowpath=base/(cell+'.json');put(rowpath,row)
args=[root,exp,source,claimhash,[cell],inputs,sourcefiles]
recovered=ns['recover_treatment_rows'](*args)
check('T1 GREEN discovers actual treatment namespace opaque row',recovered=={cell:row})
# Execute exact old source loop; it demonstrably misses the same opaque row.
jobtree=ast.parse((OLD/P/'job.py').read_text());reconcile=next(n for n in jobtree.body if isinstance(n,ast.FunctionDef) and n.name=='_reconcile')
loop=next(n for n in reconcile.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='name')
oldloop={'root':root,'PREFIX':'research_artifacts/onchain-paper-replication-2026-09-24','args':type('MetadataOnly',(),{'experiment':exp})(),'claim':{'experiment':{'cells':[cell]}},'recorded':{},'json':json}
exec(compile(ast.Module(body=[loop],type_ignores=[]),'original-source-namespace-loop','exec'),oldloop)
check('T1 RED exact original loop omitted same durable row',oldloop['recorded']=={})
# Bound input hash substitutions; no fake claim is constructed or started.
for field in ('source','claim_sha256','plan_sha256','cells'):
 original=(base/'intent.json').read_bytes();v=json.loads(original);v[field]='wrong';put(base/'intent.json',v)
 refusal('T1 bad intent '+field,lambda:ns['recover_treatment_rows'](*args));(base/'intent.json').write_bytes(original)
for field in ('asset','week','manifest_path','manifest_sha256','coverage_sha256','treatment_receipt_sha256','id'):
 bad=dict(row);bad[field]='wrong';put(rowpath,bad);refusal('T1 bad durable '+field,lambda:ns['recover_treatment_rows'](*args));put(rowpath,row)
for field in ('source','claim_sha256','plan_sha256','asset','week','parent_manifest_sha256','parent_coverage_sha256','parent_claim_sha256','parent_terminal_sha256','parent_ledger_sha256','cohort_sha256'):
 bad=dict(receipt);bad[field]='wrong';wrong=dict(row);wrong['treatment_receipt_sha256']=put(output.parent/'treatment.json',bad);put(rowpath,wrong)
 refusal('T1 internally rehashed receipt corruption '+field,lambda:ns['recover_treatment_rows'](*args));put(output.parent/'treatment.json',receipt);put(rowpath,row)
for field in ('asset','week','end_utc','claim_sha256','plan_sha256','graph_manifest_sha256'):
 bad=dict(coverage);bad[field]='wrong';wrong=dict(row);wrong['coverage_sha256']=put(output.parent/'coverage.json',bad);put(rowpath,wrong)
 refusal('T1 internally rehashed coverage corruption '+field,lambda:ns['recover_treatment_rows'](*args));put(output.parent/'coverage.json',coverage);put(rowpath,row)
wrong=copy.deepcopy(inputs);wrong['late_plan']['sha256']=None;refusal('T1 unresolved design input cannot substitute resolved claim input',lambda:ns['recover_treatment_rows'](*args[:5],wrong,sourcefiles))
wrong=dict(sourcefiles);wrong[next(iter(wrong))]=h(b'wrong');refusal('T1 mutated source pin',lambda:ns['recover_treatment_rows'](*args[:6],wrong))
refusal('T1 missing denominator cell',lambda:ns['recover_treatment_rows'](root,exp,source,claimhash,[],inputs,sourcefiles))
u={'id':cell,'asset':'ETH','week':week,'status':'unavailable','reason':'opaque failure retained'};put(rowpath,u)
check('T1 unavailable kept as unavailable',ns['recover_treatment_rows'](*args)=={cell:u});put(rowpath,row)
# Correction wiring is after original actual owner/death/claim checks, before fallback.
body=(S/P/'job.py').read_text();loc=body.index('    treatment_rows = recover_treatment_rows(')
check('T1 passes actual resolved claim inputs',"claim['inputs']" in body[loc:loc+300])
check('T1 recovery occurs after owner/death and before fallback',body.index("if group is None:\n        raise RuntimeError('admitted run has no cgroup death proof')")<loc<body.index("cells = [recorded.get(name"))
check('T1 duplicate namespace refuses',"if set(treatment_rows) & set(recorded):" in body[loc:loc+500])
check('no numerical package loaded',not any(k in sys.modules for k in ('numpy','torch','scipy')))
report={'scope':'independent correction-only metadata/AST review; synthetic records are not scientific authority','decision':'ACCEPTED_SOURCE_ONLY_CORRECTIONS','checks':checks,'count':len(checks),'source_manifest_sha256':h((S/'MANIFEST03.json').read_bytes()),'remaining':['producer01 original whole implementation is not self-reviewed here','no array/component numerical validation in observer','no genuine claim/Run/native/runtime execution','fund historical known_at policy remains unadmitted','Root exact source/registration/budget/resource/recovery and downstream review required']}
(D/'REVIEW01.json').write_text(json.dumps(report,indent=2)+'\n');print(len(checks),'checks passed')
