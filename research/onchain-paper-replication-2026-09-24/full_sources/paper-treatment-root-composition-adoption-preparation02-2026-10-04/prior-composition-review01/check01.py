"""Independent source/OID/AST and read-only recipe controls; no numerical imports."""
import ast,copy,hashlib,importlib.util,json,os,stat,subprocess,sys
from pathlib import Path
B=Path(__file__).resolve().parent;P=B.parent/'paper-treatment-root-composition-preparation01-2026-10-04';MAIN=B.parents[3];checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def blob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def ok(v,label):
 if not v:raise AssertionError(label)
 checks.append(label)
def refuse(f,label):
 try:f()
 except (ValueError,OSError,KeyError):checks.append(label);return
 raise AssertionError('accepted '+label)
def git(*args):return subprocess.check_output(['git',*args],cwd=MAIN,timeout=10)
head_start=git('rev-parse','HEAD').decode().strip();manifest=json.loads((P/'MANIFEST01.json').read_text());ok(sha(P/'MANIFEST01.json')=='a81e3f63881deb038d25eb61821874dd89b4ae887936483195ed8be32d5d11b8','frozen complete composition manifest')
ok({e['path'] for e in manifest['entries']}=={p.relative_to(P).as_posix() for p in P.rglob('*')}-{'MANIFEST01.json'},'complete artifact membership')
for e in manifest['entries']:
 p=P/e['path'];s=p.lstat();ok(stat.S_IMODE(s.st_mode)==e['mode'],'member mode')
 if e['type']=='file':ok(stat.S_ISREG(s.st_mode) and s.st_size==e['bytes'] and sha(p)==e['sha256'],'member file hash/extent')
 else:ok(stat.S_ISDIR(s.st_mode),'member directory')
base=json.loads((P/'BASELINE01.json').read_text());closure=json.loads((P/'CLOSURE01.json').read_text());guards=json.loads((P/'SCIENTIFIC_GUARDS01.json').read_text());ok(sha(P/'CLOSURE01.json')=='833b30f52f9365fd681bfaeea8031909fe938db7bb46e33ab9082f8a8d8961b1','exact closure pin')
ok(len(base['sources'])==135 and len(closure['sources'])==138,'exact135→138 closure')
# Read only actual committed tree records for precisely declared source paths.
tree=git('ls-tree','-z',base['head'],'--',*sorted(base['sources']));records={}
for entry in tree.rstrip(b'\0').split(b'\0'):
 mode,kind,rest=entry.split(b' ',2);oid,path=rest.split(b'\t',1);records[path.decode()]={'mode':mode.decode(),'kind':kind.decode(),'oid':oid.decode()}
ok(set(records)==set(base['sources']),'actual pinned Git tree exact declared source subset')
for rel,record in base['sources'].items():
 working=MAIN/rel;snapshot=P/'baseline'/rel;raw=working.read_bytes();s=working.lstat();gitrow=records[rel]
 ok(raw==snapshot.read_bytes() and hashlib.sha256(raw).hexdigest()==record['sha256'] and len(raw)==record['bytes'],'actual baseline working/snapshot/SHA '+rel)
 ok(stat.S_IMODE(s.st_mode)==record['mode'] and gitrow=={'mode':record['git_mode'],'kind':'blob','oid':record['git_blob_oid']} and blob(raw)==record['git_blob_oid'],'actual baseline mode/committed OID '+rel)
for rel,record in closure['sources'].items():
 p=P/'candidate'/rel;raw=p.read_bytes();s=p.lstat();ok(sha(p)==record['sha256'] and len(raw)==record['bytes'] and stat.S_IMODE(s.st_mode)==record['mode'] and blob(raw)==record['git_blob_oid'] and record['git_mode']==('100755' if s.st_mode&0o111 else '100644'),'candidate exact body/mode/computed OID '+rel)
# Actual required_sources function, only stdlib path enumeration; no package import.
for label,root,expected,onchain in [('baseline',MAIN,set(base['sources']),127),('candidate',P/'candidate',set(closure['sources']),130)]:
 job=root/'tradingagents/research/onchain_replication/job.py';tree=ast.parse(job.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='required_sources');ns={'Path':Path,'__file__':str(job)};exec(compile(ast.Module(body=[fn],type_ignores=[]),'exact-required-source-function','exec'),ns)
 ok(ns['required_sources']()==expected and len(list(job.parent.glob('*.py')))==onchain,'actual '+label+' required closure and onchain count')
# Authenticated reviewed producer/consumer origins and exact composition inverse.
changes=json.loads((P/'ADOPTION_DELTAS01.json').read_text());changed={r['path'] for r in changes};selfpath=closure['producer_dynamic_self_path']
for row in changes:
 origin=Path(row['origin']);ok(sha(origin)==row['origin_sha256'],'actual reviewed origin '+row['path'])
 if row['path']!=selfpath:ok((P/'candidate'/row['path']).read_bytes()==origin.read_bytes(),'accepted source body exact '+row['path'])
unchanged=set(base['sources'])-changed;ok(len(unchanged)==131,'131 untouched original bodies')
for rel in unchanged:ok(base['sources'][rel]==closure['sources'][rel] and (P/'baseline'/rel).read_bytes()==(P/'candidate'/rel).read_bytes(),'unchanged source method '+rel)
module=P/'candidate'/selfpath;inv=json.loads((P/'COMPOSITION_INVERSE01.json').read_text());restored=module.read_text()
for e in reversed(inv['edits']):ok(restored.count(e['new'])==1,'unique composition inverse');restored=restored.replace(e['new'],e['old'])
ok(restored==Path(inv['origin']).read_text() and hashlib.sha256(restored.encode()).hexdigest()==inv['origin_sha256'],'complete admission byte inverse')
ok(ast.dump(ast.parse(restored))==ast.dump(ast.parse(Path(inv['origin']).read_text())),'complete admission AST inverse')
for row in json.loads((P/'ORIGIN_REVIEWS01.json').read_text()):ok(sha(Path(row['actual_path']))==row['sha256'],'actual independent prior review '+row['role'])
# Source-map closure is reconstructed from actual source AST rather than declared metadata alone.
astroot=ast.parse(module.read_text());assign=next(n for n in astroot.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PRODUCER_SOURCE_PINS' for t in n.targets));pins=ast.literal_eval(assign.value)
ok(len(pins)==137 and selfpath not in pins and pins==closure['producer_static_pins'],'137 other-source literal pins without self cycle')
joined={**pins,selfpath:sha(module)};ok(joined=={rel:r['sha256'] for rel,r in closure['sources'].items()},'dynamic actual self yields all138 exact final hashes')
# Exact scalar map predicate extracted; no Run/Owner/real claim object constructed.
admit=next(n for n in astroot.body if isinstance(n,ast.FunctionDef) and n.name=='admit_treatment');loop=next(n for n in admit.body if isinstance(n,ast.For));check=next(n for n in loop.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and any(isinstance(a,ast.Constant) and a.value=='unreviewed producer source closure' for a in n.value.args));expr=check.value.args[0]
def accepts(mapping):return eval(compile(ast.Expression(expr),'exact-source-map-predicate','eval'),{'claim':{'experiment':{'source_files':mapping}},'producer_pins':joined})
ok(accepts(joined),'all exact source pins accepted at pure predicate')
for rel in joined:
 missing=dict(joined);missing.pop(rel);ok(not accepts(missing),'missing required source refused '+rel)
 bad=dict(joined);bad[rel]='0'*64;ok(not accepts(bad),'changed required source refused '+rel)
ok(accepts({**joined,'opaque_auxiliary_review.json':'0'*64}),'additional registered auxiliary path not confused with required Python closure')
# Actual self-admission check precedes constructed producer map and all input IO.
selfcheck=next(i for i,n in enumerate(admit.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and any(isinstance(a,ast.Constant) and a.value=='treatment verifier source is not admitted' for a in n.value.args));mapassign=next(i for i,n in enumerate(admit.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='producer_pins' for t in n.targets));ok(selfcheck<mapassign,'actual current self source checked before producer map')
require_src=ast.unparse(admit.body[selfcheck]);ok("run.admission.experiment['source_files'].get(self_relative) == self_hash" in require_src,'genuine admitted self hash equality unchanged semantics')
for rel,record in guards.items():
 raw=(MAIN/rel).read_bytes();committed=git('show',base['head']+':'+rel);ok(raw==committed and hashlib.sha256(raw).hexdigest()==record['sha256'] and len(raw)==record['bytes'] and stat.S_IMODE((MAIN/rel).stat().st_mode)==record['mode'],'actual committed scientific guard '+rel)
ok(guards['research/onchain-paper-replication-2026-09-24/config/model.json']['sha256']=='20f451c08143dd81491b5c9fa0a90243ee6a9363df1fbbfcbd9c45b32f9b054d','model CONFIG20f preserved')
ok(guards['research/onchain-paper-replication-2026-09-24/config/training.json']['sha256']=='d5276b75491e130bd03d43de28120f72dd792e42af4446382a6c127d387b8ec0','training d527 preserved')
# Execute only the read-only recipe. No destination root is created or reserved.
sys.path.insert(0,str(P));spec=importlib.util.spec_from_file_location('review_source_recipe',P/'recipe01.py');recipe=importlib.util.module_from_spec(spec);spec.loader.exec_module(recipe)
target='/home/malecada/master_thesis/onchain-treatment-isolation/review-only-composition-20261004/source';roles={k:None for k in recipe.ROLE_NAMES};before=os.path.lexists(Path(target).parent)
try:plan=recipe.prepare(target,roles);recipe_result={'status':'prepared','copy_count':len(plan['copy'])}
except ValueError as e:plan=None;recipe_result={'status':'refused','reason':str(e)}
ok(not before and not os.path.lexists(Path(target).parent),'read-only recipe creates/reserves no destination')
if plan is not None:
 ok(len(plan['copy'])==138 and len(plan['roles'])==14 and all(v is None for v in plan['roles'].values()),'deterministic complete recipe and null roles')
 ok(all(plan[k] is None for k in ('future_source_commit','future_design_source','future_registration_commit','authority')) and plan['financial_credit']==0,'future authority stays null')
 (B/'ACTUAL_DRAFT_COPY01.json').write_text(json.dumps(plan,sort_keys=True,indent=2)+'\n')
for path in ['/',str(MAIN),str(MAIN.parent),str(recipe.PARENT),str(recipe.PARENT/'../elsewhere/unit/source'),'/home/malecada/master_thesis/onchain-financial-isolation/owned/source',target+'/child',target+'/','relative/unit/source']:
 refuse(lambda path=path:recipe.target_path(path),'unsafe target '+path)
for value in ({},{**roles,'extra':None},{**roles,'registration':'invented'},{**roles,'independent_review':{}}):refuse(lambda value=value:recipe.role_map(value),'roles cannot impersonate authority')
refuse(lambda:recipe.release(),'release always refuses')
for key,value in [('sha256','0'*64),('bytes',0),('mode',0),('git_blob_oid','0'*40),('git_mode','100755')]:
 mapping=copy.deepcopy(closure['sources']);mapping[next(iter(mapping))][key]=value;refuse(lambda mapping=mapping:recipe.verify_source(P/'candidate',mapping),'source map mutation '+key)
for method in ('remove','add'):
 mapping=copy.deepcopy(closure['sources'])
 if method=='remove':mapping.pop(next(iter(mapping)))
 else:mapping['tradingagents/research/onchain_replication/unknown.py']=next(iter(mapping.values()))
 refuse(lambda mapping=mapping:recipe.verify_source(P/'candidate',mapping),'source membership mutation '+method)
# Read-only actual HEAD evidence; strict guard's future rejection is a separate scalar control.
head_end=git('rev-parse','HEAD').decode().strip();changed_names=git('diff','--name-only',base['head'],head_end,'--',*sorted(set(base['sources'])|set(guards))).decode().splitlines();ok(changed_names==[],'no actual baseline source/guard commit delta')
prep=next(n for n in ast.parse((P/'recipe01.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='prepare');headcheck=next(n.value for n in prep.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and any(isinstance(a,ast.Constant) and 'current Main commit differs' in str(a.value) for a in n.value.args));guard=compile(ast.Expression(headcheck),'exact-head-refusal','eval')
refuse(lambda:eval(guard,{'require':recipe.require,'head':'0'*40,'base':base}),'prospective different HEAD refuses even unchanged body closure')
source=module.read_text();ok("raise ValueError('UNADMITTED: exact historical cohort and known_at policy independent admission required')" in source,'fund historical policy remains blocked');ok(not any(k in sys.modules for k in ('numpy','torch','scipy')),'no numerical import')
(B/'CHECKS01.json').write_text(json.dumps({'status':'passed-source-controls','checks':len(checks),'labels':checks,'head_start':head_start,'head_end':head_end,'baseline_head':base['head'],'changed_source_or_guard_paths':changed_names,'actual_recipe':recipe_result,'prospective_head_refusal':'exact guard refuses every different commit, including a hypothetical docs-only commit; no such commit was fabricated','authority':None},sort_keys=True,indent=2)+'\n');print(json.dumps({'checks':len(checks),'heads':[head_start,head_end],'actual_recipe':recipe_result}))
