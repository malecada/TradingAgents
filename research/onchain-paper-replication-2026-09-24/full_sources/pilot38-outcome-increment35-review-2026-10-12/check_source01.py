"""Read-only fixed-pin and literal/AST inverse review. Never executes helpers."""
import ast,hashlib,json,stat,difflib
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[3];F=D.parent
C=F/'pilot38-outcome-increment35-candidate-2026-10-12';O=F/'pilot38-corrected-registration-increment34-candidate-2026-10-12'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def pins(seq):
 for x in seq:
  p=R/x['path'];s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and not p.is_symlink() and p.resolve()==p
  assert (s.st_size,sha(p),format(stat.S_IMODE(s.st_mode),'04o'))==(x['bytes'],x['sha256'],x['mode']),x['path']
scope=load(C/'TOOL_SCOPE01.json');tree=ast.parse((C/'select35.py').read_text());a={x.targets[0].id:ast.literal_eval(x.value) for x in tree.body if isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Name) and x.targets[0].id in ('baseline_pins','selected_pins','reused_pins','closed_directory_roster')}
assert a['selected_pins']==scope['selected_pins'] and a['baseline_pins']==scope['baseline'] and a['reused_pins']==scope['exact_prior33_34_rows_reused'] and a['closed_directory_roster']==scope['closed_directory_roster']
for seq in (a['selected_pins'],a['baseline_pins'],a['reused_pins']):pins(seq)
selected={x['path']:x for x in a['selected_pins']};reused={x['path']:x for x in a['reused_pins']};assert len(selected)==len(a['selected_pins']) and not set(selected)&set(reused)
for x in a['closed_directory_roster']:
 p=R/x['path'];assert p.is_dir() and not p.is_symlink() and p.resolve()==p
 assert sorted(z.name for z in p.iterdir())==x['children'] and format(stat.S_IMODE(p.stat().st_mode),'04o')==x['mode']
 for z in p.iterdir():
  if z.is_file():assert str(z.relative_to(R)) in selected
  else:assert str(z.relative_to(R)) in {v['path'] for v in a['closed_directory_roster']}
assert len(scope['opaque36_exact'])==3
for x in scope['opaque36_exact']:assert selected[x['path']]==x
oldprivate=[x for x in selected if x.startswith('research_artifacts/archive-dispatch-ethpilot-20261011-36/')];assert sorted(oldprivate)==sorted(x['path'] for x in scope['opaque36_exact'])
for p in selected:
 assert not set(Path(p).parts)&{'.git','.venv','node_modules','keys','apis'} and Path(p).name not in {'.env','hf_token.txt','connection.json','id_ed25519_storagebox_u676273'}
 assert not p.endswith('.tar') and Path(p).name!='actual_external_archive_blob_return.stdout'
assert not any(p.startswith(str(D.relative_to(R))+'/') for p in selected)
# Frozen prior reviews and complete original38 outcome review bodies are included.
for root in ['pilot38-preparation-outcome-review-2026-10-12','pilot39-successor-preparation-review-2026-10-12']:
 for p in (F/root).iterdir():
  if p.is_file():assert str(p.relative_to(R)) in selected
# Authenticate unchanged33/34 exclusions against their actual returned selection metadata.
H=F/'real-data-pilot-full24-preparation-increment01-2026-10-09';oldrows={}
for d,n in [('full38increment33',33),('full38increment34',34)]:
 p=H/d/f'SELECTION{n}.json'
 if not p.exists():
  matches=list(H.glob(f'*/SELECTION{n}.json'));assert len(matches)==1;p=matches[0]
 for x in load(p)['rows']:oldrows[x['path']]=x
for x in a['reused_pins']:
 y=oldrows[x['path']];assert y['type']=='regular' and all(x[k]==y[k] for k in ('path','bytes','sha256','mode'))
baseline=load(R/a['baseline_pins'][0]['path']);capture=load(R/a['baseline_pins'][2]['path']);assert baseline['capture']['sha256']==a['baseline_pins'][2]['sha256'] and capture['selection']['sha256']==a['baseline_pins'][3]['sha256'] and baseline['no_alternates'] is True
inverse={}
for old,new in [('capture34.py','capture35.py'),('recover34.py','recover35.py')]:
 original=(O/old).read_text();actual=(C/new).read_text();forward=original
 for before,after in scope['capture_recover_aliases']:forward=forward.replace(before,after)
 assert forward==actual,new
 backward=actual
 for before,after in reversed(scope['capture_recover_aliases']):backward=backward.replace(after,before)
 assert backward==original and ast.dump(ast.parse(backward))==ast.dump(ast.parse(original));inverse[new]={'original_sha256':sha(O/old),'candidate_sha256':sha(C/new),'literal_and_ast_inverse':True}
manifest=load(C/'HELPERS_MANIFEST01.json')
for p,h in manifest.items():assert sha(C/Path(p).name)==h,p
# Published unified patches are reconstructed independently for the three source files.
forward='';backward=''
for old,new in [('select34.py','select35.py'),('capture34.py','capture35.py'),('recover34.py','recover35.py')]:
 x=(O/old).read_text().splitlines(True);y=(C/new).read_text().splitlines(True)
 forward+=''.join(difflib.unified_diff(x,y,fromfile=old,tofile=new));backward+=''.join(difflib.unified_diff(y,x,fromfile=new,tofile=old))
# Header spelling is evidence decoration; compare exact hunks after their two file headers.
def hunks(s):return '\n'.join(l for l in s.splitlines() if not l.startswith(('--- ','+++ ')))
assert hunks((C/'LITERAL_PATCH01.diff').read_text())==hunks(forward)
assert hunks((C/'LITERAL_INVERSE01.diff').read_text())==hunks(backward)
assert not (R/scope['deployment_directory']/'SELECTION35.json').exists()
assert not (R.parent/'onchain-pilot-recovery/real-pilot-outcome38-20261012-35.git').exists()
result={'decision':'source_only_accepted','selected_files':len(selected),'selected_bytes':sum(x['bytes'] for x in selected.values()),'reused_files':len(reused),'closed_directory_roster':len(a['closed_directory_roster']),'opaque36_files':len(oldprivate),'opaque_body_handling':'hash/stat only; no decode or referenced target reads','inverse':inverse,'candidate_snapshot':{p.name:sha(p) for p in C.iterdir() if p.is_file()},'actual_capture_or_recovery_accepted':False,'helpers_executed':False}
with (D/'SOURCE_CHECK01.json').open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps(result,sort_keys=True))
