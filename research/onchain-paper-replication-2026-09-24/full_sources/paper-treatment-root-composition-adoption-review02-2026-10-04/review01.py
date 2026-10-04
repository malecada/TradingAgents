import ast,copy,hashlib,importlib.util,json,os,shutil,stat,subprocess,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent;SRC=OUT.parent/'paper-treatment-root-composition-adoption-preparation02-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def check(name,value):
 assert value,name;checks.append({'name':name,'accepted':True})
def refuse(name,f):
 try:f()
 except (ValueError,OSError,subprocess.CalledProcessError) as e:checks.append({'name':name,'refusal':type(e).__name__,'reason':str(e)})
 else:raise AssertionError('unexpected acceptance '+name)
def save(name,value):(OUT/name).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
manifest=json.loads((SRC/'MANIFEST02.json').read_bytes());check('exact frozen manifest',sha((SRC/'MANIFEST02.json').read_bytes())=='68dec93c6d7ef4a2280832c363175601845f674291188b641a0dd2940c391570');expected={r['path']:r for r in manifest['entries']};actual={str(p.relative_to(SRC))for p in SRC.rglob('*') if p!=SRC/'MANIFEST02.json'};check('complete source evidence membership',actual==set(expected))
for name,row in expected.items():
 p=SRC/name;s=p.lstat();check('mode '+name,stat.S_IMODE(s.st_mode)==row['mode'])
 if row['type']=='file':check('raw '+name,stat.S_ISREG(s.st_mode) and s.st_size==row['bytes'] and sha(p.read_bytes())==row['sha256'])
 else:check('directory '+name,stat.S_ISDIR(s.st_mode))
new=(SRC/'recipe02.py').read_bytes();check('exact candidate body',sha(new)=='0501559e520a49605a21724b71e2c409b20302e0b790c3abc11518c75ec739b1');old=(SRC/'recipe01.py').read_bytes();inverse=json.loads((SRC/'RECIPE_INVERSE01.json').read_bytes());restored=new.decode()
for edit in reversed(inverse['edits']):check('unique inverse '+str(len(checks)),restored.count(edit['new'])==1);restored=restored.replace(edit['new'],edit['old'])
check('exact byte inverse to original acceptance',restored.encode()==old);check('exact AST inverse',ast.dump(ast.parse(restored),include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False))
sys.path.insert(0,str(SRC));spec=importlib.util.spec_from_file_location('reviewed_adoption',SRC/'recipe02.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
base=json.loads((SRC/'BASELINE01.json').read_bytes());closure=json.loads((SRC/'CLOSURE01.json').read_bytes());guards=json.loads((SRC/'SCIENTIFIC_GUARDS01.json').read_bytes());check('135-138-137self-seven',len(base['sources'])==135 and len(closure['sources'])==138 and len(closure['producer_static_pins'])==137 and len(guards)==7)
for sub,pins in [('baseline',base['sources']),('candidate',closure['sources'])]:M.verify_source(SRC/sub,pins);check('inherited '+sub+' closure preserved',True)
roles={n:None for n in M.ROLE_NAMES};target=str(M.PARENT/'independent-adoption-review02-never-created'/'source');before=os.path.lexists(Path(target).parent);result=M.prepare(target,roles);save('ACTUAL_READ_ONLY_PREPARE01.json',result);check('no creation',not before and not os.path.lexists(Path(target).parent));check('exact current historical distinction',result['original_main']['commit']==base['head'] and result['current_main']['historical_baseline_commit']==base['head'] and result['current_main']['commit']!=base['head']);check('roles-unreleased-fund',len(result['roles'])==14 and all(v is None for v in result['roles'].values()) and result['authority']is None and result['fund_complete'].startswith('REFUSED') and result['financial_credit']==0)
# Independent scalar source predicates: no fixture Git writes.
for n in M.ROLE_NAMES:
 q=dict(roles);q[n]='unsupported';refuse('every nonnull authority '+n,lambda:M.role_map(q));q=dict(roles);q.pop(n);refuse('every missing authority '+n,lambda:M.role_map(q))
for t in ('/',str(M.MAIN),str(M.PARENT),str(M.PARENT/'bad_unit'/'source'),str(M.PARENT/'okay-unit'/'../source'),str(M.PARENT/'okay-unit'/'source'/'child')):refuse('fresh target boundary '+t,lambda:M.target_path(t))
refuse('release always refuses',M.release)
# New own plain source copies; only the independent review owns mutations.
plain=OUT/'owned-source-controls';shutil.copytree(SRC/'baseline',plain)
for rel,pin in guards.items():p=plain/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((M.MAIN/rel).read_bytes());p.chmod(pin['mode'])
for rel,pin in base['sources'].items():(plain/rel).chmod(pin['mode'])
for rel in base['sources']:
 p=plain/rel;raw=p.read_bytes();p.write_bytes(raw+b'\n# independent opaque alteration\n');refuse('every exact body '+rel,lambda:M.verify_source(plain,base['sources']));p.write_bytes(raw)
for rel in base['sources']:
 p=plain/rel;mode=stat.S_IMODE(p.stat().st_mode);p.chmod(mode^0o100);refuse('every exact mode '+rel,lambda:M.verify_source(plain,base['sources']));p.chmod(mode)
# Exercise actual existing immutable Git objects without touching their refs/index.
facts=json.loads((SRC/'CHECKS02.json').read_bytes())['synthetic_git'];repo=Path(facts['root']);B=copy.deepcopy(base);B['root']=str(plain);B['head']=facts['historical'];git_bytes=M._git_bytes;git_status=M._git_status;selected=facts['metadata']
def frozen_git(root,*args):return (selected+'\n').encode() if args==('rev-parse','--verify','HEAD') else git_bytes(repo,*args)
M._git_bytes=frozen_git;M._git_status=lambda root,*args:git_status(repo,*args)
try:
 current=M.verify_current_main(plain,B,guards);check('actual committed docs endpoint accepted',current['commit']==selected)
 # Old exact predicate extracted from frozen predecessor, not reimplemented.
 oldfn=next(x for x in ast.parse(old).body if isinstance(x,ast.FunctionDef)and x.name=='prepare');statement=next(x for x in oldfn.body if isinstance(x,ast.Expr)and any(isinstance(z,ast.Constant)and z.value=='current Main commit differs; require a fresh explicit source recipe'for z in ast.walk(x)));refuse('exact original RED on docs successor',lambda:exec(compile(ast.Module(body=[statement],type_ignores=[]),'<old actual predicate>','exec'),{'require':M.require,'head':selected,'base':B}))
 selected=facts['changed_source'];refuse('changed committed body despite restored plain checkout',lambda:M.verify_current_main(plain,B,guards))
 # Enumerate genuine retained fixture commits read-only and exercise all seams.
 raw=git_bytes(repo,'log','--all','--format=%H%x09%s').decode();commits=[x.split('\t',1)for x in raw.splitlines()];save('IMMUTABLE_FIXTURE_COMMITS01.json',commits)
 tests={'Opaque source executable mode':'committed executable mode','Opaque committed scientific guard mutation':'committed scientific guard','Opaque outside-scope change':'outside docs/evidence endpoint','Opaque unrelated history':'unrelated identical-source ancestry'}
 for title,label in tests.items():
  found=[oid for oid,msg in commits if msg==title];check('one retained witness '+label,len(found)==1);selected=found[0];refuse(label,lambda:M.verify_current_main(plain,B,guards))
 selected=facts['final'];check('restored endpoint accepted with intermediate changes qualified',M.verify_current_main(plain,B,guards)['commit']==selected)
finally:M._git_bytes=git_bytes;M._git_status=git_status
check('no numerical imports',not any(n in sys.modules for n in ('numpy','torch','pandas','scipy')));save('CHECKS01.json',{'checks':checks,'count':len(checks),'actual_main':result['current_main'],'scope':'NEW02 predicate/provenance seam and inherited byte preservation only','no_git_mutations':True,'authority':None});print(json.dumps({'checks':len(checks),'actual_current_main':result['current_main']['commit'],'candidate_sha256':sha(new)}))
