import ast,datetime,difflib,hashlib,json
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'pilot35-preparation-increment-tools-review01-2026-10-11';H=F/'real-data-pilot-full24-preparation-increment01-2026-10-09';N=H/'full35increment30';O=H/'nativeoutcome29';refs={};checks=[]
def read(p):
 b=p.read_bytes();assert len(b)<4*1024**2;refs[str(p.relative_to(R))]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b.decode()
def ck(v,n):
 assert v,n
 checks.append(n)
def obj(p):return json.loads(read(p))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(65536):h.update(b)
 return h.hexdigest()
def write(n,v):
 with (D/n).open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
m=obj(N/'HELPERS_MANIFEST01.json');ck(sha(N/'HELPERS_MANIFEST01.json')=='127ab71e56ec0ce2ad671d02708208a6cb8ade9c18fa2dc301a95a6afc04f621','frozen author manifest')
for n,v in m['files'].items():read(N/n);ck(refs[str((N/n).relative_to(R))]==v,'author body '+n)
oldreview=obj(F/'pilot34-native03-increment-tools-review01-2026-10-11/TOOLS_REVIEW01.json');ck(sha(F/'pilot34-native03-increment-tools-review01-2026-10-11/TOOLS_REVIEW01.json')=='4078c0af021ec8c343b5fce965e3e1c3ce7cdcdaa06aa9aefbf34679b9b7e2a1','accepted29 mechanics review')
texts={};patch=[];inv=[]
for name in ('select','capture','recover'):
 a=read(O/(name+'29.py'));b=read(N/(name+'30.py'));texts[name]=(a,b);ast.parse(b)
 ck(refs[str((O/(name+'29.py')).relative_to(R))]==m['original_helpers'][name+'29.py'],'original '+name)
 patch.extend(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=name+'29.py',tofile=name+'30.py'));inv.extend(difflib.unified_diff(b.splitlines(True),a.splitlines(True),fromfile=name+'30.py',tofile=name+'29.py'))
 if name!='select':
  restored=b.replace('full35-preparation-increment30','native-outcome-increment29').replace('real-pilot-full35-preparation-20261011-30','real-pilot-native03-outcome-20261011-29').replace('full35increment30','nativeoutcome29')
  for stem in ('SELECTION','CAPTURE','GIT_OPERATIONS','FRESH_GIT_RECOVERY'):restored=restored.replace(stem+'30',stem+'29')
  ck(restored==a and ast.dump(ast.parse(restored))==ast.dump(ast.parse(a)),name+' independent literal and AST inverse')
ck(''.join(patch)==read(N/'LITERAL_PATCH01.diff') and ''.join(inv)==read(N/'LITERAL_INVERSE01.diff'),'full three-file bidirectional diffs')
a,b=texts['select'];tree=ast.parse(b)
def val(n):return ast.literal_eval(next(x.value for x in tree.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id==n for t in x.targets)))
ck(a[a.index('reused=[]'):a.index('selection = {')]==b[b.index('reused=[]'):b.index('selection = {')],'unchanged complete typed body/reuse/mode/secret/64MiB/currentness core')
ck(val('scopes')==[] and len(val('owned'))==15 and len(set(val('owned')))==15,'15 public roots zero empirical scopes')
ck(D.name in val('owned') and 'pilot35-binding-release-review01-2026-10-11' in val('owned'),'both final review roots mandatory')
ck('assert root.is_dir() and not root.is_symlink()' in b,'missing scope fails closed')
ck(len(val('prior_generated_names'))==34 and len(set(val('prior_generated_names')))==34,'34 exact prior names')
for n in val('prior_generated_names'):ck((O/n).is_file() and not (O/n).is_symlink(),'prior name exists '+n)
expected={'ADMISSION01.json','admission-stdout01.txt','admission-stderr01.txt','BINDING01.json','RELEASE_REVIEW01.json'}
ck({Path(x).name for x in val('fixed_public_names')[2:]}==expected and 'assert (ROOT/relative).is_file() and not (ROOT/relative).is_symlink(), relative' in b,'five final actual files required no fabricated receipt')
ck(len(val('main_source_pins'))==10 and set(val('main_source_pins'))==set(val('main_source_names')),'exact ten installed paths')
for n,h in val('main_source_pins').items():read(R/n);ck(sha(R/n)==h,'installed '+n)
prior=obj(O/'FRESH_GIT_RECOVERY29.json');ck(sha(O/'FRESH_GIT_RECOVERY29.json')=='d297b714a4cc2cc014a026040d85cd2da537e50b3eab94e273edd08abbc54609' and prior['source']=='f8222a31bab1bc40caebddf9a160eb20fc174e96','actual29 baseline')
ret=obj(F/'pilot34-native03-increment-return-review01-2026-10-11/REVIEW01.json');ck(sha(F/'pilot34-native03-increment-return-review01-2026-10-11/REVIEW01.json')=='a522ca34f5e90c317002d3431875aab2896afeb64b01c9bc710d5454aacaa9e7','accepted returned29')
cap=obj(O/'CAPTURE29.json');sel=obj(O/'SELECTION29.json');ck(sha(O/'CAPTURE29.json')==prior['capture']['sha256'] and sha(O/'SELECTION29.json')==cap['selection']['sha256'],'receipt capture selection joins')
for n in ('native-outcome-increment29.tar','fresh-git-recovered-nativeoutcome29.tar','actual_external_archive_blob_return.stdout'):
 p=O/n;ck(not p.is_symlink() and p.stat().st_size==prior['returned_archive']['bytes'] and sha(p)==prior['returned_archive']['sha256'],'actual alias '+n)
ck("assert excluded=={str((prior.parent/name).relative_to(ROOT)) for name in ('native-outcome-increment29.tar','fresh-git-recovered-nativeoutcome29.tar','actual_external_archive_blob_return.stdout')}" in b,'only three exact aliases')
ck("(HERE/'SELECTION30.json').open('x')" in b and 'selection30 already spent' in b and 'Git delta outside declared full35increment30 scope' in b,'exclusive finite selector')
ck("'prior_inherited_reuse_preserved_by_receipt':prior_selection['exact_unchanged_prior_rows_reused']" in b and "'earlier_inherited_reuse_preserved_by_receipt':prior_selection['prior_inherited_reuse_preserved_by_receipt']" in b,'inherited receipt continuity unchanged')
ck(not (N/'SELECTION30.json').exists() and not (N/'CAPTURE30.json').exists() and not (N/'FRESH_GIT_RECOVERY30.json').exists(),'new operations not executed at review')
ck(not (R.parent/'onchain-pilot-recovery/real-pilot-full35-preparation-20261011-30.git').exists(),'fresh bare destination absent')
commands={x:'.venv/bin/python -B '+str((N/(x+'30.py')).relative_to(R)) for x in ('select','capture','recover')}
write('TOOLS_REVIEW01.json',{'decision':'accepted','scope':'Source and prospective Root command entry only; unchanged29 mechanics with finite fresh35 scope.','checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'references':refs,'commands':commands,'conditions':['Root freezes all 15 complete public roots, accepted final binding/release and all five final E35 files before one-use selection. Presence is not acceptance.','Root executes select then capture; commits and successfully pushes exact archive before recover. Actual returned-byte independent review remains required.','No empirical/private/runtime store coverage, source admission, whole capacity, POSIX restoration or deletion authority.'],'helpers_executed':False})
(D/'REPORT.md').write_text('Accepted source-only increment30 tools and prospective Root commands. '+str(len(checks))+' focused checks passed. Capture/recovery literal and AST inverses reproduce accepted29. Selector preserves typed/mode/hash/currentness and reuse core; exact 15 public roots, ten installed source pins, 34 prior names, five final E35 files, and three authenticated archive aliases. No empirical scope is traversed.\n\nRoot must freeze complete accepted final entry/review bodies before one-use select/capture, then commit/push before fresh recovery. This review does not establish actual capture/recovery or empirical release. No helpers, Git, network or scientific modules were executed.\n')
write('MANIFEST01.json',{'decision':'accepted','files':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(D.iterdir()) if p.is_file()}})
print(json.dumps({'checks':len(checks),'review':sha(D/'TOOLS_REVIEW01.json'),'manifest':sha(D/'MANIFEST01.json')}))
