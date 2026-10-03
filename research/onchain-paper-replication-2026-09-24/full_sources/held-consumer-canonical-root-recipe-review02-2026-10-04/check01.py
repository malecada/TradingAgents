"""Independent bounded RR1–RR5 successor review; no installation or admission."""
import ast,copy,hashlib,importlib.util,json,os,stat,sys
from pathlib import Path
H=Path(__file__).resolve().parent;C=H.parent/'held-consumer-canonical-root-recipe02-2026-10-04';B=H.parent/'held-consumer-canonical-root-recipe01-2026-10-04';V=H.parent/'held-consumer-canonical-root-recipe-review01-2026-10-04'
sys.path.insert(0,str(C))
import prepare01 as P
import rebind01 as R
import manifest02 as M
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
oldP=module('old_prepare',B/'prepare01.py');sys.modules['prepare01']=oldP
try:oldR=module('old_rebind',B/'rebind01.py')
finally:sys.modules['prepare01']=P
checks=[];witnesses=[]
def ok(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def body(p):
 p=Path(p);s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size<=4*1024**2;return p.read_bytes()
def refused(n,fn):
 try:fn()
 except (ValueError,KeyError,TypeError,AssertionError):checks.append(n);return
 raise AssertionError(n)
pins={'prepare01.py':'12457e989adb553c6fea32239d36bafb3810865413e94f9d9684c47572a1dc0e','rebind01.py':'7c7d442983ac4b12905e991fd6bde105b93ac25fc8b8bb3772466179e295ccef','manifest02.py':'60ed0b35f8eab6360a23493266860ed671c188de2d62b0215393fbae31f47c05','MANIFEST02.json':'6b6bfe5126cd783e6d0e0ec4555b30ae220e3a4ded71c3ff73a261a594040683','SOURCE_EXPECTATIONS02.json':'e7ba2f536d8783f380db41922af04e030a680258bb87ed918648a0c57d89d436'}
for n,pin in pins.items():ok('exact source pin '+n,sha(body(C/n))==pin)
ok('prior withheld review immutable',sha(body(V/'MANIFEST01.json'))=='42f1debabdf962033c64149f5c90be2e0ef25fc9176ef4330f30633c0c231e0f')
oldmanifest=body(B/'MANIFEST01.json');ok('original incomplete root manifest retained',body(C/'MANIFEST01.json')==oldmanifest)
rows=json.loads(body(C/'MANIFEST02.json'))['entries'];actual={p.relative_to(C).as_posix() for p in C.rglob('*')};declared={r['path'] for r in rows}
ok('complete647/547 typed denominator',len(rows)==647 and sum(r['type']=='file' for r in rows)==547 and len(declared)==647)
ok('manifest includes every actual path',actual==declared|{'MANIFEST02.json'})
for r in rows:
 p=C/r['path'];s=p.lstat();ok('mode '+r['path'],stat.S_IMODE(s.st_mode)==r['mode'])
 if r['type']=='file':ok('body '+r['path'],stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and sha(body(p))==r['sha256'])
 else:ok('directory '+r['path'],r['type']=='directory' and stat.S_ISDIR(s.st_mode))
ok('actual manifest helper recomputes exact full rows',M.collect(C)==rows)
oldpaths={p.relative_to(B/'generated01').as_posix() for p in (B/'generated01').rglob('*')};newpaths={p.relative_to(C/'generated01').as_posix() for p in (C/'generated01').rglob('*')}
ok('entire generated subtree membership unchanged',oldpaths==newpaths)
copied=0
for name in sorted(oldpaths):
 a=B/'generated01'/name;b=C/'generated01'/name
 if a.is_file():copied+=1;ok('inherited generated exact bytes and mode '+name,body(a)==body(b) and stat.S_IMODE(a.stat().st_mode)==stat.S_IMODE(b.stat().st_mode))
ok('510 unchanged generated regular bodies',copied==510)
ok('unresolved cases byte-identical',body(C/'DRAFT_CASES02.json')==body(B/'DRAFT_CASES02.json'))
# Full inverses, constrained to the named new helpers and checks.
inverse=json.loads(body(C/'PREPARE_INVERSE02.json'));raw=body(C/'prepare01.py');ok('prepare sole replacement inverse',raw.count(inverse['new'].encode())==1 and raw.replace(inverse['new'].encode(),inverse['old'].encode())==body(B/'prepare01.py'))
inv=json.loads(body(C/'INVERSE02.json'));text=body(C/'rebind01.py').decode()
for key in ('inserted_helper','inserted_validator'):ok('one inserted block '+key,text.count(inv[key])==1);text=text.replace(inv[key],'',1)
ok('one new validation call',text.count(inv['validation_call'])==1);text=text.replace(inv['validation_call'],'',1)
ok('one root predicate replacement',text.count(inv['replace_new'])==1);text=text.replace(inv['replace_new'],inv['replace_old'],1)
ok('rebind full-byte inverse',text.encode()==body(B/'rebind01.py'))
ok('rebind whole AST inverse',ast.dump(ast.parse(text))==ast.dump(ast.parse(body(B/'rebind01.py'))))
newfunctions={n.name for n in ast.parse(body(C/'prepare01.py')).body if isinstance(n,ast.FunctionDef)}-{n.name for n in ast.parse(body(B/'prepare01.py')).body if isinstance(n,ast.FunctionDef)}
ok('prepare exactly expectations helper added',newfunctions=={'expectations'})
newfunctions={n.name for n in ast.parse(body(C/'rebind01.py')).body if isinstance(n,ast.FunctionDef)}-{n.name for n in ast.parse(body(B/'rebind01.py')).body if isinstance(n,ast.FunctionDef)}
ok('rebind exactly destination and draft helpers added',newfunctions=={'fresh_capsule','validate_draft'})
expected=P.expectations();drafts=json.loads(body(B/'generated01/DRAFT_CASES01.json'));source=json.loads(body(B/'generated01/SOURCE_MAP01.json'));before={r['path']:r['baseline_sha256'] for r in source['entries']};after={r['path']:r['candidate_sha256'] for r in source['entries']}
ok('pinned expectations reconstructed independently',expected=={'baseline':before,'candidate':after,'cases':{case:{'inputs':d['experiment']['inputs'],'outputs':d['experiment']['outputs'],'roles':d['roles']} for case,d in drafts.items()}})
# RR1 old roots accepted, current strict predicate refused without writes.
for root in ('/',str(P.CAP.parent)):
 d,_=oldR.rebind('success',root);ok('RR1 actual baseline RED '+root,d['capsule_root']==root)
 refused('RR1 current GREEN '+root,lambda root=root:R.rebind('success',root))
 witnesses.append({'id':'RR1','root':root,'baseline_accepts':True,'successor_refuses':True})
valid=str(P.CAP.parent.parent/'opaque-review-successor-20261004-01'/'source');ok('valid control unit remains absent',not os.path.lexists(Path(valid).parent))
for root in (str(P.CAP),str(P.CAP/'child'),str(P.CAP.parent/'another-source'),str(P.CAP.parent.parent),'/home/malecada/master_thesis','/home/malecada/master_thesis/onchain-financial-isolation/opaque-review/source','relative',valid+'/',valid.replace('/source','/../source'),str(P.CAP.parent.parent/'keys'/'source')):
 refused('strict root refusal '+root,lambda root=root:R.fresh_capsule(root))
ok('authorized absent sibling accepted without creation',str(R.fresh_capsule(valid))==valid and not Path(valid).parent.exists())
# RR2 exact source membership pins refuse symmetric omissions and alterations.
drop=next(p for p in before if p!=P.CHANGE);x=dict(before);y=dict(after);x.pop(drop);y.pop(drop);oldP.one_change(x,y);refused('RR2 current rejects symmetric missing entry',lambda:P.one_change(x,y));witnesses.append({'id':'RR2','baseline_accepts198':True,'successor_refuses198':True})
P.one_change(before,after)
for kind in ('both_add','changed_baseline','changed_candidate','same_count_swapped_path'):
 x=dict(before);y=dict(after)
 if kind=='both_add':x['opaque.py']='0'*64;y['opaque.py']='0'*64
 elif kind=='changed_baseline':x[drop]='0'*64
 elif kind=='changed_candidate':y[drop]='0'*64
 else:x['opaque.py']=x.pop(drop);y['opaque.py']=y.pop(drop)
 refused('complete pinned maps refuse '+kind,lambda x=x,y=y:P.one_change(x,y))
# Authenticated expectation bytes are not a freely replaceable authority map.
oldread=P.read
def altered_expectation(path):return oldread(path)+b' ' if Path(path)==C/'SOURCE_EXPECTATIONS02.json' else oldread(path)
P.read=altered_expectation
try:refused('changed expectation bytes refused',P.expectations)
finally:P.read=oldread
# RR3 actual old and new rebind under the same owned in-memory mutation.
def with_draft(mod,draft,fn):
 old=mod.read
 def reader(path):return P.encode(draft) if Path(path)==mod.HERE/'generated01/DRAFT_CASES01.json' else old(path)
 mod.read=reader
 try:return fn()
 finally:mod.read=old
mut=copy.deepcopy(drafts);mut['success']['roles']['opaque_extra']=None;mut['success']['experiment']['source_files'].pop(drop)
red,_=with_draft(oldR,mut,lambda:oldR.rebind('success',valid));ok('RR3 baseline RED mutated counts returned',len(red['roles'])==16 and len(red['experiment']['source_files'])==198)
refused('RR3 successor GREEN counts refused',lambda:with_draft(R,mut,lambda:R.rebind('success',valid)));witnesses.append({'id':'RR3','baseline_accepts16roles198pins':True,'successor_refuses':True})
for kind in ('role_missing','role_value','source_missing','input_missing','input_hash','output_missing','output_renamed','future_source','inherited_charter'):
 mut=copy.deepcopy(drafts);d=mut['success']
 if kind=='role_missing':d['roles'].pop('runtime')
 elif kind=='role_value':d['roles']['runtime']['future_reference']={'opaque':True}
 elif kind=='source_missing':d['experiment']['source_files'].pop(drop)
 elif kind=='input_missing':d['experiment']['inputs'].pop('execution_job')
 elif kind=='input_hash':d['experiment']['inputs']['execution_job']['sha256']='0'*64
 elif kind=='output_missing':d['experiment']['outputs'].pop()
 elif kind=='output_renamed':d['experiment']['outputs'][0]='opaque-output.json'
 elif kind=='future_source':d['source_commit']='0'*40
 else:d['experiment']['charter']='opaque-charter'
 refused('draft structure refusal '+kind,lambda mut=mut:with_draft(R,mut,lambda:R.rebind('success',valid)))
# RR5 exact absolute owned file counterexample and extra path mutations.
jobpath=drafts['success']['experiment']['inputs']['execution_job']['path'];opaque=H/'opaque-job.json';opaque.write_bytes(body(B/'generated01/input-draft'/jobpath));mut=copy.deepcopy(drafts);mut['success']['experiment']['inputs']['execution_job']['path']=str(opaque)
red,bodies=with_draft(oldR,mut,lambda:oldR.rebind('success',valid));ok('RR5 baseline RED absolute input returned',str(opaque) in bodies)
refused('RR5 successor GREEN absolute input refused',lambda:with_draft(R,mut,lambda:R.rebind('success',valid)));witnesses.append({'id':'RR5','owned_absolute_input':str(opaque),'baseline_accepts':True,'successor_refuses':True,'undeclared_path_access':False})
for path in ('../opaque-job.json','fixture_inputs/../opaque.json','keys/opaque.json','fixture_inputs/a\\b.json','fixture_inputs/a\0b.json'):
 mut=copy.deepcopy(drafts);mut['success']['experiment']['inputs']['execution_job']['path']=path
 refused('input path refused '+repr(path),lambda mut=mut:with_draft(R,mut,lambda:R.rebind('success',valid)))
# Opaque body hashes are validated before any moved-body output is returned.
oldread=R.read
def damaged_job(path):return oldread(path)+b' ' if Path(path)==C/'generated01/input-draft'/jobpath else oldread(path)
R.read=damaged_job
try:refused('current opaque input hash mutation refused',lambda:R.rebind('success',valid))
finally:R.read=oldread
for case in P.CASES:
 null,b=R.rebind(case);ok(case+' exact unresolved draft',null==json.loads(body(C/'DRAFT_CASES02.json'))[case])
 d,b=R.rebind(case,valid);e,c=R.rebind(case,valid);ok(case+' deterministic valid bind',d==e and b==c and not Path(valid).parent.exists())
 ok(case+' fixed case cardinalities',len(d['experiment']['inputs'])==33 and len(d['roles'])==15 and len(d['experiment']['outputs'])==6 and d['candidate_implementation_count']==199 and d['candidate_package_count']==148)
 ok(case+' unresolved authority remains null',d['fresh_identity'] is None and d['source_commit'] is None and d['registration_commit'] is None and d['cumulative_allocation'] is None and d['case_contract']['experiment_id'] is None)
 refused(case+' release always refused',lambda d=d:P.release(d))
# RR4 actual prior inventory misses 3; successor includes them and old root manifest.
missing=set(json.loads(body(V/'CHECKS02.json'))['partial_helper_observations'][0]['omitted'][i]['path'] for i in range(3))
old_declared={r['path'] for r in json.loads(oldmanifest)['entries']}
ok('RR4 baseline RED exact omissions',missing.isdisjoint(old_declared) and all((B/p).is_file() for p in missing))
ok('RR4 successor GREEN complete copied evidence',missing|{'MANIFEST01.json'}<=declared)
witnesses.append({'id':'RR4','old_missing':sorted(missing),'successor_includes_all':True,'includes_old_root_manifest':True})
tiny=H/'manifest-control';(tiny/'nested').mkdir(parents=True)
for p in (tiny/'MANIFEST01.json',tiny/'MANIFEST02.json',tiny/'nested/MANIFEST01.json',tiny/'nested/MANIFEST02.json'):p.write_bytes(b'{}\n')
collected=M.collect(tiny);ok('new manifest helper excludes exact root only',{r['path'] for r in collected}=={'MANIFEST01.json','nested','nested/MANIFEST01.json','nested/MANIFEST02.json'})
bad=H/'manifest-link-control';bad.mkdir();(bad/'opaque-link').symlink_to(opaque)
refused('manifest helper refuses symlink member',lambda:M.collect(bad))
ok('no numerical or genuine runtime import',not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')) and not any(n.startswith('tradingagents') for n in sys.modules))
out={'schema_version':1,'checks':checks,'count':len(checks),'candidate_pins':pins,'fresh_reviewed_python_sources':['prepare01.py','rebind01.py','manifest02.py'],'fresh_reviewed_metadata':'SOURCE_EXPECTATIONS02.json','candidate_manifest_members':647,'candidate_manifest_files':547,'unchanged_generated_files':510,'RR1_to_RR5':witnesses,'prior_scientific_source_acceptance_repeated':False,'inherited_review_manifest':'42f1debabdf962033c64149f5c90be2e0ef25fc9176ef4330f30633c0c231e0f','valid_opaque_destination':valid,'destination_created':False,'actual_native_execution':False,'actual_claims':False,'numerical_imports':False,'network':False,'release':None}
(H/'CHECKS01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(len(checks),'independent corrected-recipe checks passed')
