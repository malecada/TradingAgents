"""Owned offline Git metadata controls; no scientific imports or execution."""
import ast,copy,hashlib,importlib.util,json,os,stat,subprocess,sys
from pathlib import Path
B=Path(__file__).resolve().parent
sys.path.insert(0,str(B))
spec=importlib.util.spec_from_file_location('recipe_successor02',B/'recipe02.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=[]
def check(name,value,detail=None):
 if not value:raise AssertionError(name)
 checks.append({'name':name,'passed':True,'detail':detail})
def refuse(name,fn):
 try:fn()
 except (ValueError,OSError,subprocess.CalledProcessError) as e:
  check(name,True,{'exception':type(e).__name__,'message':str(e)});return
 raise AssertionError('accepted '+name)
def dump(name,obj):(B/name).write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n')
old=(B/'recipe01.py').read_bytes();new=(B/'recipe02.py').read_bytes();inverse=json.loads((B/'RECIPE_INVERSE01.json').read_text());restored=new.decode()
for e in reversed(inverse['edits']):
 check('unique inverse seam '+str(len(checks)),restored.count(e['new'])==1)
 restored=restored.replace(e['new'],e['old'])
check('full byte inverse',restored.encode()==old)
check('full AST inverse',ast.dump(ast.parse(restored),include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False))
check('inverse original pin',m.sha(old)==inverse['baseline_recipe_sha256'])
check('inverse successor pin',m.sha(new)==inverse['candidate_recipe_sha256'])
base=json.loads((B/'BASELINE01.json').read_text());guards=json.loads((B/'SCIENTIFIC_GUARDS01.json').read_text());closure=json.loads((B/'CLOSURE01.json').read_text())
for subtree,pins in [('baseline',base['sources']),('candidate',closure['sources'])]:
 m.verify_source(B/subtree,pins)
 for rel,pin in pins.items():check(subtree+' exact '+rel,m.sha((B/subtree/rel).read_bytes())==pin['sha256'])
check('candidate137 plus dynamic self',len(closure['producer_static_pins'])==137 and set(closure['producer_static_pins'])|{closure['producer_dynamic_self_path']}==set(closure['sources']))
R=B/'owned-source-git01';R.mkdir()
env={**m._git_environment(),'GIT_AUTHOR_NAME':'Opaque source control','GIT_AUTHOR_EMAIL':'opaque@example.invalid','GIT_COMMITTER_NAME':'Opaque source control','GIT_COMMITTER_EMAIL':'opaque@example.invalid','GIT_AUTHOR_DATE':'2026-10-04T00:00:00Z','GIT_COMMITTER_DATE':'2026-10-04T00:00:00Z'}
def git(*a):return subprocess.check_output(['git',*a],cwd=R,env=env,stderr=subprocess.DEVNULL,timeout=10).decode().strip()
git('init','--template=','-b','fixture')
for rel,pin in base['sources'].items():
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((B/'baseline'/rel).read_bytes());p.chmod(pin['mode'])
for rel,pin in guards.items():
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((m.MAIN/rel).read_bytes());p.chmod(pin['mode']);check('fixture exact guard '+rel,m.sha(p.read_bytes())==pin['sha256'])
git('add','--','.');git('-c','commit.gpgsign=false','commit','-qm','Opaque baseline source fixture')
historical=git('rev-parse','HEAD');fixture=copy.deepcopy(base);fixture.update(root=str(R),head=historical)
check('fixture baseline acceptance',m.verify_current_main(R,fixture,guards)['commit']==historical)
for rel in ('docs/source-fixture-note.md','research/opaque-fixture-evidence.json'):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('opaque metadata only\n')
git('add','--','docs','research');git('-c','commit.gpgsign=false','commit','-qm','Opaque documentation and evidence successor')
metadata_head=git('rev-parse','HEAD')
# Extract the actual original require expression, without its unrestricted Git command.
oldfn=next(n for n in ast.parse(old).body if isinstance(n,ast.FunctionDef) and n.name=='prepare')
oldcheck=next(n for n in oldfn.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and any(isinstance(x,ast.Constant) and x.value=='current Main commit differs; require a fresh explicit source recipe' for x in ast.walk(n)))
oldcode=compile(ast.Module(body=[oldcheck],type_ignores=[]),'<actual-old-head-predicate>','exec')
refuse('RED old strict predicate rejects docs-only successor',lambda:exec(oldcode,{'require':m.require,'head':metadata_head,'base':fixture}))
current=m.verify_current_main(R,fixture,guards)
check('GREEN successor accepts distinct docs-only HEAD',current['commit']==metadata_head and current['historical_baseline_commit']==historical and metadata_head!=historical)
dump('FIXTURE_PROVENANCE01.json',{'kind':'OPAQUE_OWNED_GIT_SOURCE_CONTROL_ONLY','historical_fixture_commit':historical,'metadata_fixture_commit':metadata_head,'verification':current,'genuine_research_source':False,'authority':None})
rel='tradingagents/research/onchain_replication/job.py';p=R/rel;original=p.read_bytes();mode=stat.S_IMODE(p.stat().st_mode)
def verify():return m.verify_current_main(R,fixture,guards)
p.write_bytes(original+b'\n# opaque mutation\n');refuse('working source byte mutation',verify);p.write_bytes(original)
p.chmod(mode^0o100);refuse('working source mode mutation',verify);p.chmod(mode)
p.unlink();refuse('partial missing source',verify);p.mkdir();refuse('directory source replacement',verify);p.rmdir();p.write_bytes(original);p.chmod(mode)
extra=p.parent/'opaque_extra_source.py';extra.write_text('# opaque\n');refuse('additional source member',verify);extra.unlink()
other=R/'opaque-held-source';p.rename(other);p.symlink_to(other);refuse('symlink source replacement',verify);p.unlink();other.rename(p)
other=R/'opaque-hardlink';os.link(p,other);refuse('hardlink source replacement',verify);other.unlink()
parent=p.parent;hold=parent.with_name('opaque-redirect-target');parent.rename(hold);parent.symlink_to(hold,target_is_directory=True);refuse('ancestor source redirect',verify);parent.unlink();hold.rename(parent)
# Every real baseline body is individually changed and refused by its exact byte pin.
for rel,pin in fixture['sources'].items():
 q=R/rel;raw=q.read_bytes();q.write_bytes(raw+b'\n# opaque per-body mutation\n')
 refuse('each source mutation '+rel,verify);q.write_bytes(raw);q.chmod(pin['mode'])
# Commit a changed source while keeping baseline checkout bytes: Git join must refuse.
p.write_bytes(original+b'\n# committed mutation\n');git('add','--',str(p.relative_to(R)));git('-c','commit.gpgsign=false','commit','-qm','Opaque changed source')
changed_head=git('rev-parse','HEAD');p.write_bytes(original);p.chmod(mode);refuse('committed source differs despite restored checkout',verify)
git('restore','--source='+metadata_head,'--staged','--worktree','--',str(p.relative_to(R)));p.chmod(mode);git('-c','commit.gpgsign=false','commit','-qm','Opaque restored source')
check('restored final source tree accepted',verify()['commit']!=metadata_head)
# Exact executable Git mode mismatch, also with baseline checkout restored.
p.chmod(mode|0o100);git('add','--',str(p.relative_to(R)));git('-c','commit.gpgsign=false','commit','-qm','Opaque source executable mode');p.chmod(mode);refuse('committed Git executable mode differs',verify)
git('restore','--source='+metadata_head,'--staged','--worktree','--',str(p.relative_to(R)));p.chmod(mode);git('-c','commit.gpgsign=false','commit','-qm','Opaque restored source mode')
grel=next(iter(guards));gp=R/grel;graw=gp.read_bytes();gp.write_bytes(graw+b'\nopaque\n');refuse('working scientific guard mutation',verify)
git('add','--',grel);git('-c','commit.gpgsign=false','commit','-qm','Opaque committed scientific guard mutation');gp.write_bytes(graw);gp.chmod(guards[grel]['mode']);refuse('committed scientific guard differs despite restored checkout',verify)
git('restore','--source='+metadata_head,'--staged','--worktree','--',grel);gp.chmod(guards[grel]['mode']);git('-c','commit.gpgsign=false','commit','-qm','Opaque restored guard')
outside=R/'outside-implementation-scope.txt';outside.write_text('opaque\n');git('add','--',outside.name);git('-c','commit.gpgsign=false','commit','-qm','Opaque outside-scope change');refuse('non-docs non-evidence commit delta',verify)
outside.unlink();git('add','--',outside.name);git('-c','commit.gpgsign=false','commit','-qm','Opaque remove outside change');check('restored source and scoped final tree accepted',bool(verify()))
# Disjoint commit with identical tree must fail ancestry, using actual commit-tree.
tree=git('rev-parse',metadata_head+'^{tree}');orphan=git('-c','commit.gpgsign=false','commit-tree',tree,'-m','Opaque unrelated history')
git('update-ref','refs/heads/orphan-fixture',orphan);git('checkout','-q','orphan-fixture')
for rel,pin in {**fixture['sources'],**guards}.items():(R/rel).chmod(pin['mode'])
refuse('identical source in unrelated Git history',verify)
git('checkout','-q','fixture')
for rel,pin in {**fixture['sources'],**guards}.items():(R/rel).chmod(pin['mode'])
check('final owned fixture acceptance',bool(verify()))
# Existing target/authority protection is used unchanged, without reserving target.
target=str(m.PARENT/'composition-adoption-review-fixture02'/'source')
for value in ('/',str(m.MAIN),str(m.PARENT/'../source'),str(m.PARENT/'bad_unit'/'source')):refuse('unsafe target '+value,lambda value=value:m.target_path(value))
roles={k:None for k in m.ROLE_NAMES};refuse('missing role',lambda:m.role_map({}));bad=dict(roles);bad['charter']='opaque';refuse('non-null charter role',lambda:m.role_map(bad));refuse('release unavailable',m.release)
actual=m.prepare(target,roles);dump('ACTUAL_READ_ONLY_RECIPE02.json',actual)
check('actual historical provenance retained',actual['original_main']['commit']==base['head'])
check('actual current source verified',actual['current_main']['source_and_scientific_guards_equal'] and actual['current_main']['source_count']==135)
check('actual complete composed closure',len(actual['copy'])==138)
check('no target created',not os.path.lexists(Path(target).parent))
check('no authority',actual['authority'] is None and actual['financial_credit']==0 and all(v is None for v in actual['roles'].values()))
check('fund policy still refused',actual['fund_complete'].startswith('REFUSED'))
dump('CHECKS02.json',{'kind':'IMPLEMENTER_SOURCE_CONTROLS_NOT_INDEPENDENT_REVIEW','count':len(checks),'checks':checks,'recipe_sha256':m.sha(new),'actual_historical_main':base['head'],'actual_current_main':actual['current_main']['commit'],'synthetic_git':{'root':str(R),'historical':historical,'metadata':metadata_head,'changed_source':changed_head,'final':git('rev-parse','HEAD')},'not_tested':['numerical outputs','genuine Run/admission','live installation','runtime capacity','concurrent adversarial mutations','network recovery'],'authority':None})
print(json.dumps({'controls':len(checks),'actual_historical_main':base['head'],'actual_current_main':actual['current_main']['commit'],'recipe_sha256':m.sha(new)}))
