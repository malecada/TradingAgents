import ast,copy,hashlib,importlib.util,json,os,stat,sys
from pathlib import Path
D=Path(__file__).resolve().parent;S=D.parent/'paper-treatment-fit-admission-preparation03-2026-10-04';OLD=D.parent/'paper-treatment-fit-admission-preparation02-2026-10-04';rel='overlay/tradingagents/research/onchain_replication/treatment_admission.py';checks=[];witness=[]
def check(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
check('frozen manifest hash',sha(S/'MANIFEST03.json')=='8f5e7ac08046c3e63b1237ed62f57e24ee9e9d046bb8cf07224bb013fa1a1d38')
rows=json.loads((S/'MANIFEST03.json').read_text())['entries'];check('complete exact manifest membership',{r['path'] for r in rows}=={str(p.relative_to(S)) for p in S.rglob('*') if p!=S/'MANIFEST03.json'})
for r in rows:
 p=S/r['path'];s=p.lstat();check('mode '+r['path'],stat.S_IMODE(s.st_mode)==r['mode'])
 if r['type']=='file':check('body '+r['path'],stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and sha(p)==r['sha256'])
 elif r['type']=='directory':check('directory '+r['path'],stat.S_ISDIR(s.st_mode))
 elif r['type']=='symlink':check('owned typed link '+r['path'],stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target'])
 else:raise AssertionError('unknown entry kind')
check('actual cardinality',len(rows)==79 and sum(r['type']=='file' for r in rows)==65 and sum(r['type']=='symlink' for r in rows)==4)
old=(OLD/rel).read_text();new=(S/rel).read_text();inverse=json.loads((S/'DA4_INVERSE01.json').read_text());check('received candidate hash',sha(S/rel)=='492e15e271a6092db6ba65e3e8a347328e4c2fcc9f28604e694ef1cb5506e2ab')
check('exact single substitution and byte inverse',new.count(inverse['new'])==1 and new.replace(inverse['new'],inverse['old'])==old);check('complete AST inverse',ast.dump(ast.parse(new.replace(inverse['new'],inverse['old'])))==ast.dump(ast.parse(old)))
for p in OLD.rglob('*'):
 if p.is_file() and str(p.relative_to(OLD))!=rel:
  q=S/p.relative_to(OLD);check('inherited body unchanged '+str(p.relative_to(OLD)),q.read_bytes()==p.read_bytes() and stat.S_IMODE(q.stat().st_mode)==stat.S_IMODE(p.stat().st_mode))
# Only exact absence branch runs. No call to actual admission or ResearchRun.
def code(text):
 fn=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='admit_treatment')
 branch=next(n for n in ast.walk(fn) if isinstance(n,ast.If) and ast.unparse(n.test)=="reference['disposition_input'] is None")
 return compile(ast.Module(body=branch.body,type_ignores=[]),'exact-source-absence-branch','exec')
oldcode=code(old);newcode=code(new)
spec=importlib.util.spec_from_file_location('opaque_source_only',S/rel);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
T=D/'owned-paths';T.mkdir();(T/'real-dir').mkdir();(T/'file').write_bytes(b'opaque');(T/'link-live').symlink_to('file');(T/'link-dangling').symlink_to('nowhere');(T/'ancestor-live').symlink_to('real-dir',target_is_directory=True);(T/'ancestor-dangling').symlink_to('absent-dir',target_is_directory=True);(T/'link-loop').symlink_to('link-loop')
paths={'canonical-absent':T/'absent','canonical-nested-absent':T/'real-dir/missing','regular':T/'file','directory':T/'real-dir','live-leaf-link':T/'link-live','dangling-leaf-link':T/'link-dangling','live-ancestor-missing':T/'ancestor-live/missing','dangling-ancestor-missing':T/'ancestor-dangling/missing','loop-link':T/'link-loop'}
week='2020-01-06T00:00:00Z';cell='treatment-eth-whale-2020-01-06';pin='0'*64
# Reconstruct actual missing row from frozen original observer AST, not invented fields.
job=S.parent/'paper-treatment-production-preparation03-2026-10-04/overlay/tradingagents/research/onchain_replication/job.py';fn=next(n for n in ast.parse(job.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='_reconcile');assignment=next(n for n in fn.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='cells' for t in n.targets));row=eval(compile(ast.Expression(assignment.value.elt.args[1]),'actual-original-postmortem-expression','eval'),{'name':cell});frozen=copy.deepcopy(row)
claim={'experiment_id':'opaque-only','experiment':{'cells':[cell]}};terminal={'status':'failed','experiment_id':'opaque-only','claim_sha256':pin};plan={'expected_weeks':[week]}
check('preserved pure missing disposition shape',m.disposition(claim,terminal,[row],pin,pin,plan,week,'whale','ETH',absent=True) is row and set(row)=={'id','status','reason'})
for label,path in paths.items():
 for version,program in [('original',oldcode),('successor',newcode)]:
  result='accepted';error=None
  try:exec(program,{'require':m.require,'row':row,'terminal':terminal,'actual_row_path':path})
  except (ValueError,RuntimeError,OSError) as e:result='refused';error=type(e).__name__
  wanted='accepted' if label.startswith('canonical') or (version=='original' and label in ('dangling-leaf-link','live-ancestor-missing','dangling-ancestor-missing','loop-link')) else 'refused'
  check('actual path '+label+' '+version,result==wanted)
  witness.append({'case':label,'source':version,'result':result,'error':error,'path':str(path),'exists':path.exists(),'lexists':os.path.lexists(path),'is_symlink':path.is_symlink()})
  check('no row fields fabricated '+label+version,row==frozen)
for rs,ts in [('complete','failed'),('unavailable','complete'),('unavailable','pending'),('unavailable',None)]:
 try:exec(newcode,{'require':m.require,'row':{**row,'status':rs},'terminal':{**terminal,'status':ts},'actual_row_path':paths['canonical-absent']})
 except ValueError:checks.append('not complete coercion '+str((rs,ts)))
 else:raise AssertionError('wrong status accepted')
check('producer pins remain None',m.PRODUCER_SOURCE_PINS is None);check('no numerical imports',not any(k in sys.modules for k in ('numpy','torch','scipy')))
(D/'WITNESS01.json').write_text(json.dumps({'actual_postmortem_row':row,'cases':witness,'scope':'actual owned paths and exact extracted predicate; no admitted Run/Owner'},indent=2)+'\n')
(D/'REVIEW01.json').write_text(json.dumps({'decision':'ACCEPTED_SOURCE_ONLY_DA4_CORRECTION','checks':checks,'count':len(checks),'candidate_sha256':sha(S/rel),'manifest_sha256':sha(S/'MANIFEST03.json'),'limitations':['point-in-time predicate only; concurrent path mutations not modeled','inherited source preservation verified, not independent self-review of earlier DA1-3 implementation','no actual admission/source composition/native/financial capacity','producer pins and historical fund policy remain unadmitted']},indent=2)+'\n');print(len(checks),'passed')
