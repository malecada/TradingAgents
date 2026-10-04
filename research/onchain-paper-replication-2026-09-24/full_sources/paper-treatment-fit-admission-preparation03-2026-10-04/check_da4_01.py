"""DA4 only: real owned pathname controls; no Run, claims, arrays or native job."""
import ast,copy,hashlib,importlib.util,json,os,stat
from pathlib import Path
B=Path(__file__).resolve().parent;O=B.parent/'paper-treatment-fit-admission-preparation02-2026-10-04';R=B.parent/'paper-treatment-fit-admission-review02-2026-10-04';REL='overlay/tradingagents/research/onchain_replication/treatment_admission.py';checks=[];cases=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ok(v,label):
 if not v:raise AssertionError(label)
 checks.append(label)
def put(name,obj):(B/name).write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n')
old=(O/REL).read_text();new=(B/REL).read_text();a="and not actual_row_path.exists(), 'only failed absent cell may use postmortem absence'";b="and not actual_row_path.is_symlink() and not actual_row_path.exists() and actual_row_path.resolve() == actual_row_path, 'only failed absent cell may use postmortem absence'"
ok(new.count(b)==1 and new.replace(b,a)==old,'one-substitution full byte inverse')
ok(ast.dump(ast.parse(new.replace(b,a)))==ast.dump(ast.parse(old)),'full AST inverse')
for p in sorted(O.rglob('*')):
 if p.is_file() and p.relative_to(O).as_posix()!=REL:
  q=B/p.relative_to(O);ok(p.read_bytes()==q.read_bytes() and stat.S_IMODE(p.stat().st_mode)==stat.S_IMODE(q.stat().st_mode),'unchanged inherited body/mode '+p.relative_to(O).as_posix())
for p in sorted(R.rglob('*')):
 if p.is_file():ok(p.read_bytes()==(B/'prior-review02'/p.relative_to(R)).read_bytes(),'preserved exact review02 '+p.relative_to(R).as_posix())
# Every top-level source function other than admit_treatment remains identical AST.
original=ast.parse(old);candidate=ast.parse(new)
for before,after in zip(original.body,candidate.body,strict=True):
 if isinstance(before,ast.FunctionDef) and before.name=='admit_treatment':continue
 ok(ast.dump(before)==ast.dump(after),'unchanged clause/function AST '+getattr(before,'name',type(before).__name__))
def predicate(source):
 module=ast.parse(source);fn=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='admit_treatment');loop=next(n for n in fn.body if isinstance(n,ast.For));branch=next(n for n in loop.body if isinstance(n,ast.If) and ast.unparse(n.test)=="reference['disposition_input'] is None");return compile(ast.Module(body=branch.body,type_ignores=[]),'actual-absence-predicate','exec')
oldcode=predicate(old);newcode=predicate(new)
# Import new stdlib-only module solely for pure disposition/require, never admit_treatment.
spec=importlib.util.spec_from_file_location('opaque_da4_module',B/REL);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);ok(m.PRODUCER_SOURCE_PINS is None,'producer source pins stay None')
root=B/'owned-path-cases01';root.mkdir(exist_ok=False)
(root/'regular').write_bytes(b'opaque regular metadata\n');(root/'directory').mkdir();(root/'target-directory').mkdir()
(root/'live-link').symlink_to('regular');(root/'dangling-link').symlink_to('absent-target')
(root/'ancestor-live').symlink_to('target-directory',target_is_directory=True);(root/'ancestor-dangling').symlink_to('absent-directory',target_is_directory=True)
(root/'plain-parent').mkdir()
paths={'missing':root/'missing','missing-under-real-parent':root/'plain-parent'/'missing','regular-file':root/'regular','directory':root/'directory','live-link':root/'live-link','dangling-link':root/'dangling-link','ancestor-live-redirect-to-missing':root/'ancestor-live'/'missing','ancestor-dangling-redirect':root/'ancestor-dangling'/'missing'}
week='2020-01-06T00:00:00Z';cell='treatment-eth-whale-2020-01-06';pin='0'*64;row={'id':cell,'status':'unavailable','reason':'owned worker ended before durable cell disposition; no retry'};original_row=copy.deepcopy(row)
claim={'experiment_id':'opaque-only','experiment':{'cells':[cell]}};terminal={'status':'failed','experiment_id':'opaque-only','claim_sha256':pin};plan={'expected_weeks':[week]}
result=m.disposition(claim,terminal,[row],pin,pin,plan,week,'whale','ETH',absent=True);ok(result is row and row==original_row,'actual pure fallback remains same unavailable object/no fields fabricated')
for label,path in paths.items():
 observations={'lexists':os.path.lexists(path),'exists':path.exists(),'is_symlink':path.is_symlink(),'resolved':str(path.resolve()),'lexical':str(path)}
 for version,program in [('previous',oldcode),('successor',newcode)]:
  try:exec(program,{'require':m.require,'row':row,'terminal':terminal,'actual_row_path':path});outcome='accepted'
  except ValueError:outcome='refused'
  expected='accepted' if label.startswith('missing') or (version=='previous' and label in ('dangling-link','ancestor-live-redirect-to-missing','ancestor-dangling-redirect')) else 'refused'
  ok(outcome==expected,label+' '+version+' '+expected);cases.append({'case':label,'source':version,'outcome':outcome,'observation':observations})
  ok(row==original_row,'predicate never fabricates disposition fields')
# No completed coercion and terminal exactness on the true absent path.
for row_status,terminal_status in [('complete','failed'),('unavailable','complete'),('unavailable','pending'),('unavailable',None)]:
 try:exec(newcode,{'require':m.require,'row':{**row,'status':row_status},'terminal':{**terminal,'status':terminal_status},'actual_row_path':paths['missing']})
 except ValueError:checks.append('wrong row/terminal refuses '+str((row_status,terminal_status)))
 else:raise AssertionError('coerced completed/active row')
# Validate old descriptor modes/source hashes in full preserved manifests separately.
for manifest,base,key in [(O/'MANIFEST02.json',O,'entries'),(R/'MANIFEST01.json',R,'entries')]:
 doc=json.loads(manifest.read_text());ok({e['path'] for e in doc[key]}=={p.relative_to(base).as_posix() for p in base.rglob('*')}-{manifest.name},'old frozen complete member set')
 for e in doc[key]:
  p=base/e['path'];s=p.lstat();ok(stat.S_IMODE(s.st_mode)==e['mode'],'old frozen mode')
  if e['type']=='file':ok(sha(p)==e['sha256'] and s.st_size==e['bytes'],'old frozen bytes')
put('DA4_INVERSE01.json',{'old_sha256':sha(O/REL),'candidate_sha256':sha(B/REL),'old':a,'new':b,'full_byte_inverse':True,'full_ast_inverse':True})
put('DA4_CHECKS01.json',{'status':'passed','checks':len(checks),'labels':checks,'path_cases':cases,'red':'Old predicate accepts a present dangling leaf symlink and ancestor redirects to missing targets','green':'Successor accepts only canonical missing owned paths and refuses every occupied/redirected case','scope':'Actual extracted predicate + pure original disposition on owned tiny paths; no genuine Run/claim/native/numerical execution','limitations':['Concurrent pathname mutation not modeled; source claim is point-in-time checks only','Symlinks remain owned control witnesses and are typed explicitly in final manifest; no recovered POSIX claim','Producer source pins remain None and genuine treatment admission remains refused']})
print(json.dumps({'checks':len(checks),'path_cases':len(cases),'source':sha(B/REL)}))
