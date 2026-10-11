from pathlib import Path
import ast,json,hashlib,difflib
H=Path('research/onchain-paper-replication-2026-09-24/full_sources');D=H/'real-data-pilot-full24-preparation-increment01-2026-10-09';A=D/'outcome27';B=D/'postnative28';O=H/'pilot34-postnative-increment-tools-review01-2026-10-11';refs={};checks=[]
def ref(p):
 b=p.read_bytes();r={'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};refs[str(p)]=r;return r
def read(p):ref(p);return json.loads(p.read_text())
def ck(v,n):assert v,n;checks.append(n)
def dump(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
m=read(B/'HELPERS_MANIFEST01.json');ck(refs[str(B/'HELPERS_MANIFEST01.json')]['sha256']=='7fcce3d8362bc16288e5706e9613c16bfa32df0fbf6fb41e44b04b8351b47725','frozen28 manifest')
for n,r in m['files'].items():a=ref(B/n);ck(all(a[k]==r[k] for k in ('sha256','bytes')),'member '+n)
prev=read(A/'HELPERS_MANIFEST01.json');priorreview=ref(H/'pilot34-outcome-increment-tools-review01-2026-10-11/TOOLS_REVIEW01.json');ck(priorreview['sha256']=='a3a3c9df0bb565a1e0f8a142e6defc38130c28e0a5a6002c2c939fcccc6465ab','accepted27 tools reused')
old={};new={};fw='';iv=''
for role in ('select','capture','recover'):
 old[role]=(A/f'{role}27.py').read_text();new[role]=(B/f'{role}28.py').read_text();ck(ref(A/f'{role}27.py')['sha256']==prev['files'][f'{role}27.py']['sha256'],'accepted27 '+role)
 fw+=''.join(difflib.unified_diff(old[role].splitlines(True),new[role].splitlines(True),fromfile=f'{role}27.py',tofile=f'{role}28.py'));iv+=''.join(difflib.unified_diff(new[role].splitlines(True),old[role].splitlines(True),fromfile=f'{role}28.py',tofile=f'{role}27.py'))
ck(fw==(B/'LITERAL_PATCH01.diff').read_text() and iv==(B/'LITERAL_INVERSE01.diff').read_text(),'complete literal patch inverse')
x=new['capture']
for a,b in [('SELECTION28','SELECTION27'),('CAPTURE28','CAPTURE27'),('post-native-increment28','failed-outcome-increment27'),('postnative28 increment','failed34 outcome increment')]:x=x.replace(a,b)
ck(x==old['capture'] and ast.dump(ast.parse(x))==ast.dump(ast.parse(old['capture'])),'capture literal AST inverse')
x=new['recover']
for a,b in [('postnative28','failed34 outcome'),('FRESH_GIT_RECOVERY28','FRESH_GIT_RECOVERY27'),('GIT_OPERATIONS28','GIT_OPERATIONS27'),('CAPTURE28','CAPTURE27')]:
 if a!='postnative28':x=x.replace(a,b)
# Replace exact frozen path and two descriptive phrases only.
x=x.replace('real-pilot-postnative-20261011-28.git','real-pilot-failed34-outcome-20261011-27.git').replace('fresh-git-recovered-postnative28.tar','fresh-git-recovered-outcome27.tar').replace('declared postnative28 public','declared failed34 outcome public').replace('declared postnative28 public increment from','declared failed34 outcome public increment from')
ck(x==old['recover'] and ast.dump(ast.parse(x))==ast.dump(ast.parse(old['recover'])),'recovery literal AST inverse')
s=new['select'];t=ast.parse(s)
def value(n):return ast.literal_eval(next(z.value for z in t.body if isinstance(z,ast.Assign) and any(isinstance(a,ast.Name) and a.id==n for a in z.targets)))
owned=value('owned');ck(len(owned)==14 and len(set(owned))==14 and O.name in owned,'14 distinct public roots including reviewer')
for n in owned:ck((H/n).is_dir() and not (H/n).is_symlink(),'required root '+n)
ck(value('scopes')==[],'no original failed34 or other empirical traversal')
# Exact complete original lower type/mode/hash/before-after handling retained.
start='reused=[]\n';end='selection = {';ck(s[s.index(start):s.index(end)]==old['select'][old['select'].index(start):old['select'].index(end)],'unchanged full reuse and typed capture-selection core')
ck('Git delta outside declared postnative28 scope' in s and 'actual five installed Main changes absent from Git delta' in s and 'prospective native03 identity already attempted' in s,'finite allowlist and preattempt barriers')
ck(all(not n.startswith(('research_artifacts/','research_runs/')) for n in value('main_source_names')+value('fixed_public_names')),'all explicit files public')
r=read(A/'FRESH_GIT_RECOVERY27.json');c=read(A/'CAPTURE27.json');sel=read(A/'SELECTION27.json');returned=read(H/'pilot34-outcome-increment-return-review01-2026-10-11/REVIEW01.json')
ck(refs[str(A/'FRESH_GIT_RECOVERY27.json')]['sha256']=='4bf7836d45312d5a089f94825cf97762c9121cff163d2ddd9bbb889cdaa199ca','exact actual27 receipt');ck(refs[str(H/'pilot34-outcome-increment-return-review01-2026-10-11/REVIEW01.json')]['sha256']=='15f94fd288e1bf89feb911e578829303e9b223be70524047a70053b894381af8','accepted actual27 review')
ck(r['source']==returned['source']=='401089cc3e973c134054fb6ef2e762cb4b152e07','baseline source');ck(refs[str(A/'CAPTURE27.json')]['sha256']==r['capture']['sha256'] and refs[str(A/'SELECTION27.json')]['sha256']==c['selection']['sha256'],'receipt/capture/selection chain');ck(len(sel['exact_unchanged_prior_rows_reused'])==returned['reused_prior26_rows']==67,'67 inherited rows rely on accepted27 not reread')
for p in [Path(c['archive']['path']),Path(r['returned_archive']['path']),A/'actual_external_archive_blob_return.stdout']:
 a=ref(p);ck(a['bytes']==r['returned_archive']['bytes'] and a['sha256']==r['returned_archive']['sha256'],'exact three archive aliases '+p.name)
install=read(H/'pilot34-serializer-postclosure-install01-2026-10-11/INTEGRATION01.json');ck(refs[str(H/'pilot34-serializer-postclosure-install01-2026-10-11/INTEGRATION01.json')]['sha256']=='bbab2992398b06cd8a9fd583f95cc973d7944364279ccfb2bffdf0a3f5b9da59','installed receipt exact')
ck({v['destination']['path'] for v in install['modules']}==set(value('main_source_names')),'exact five installed source roster')
for v in install['modules']:
 q=v['destination'];a=ref(Path(q['path']));ck(a['sha256']==q['sha256'] and a['bytes']==q['bytes'],'actual installed source '+Path(q['path']).name)
ck(not (H/'pilot34-native-owner-qualification03-2026-10-11/attempt01').exists(),'native03 not attempted at review');ck(not (B/'SELECTION28.json').exists(),'selector unused')
result={'decision':'accepted','scope':'Exact prospective postnative28 source/command entry only; helpers not executed.','checks':checks,'references':refs,'owned_public_dirs':owned,'original_failed34_scope_traversal':False,'inherited27_prior26_rows':67,'commands':{role:f'taskset -c 3 nice -n 10 .venv/bin/python -B {B}/{role}28.py' for role in ('select','capture','recover')},'conditions':['Root freezes all14 public roots, current STATE/coordination and five installed source bodies before one selection/capture.','Qualification03 attempt01 must remain absent; actual native03 occurs only after this preparation externally returns and separate entry release.','Commit/push exact archive and selected source before one fresh recover28; independent actual returned-byte review follows.'],'limits':['No helper execution, scientific/native imports, Git or network operations performed.','Existing67 inherited rows reused by accepted27 anchor without historical raw replay.','Literal/AST capture/recovery mechanics unchanged; selector deliberately adds fixed scope/receipt/source/attempt guards.','No actual external-return, POSIX reconstruction, empirical eligibility, runtime completeness or deletion authority.']}
dump(O/'TOOLS_REVIEW01.json',result);(O/'REPORT.md').write_text('Accepted prospective postnative28 source-only tools. Capture/recovery exact literal and AST inverses match27. Selector keeps original typed/mode/hash/before-after and reuse core; finite14-root allowlist, exact actual27 receipt/review, three aliases, five installed source pins and native03 preattempt guard bound new selection. Original failed34 scientific scopes are empty and not traversed.67 inherited prior26 rows rely on already accepted27 review. Root must freeze roster and perform select/capture once, commit/push, recover once, then obtain actual returned-byte acceptance. No helpers executed here.\n');dump(O/'MANIFEST01.json',{'status':'FROZEN_TOOLS_SOURCE_REVIEW','files':{p.name:ref(p) for p in O.iterdir()}});print(json.dumps({'review':ref(O/'TOOLS_REVIEW01.json'),'manifest':ref(O/'MANIFEST01.json'),'checks':len(checks)}))
