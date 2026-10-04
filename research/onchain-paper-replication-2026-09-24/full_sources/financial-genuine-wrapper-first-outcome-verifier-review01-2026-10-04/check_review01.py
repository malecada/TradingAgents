import ast,copy,hashlib,importlib.util,itertools,json,os,shutil,stat,sys
from pathlib import Path
D=Path(__file__).resolve().parent;S=D/'source';P=D.parent/'financial-genuine-wrapper-first-outcome-verifier-preparation01-2026-10-04';T=D/'owned01';T.mkdir();sys.path.insert(0,str(S));spec=importlib.util.spec_from_file_location('outcome_review',S/'verifier01.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
checks=[];witness=[];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def ok(name,value,detail=None):
 if not value:raise AssertionError(name)
 checks.append({'name':name,'detail':detail})
def refuse(name,fn):
 try:fn()
 except (ValueError,OSError,TypeError,KeyError) as e:ok(name,True,{'error':type(e).__name__,'message':str(e)});return
 raise AssertionError('accepted '+name)
def dump(name,obj):(D/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
ok('exact source',sha(S/'verifier01.py')=='af95b4712edff8a0b5bc72c81946740b5cdc579114d47e91db35f14228b9ef65');ok('exact author manifest',sha(P/'MANIFEST01.json')=='752014b4222dba4471fd72492841030f3d376f9e2fcf20f658315a2358daf474')
m=json.loads((P/'MANIFEST01.json').read_text());rows=m['members'];ok('whole candidate membership',{p.relative_to(P).as_posix() for p in P.rglob('*') if p!=P/'MANIFEST01.json'}=={r['path'] for r in rows})
for r in rows:
 p=P/r['path'];s=p.lstat();good=stat.S_IMODE(s.st_mode)==r['mode']
 if r['kind']=='file':good=good and stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and s.st_nlink==r['nlink'] and sha(p)==r['sha256']
 elif r['kind']=='directory':good=good and stat.S_ISDIR(s.st_mode)
 elif r['kind']=='symlink':good=good and stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target']
 else:good=False
 ok('manifest '+r['path'],good)
q=json.loads((S/'REQUEST_FINAL03.json').read_text());ok('request source pin',sha(S/'REQUEST_FINAL03.json')==V.QHASH)
inverse=json.loads((S/'SOURCE_INVERSE01.json').read_text());ok('no original source substitution',inverse['unchanged_baseline_source_hashes']==q['source_files'])
for rel,pin in q['source_files'].items():
 ok('actual declared source body '+rel,sha(P/'baseline/capsule'/rel)==pin==sha(Path(q['capsule_root'])/rel))
for rel,pin in {**q['helper_hashes'],'parent01.py':q['caller_sha256']}.items():ok('actual Parent source/helper '+rel,sha(P/'baseline/parent'/rel)==pin==sha(Path(q['parent_root'])/rel))
for ref in [*q['proofs'].values(),q['final_review']]:ok('actual pinned release evidence '+Path(ref['path']).name,sha(Path(ref['path']))==ref['sha256'])
gate=json.loads((P/'baseline/capsule'/q['registration']).read_text());entry=gate['experiments'][q['identity']]
for role,ref in entry['inputs'].items():ok('actual exact registered input '+role,sha(P/'baseline/capsule'/ref['path'])==ref['sha256']==q['input_hashes'][role])
job=json.loads((P/'baseline/capsule'/entry['inputs']['execution_job']['path']).read_text())
# Real static bodies, no actual or invented outcome records.
par=T/'static-parent';shutil.copytree(P/'baseline/parent',par);shutil.copy2(S/'REQUEST_FINAL03.json',par/'REQUEST_FINAL03.json');cap=P/'baseline/capsule';ct=V.Tree(cap);pt=V.Tree(par)
context={'schema_version':1,'kind':'root-financial-first-outcome-observation-v1','identity':q['identity'],'capsule_inventory_sha256':V.sha(V.canonical(ct.inventory)),'parent_inventory_sha256':V.sha(V.canonical(pt.inventory)),'actual_parent_exit':None,'process_observation':None,'source_claim_review':None};raw=V.canonical(context)
result=V.verify(cap,par,raw,V.sha(raw));dump('STATIC_INSPECTION01.json',result);ok('static absence uncertain never planned',result['disposition']=='CLEANUP_UNCERTAIN' and result['claim_present'] is False and result['release_authorized'] is False and result['capacity_verified'] is False and result['paper_financial_fit_credit']==0)
for key,value in [('actual_parent_exit',True),('kind','wrong'),('schema_version',True),('identity','wrong'),('capsule_inventory_sha256','0'*64),('parent_inventory_sha256','0'*64),('process_observation',{}),('source_claim_review',{'path':'absent','sha256':None})]:
 c=copy.deepcopy(context);c[key]=value;b=V.canonical(c);refuse('observation refusal '+key,lambda b=b:V.external_context(b,V.sha(b),ct,pt,q['identity']))
for rawbad in (b'{"key":1,"key":2}',b'{"x":NaN}',b'{"x":Infinity}',b'{"x":-Infinity}'):refuse('strict JSON '+repr(rawbad),lambda rawbad=rawbad:V.decoded(rawbad))
for pin in (None,'','A'*64,'0'*63,1,True):refuse('strict hash '+repr(pin),lambda pin=pin:V.hashed(pin))
# Four dispositions are pure predicates. No fake claim/Owner/Run is constructed.
for cleanup in (False,True):
 for claim in (False,True):
  for planned in (False,True):
   for predis in (False,True):
    got=V.classify(claim_present=claim,planned_bytes=planned,cleanup_proved=cleanup,predispatch_proved=predis)
    ok('no cleanup remains uncertain '+repr((cleanup,claim,planned,predis)),cleanup or got=='CLEANUP_UNCERTAIN')
    if cleanup and not claim:ok('absent claim never planned '+repr((planned,predis)),got==('NO_CLAIM_PREDISPATCH_REFUSAL' if predis else 'UNEXPECTED_FAILURE_NO_CLAIM'))
# Original cache key semantics independently match original canonical_bytes.
prov={'opaque':'bounded provenance control, not a genuine checkpoint'};body=b'opaque state bytes not a tensor';key=V.sha(V.canonical({'provenance':prov,'epoch':1,'batch':0}));meta={'schema_version':1,'key':key,'provenance':prov,'members':{'state.pt':{'sha256':V.sha(body),'size':len(body)}}}
ok('opaque metadata cursor-key only',V.cursor_manifest(meta,prov,body)==key)
for k,v in [('key','0'*64),('provenance',{}),('schema_version',True),('members',{})]:
 mm=copy.deepcopy(meta);mm[k]=v;refuse('cursor opaque mutation '+k,lambda mm=mm:V.cursor_manifest(mm,prov,body))
# Owned complete namespace and file mutation controls.
r=T/'tiny';r.mkdir();(r/'empty').mkdir();(r/'opaque').write_bytes(b'bytes');tree=V.Tree(r);ok('full tiny denominator',set(tree.rows)=={'empty','opaque'});tree.close_check();(r/'opaque').write_bytes(b'changed');refuse('changed original byte',lambda:tree.raw('opaque'));refuse('changed complete namespace',tree.close_check)
for label,dangling in [('link',False),('dangling',True)]:
 r=T/label;r.mkdir();(r/'p').symlink_to(T/('not-here' if dangling else 'tiny'));refuse('whole root '+label,lambda r=r:V.inventory(r))
r=T/'hardlink';r.mkdir();(r/'one').write_bytes(b'x');os.link(r/'one',r/'two');refuse('hardlink inventory refusal',lambda:V.inventory(r))
oversize=P/'opaque_controls01/oversized/big';ok('retained negative extent honestly over cap',oversize.stat().st_size==4*1024**2+1);refuse('retained offline oversize refuses',lambda:V.inventory(oversize.parent))
# Genuine acquired descriptors and unchanged first-fatal cleanup (no fake owner).
for i,(one,two) in enumerate(itertools.product((None,OSError,MemoryError,KeyboardInterrupt,SystemExit),repeat=2)):
 p=T/('fd-%02d'%i);p.write_bytes(b'opaque');fd=os.open(p,os.O_RDONLY);primary=None if one is None else one('body');later=None if two is None else two('close');calls=[];caught=None
 def close():
  os.close(fd);calls.append('closed')
  if later is not None:raise later
 try:
  try:
   if primary is not None:raise primary
  finally:V.R._cleanup((close,lambda:calls.append('last')))
 except BaseException as e:caught=e
 fatal=lambda e:e is not None and (isinstance(e,MemoryError) or not isinstance(e,Exception))
 expected=primary if fatal(primary) else later if fatal(later) else primary if later is None else None
 ok('all cleanup callbacks '+str(i),calls==['closed','last']);refuse('actual fd closed '+str(i),lambda:os.fstat(fd));ok('first fatal identity '+str(i),caught is expected if expected is not None else (caught is None if later is None else type(caught).__name__=='CleanupFailure'))
# VF1: exact extracted guard field predicates, original resource config inputs.
# No full guard/Owner/claim receipt is built or written; these are isolated kwargs.
fn=next(x for x in ast.parse((S/'verifier01.py').read_text()).body if isinstance(x,ast.FunctionDef) and x.name=='verify');guard_checks=[]
for x in ast.walk(fn):
 if isinstance(x,ast.Expr) and isinstance(x.value,ast.Call) and isinstance(x.value.func,ast.Name) and x.value.func.id=='require' and any(isinstance(y,ast.Constant) and y.value in ('original native policy','guard retry refused') for y in ast.walk(x)):guard_checks.append(x)
code=compile(ast.Module(body=guard_checks,type_ignores=[]),'<exact-guard-policy-predicates>','exec');ok('exact two guard predicates',len(guard_checks)==2)
fields={**job['resources'],'memory_swap_max_bytes':0,'retry':False}
mutations={'elapsed_time_kill':True,'storage_breach':{'opaque':'retained observed failure'},'storage_last_error':'observed scan failure','cleanup_error':'observed close failure','child_log_limit_reached':True,'child_exit_code':137,'memory_events':{'oom':1,'oom_kill':1},'limit_reason':'host runtime memory reserve breached'}
for field,value in mutations.items():
 kw={**fields,field:value};exec(code,{'require':V.require,'guard':kw,'job':job});got=V.classify(claim_present=True,planned_bytes=True,cleanup_proved=True,predispatch_proved=False);ok('VF1 explicit conflicting resource field still passes '+field,got=='PLANNED_FAILED_SPENT_INTERRUPT1_BYTES');witness.append({'finding':'VF1','source_seam':'exact native policy/retry require expressions plus unchanged classifier','mutated_original_resource_field':field,'value':value,'guard_predicates':'accepted','disposition':got,'qualification':'isolated scalar source witness; no genuine or fabricated claim/Owner/guard receipt, no actual outcome classification'})
# The end-of-verify exit guard only checks None, not contradictions with terminal.
exit_checks=[x for x in fn.body if isinstance(x,ast.If) and ast.unparse(x.test)=="context['actual_parent_exit'] is None"]
ok('exit guard source observed',len(exit_checks)==2)
for exitcode in (0,1,137):
 c={**context,'actual_parent_exit':exitcode};b=V.canonical(c);V.external_context(b,V.sha(b),ct,pt,q['identity']);ns={'context':c,'cleanup':True,'missing':[]};exec(compile(ast.Module(body=exit_checks,type_ignores=[]),'<exact-actual-exit-guard>','exec'),ns);ok('VF1 actual exit cannot suppress conflicting planned bytes '+str(exitcode),ns['cleanup'] is True);witness.append({'finding':'VF1','actual_parent_exit_scalar':exitcode,'cleanup_stays_true':ns['cleanup'],'qualification':'exact source scalar seam; actual Root exit not asserted'})
# The genuine lifecycle records exact failure reason; verifier terminal join omits it.
subs={x.slice.value for x in ast.walk(fn) if isinstance(x,ast.Subscript) and isinstance(x.value,ast.Name) and x.value.id=='terminal' and isinstance(x.slice,ast.Constant)};ok('VF1 lifecycle reason omitted', 'reason' not in subs)
# No full native/lifecycle test is represented by the scalar witnesses.
ok('no numerical imports',not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')))
dump('VF1_WITNESSES01.json',witness);dump('CHECKS01.json',{'count':len(checks),'checks':checks,'source_sha256':sha(S/'verifier01.py'),'candidate_manifest_sha256':sha(P/'MANIFEST01.json'),'verdict':'WITHHELD_VF1','actual_outcomes_inspected':0,'actual_claims_created':0,'baseline_source_bodies':len(q['source_files']),'retained_author_oversize_bytes':oversize.stat().st_size,'scope':'source authentication, actual static no-outcome route, owned IO and extracted scalar contradiction controls only','authority':None});print(json.dumps({'checks':len(checks),'verdict':'WITHHELD_VF1','source':sha(S/'verifier01.py')}))
