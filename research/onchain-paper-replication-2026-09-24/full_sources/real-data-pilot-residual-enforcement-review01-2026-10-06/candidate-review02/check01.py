"""Independent candidate identity and one uncovered exact-threshold counterexample."""
from pathlib import Path
import difflib,hashlib,json,sys,types
H=Path(__file__).resolve().parent;F=H.parent.parent;ROOT=F.parents[2]
C=F/'real-data-pilot-residual-enforcement-candidate01-2026-10-06'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(v,m):
 if not v:raise AssertionError(m)
need(sha(C/'MANIFEST01.json')=='0593536e54b519b5b22b2dcb9c5382353a61ac01e518c3eb3c59893ca97cc150','candidate identity')
need(sha(C/'SOURCE_DELTA02.json')=='7c8f670f276ae9ea6c0994dc003d297edd794c4531338dfaf1137d01b44a152f','source delta')
for name,h in json.loads((C/'MANIFEST01.json').read_text()).items():need(sha(C/name)==h,'member '+name)
for name,item in json.loads((C/'SOURCE_DELTA02.json').read_text()).items():
 before=ROOT/item['baseline_path'];after=C/name
 need(sha(before)==item['baseline_sha256'] and sha(after)==item['candidate_sha256'],'source pair')
 diff=''.join(difflib.unified_diff(before.read_text().splitlines(True),after.read_text().splitlines(True),fromfile=item['baseline_path'],tofile='candidate/'+name))
 need(diff==(C/(name+'.patch')).read_text(),'patch exactness')
 compile(after.read_bytes(),str(after),'exec')
def audit(event,args):
 if event.startswith(('socket.','subprocess.')):raise RuntimeError('offline only')
 if event=='import' and args[0].split('.')[0] in {'numpy','torch','scipy','pandas'}:raise RuntimeError('no numerical imports')
sys.addaudithook(audit)
prefix='residual_independent';pkg=types.ModuleType(prefix);pkg.__path__=[str(C)];sys.modules[prefix]=pkg
for name in ['workflow_storage','real_pilot_storage']:
 m=types.ModuleType(prefix+'.'+name);m.__package__=prefix;m.__file__=str(C/(name+'.py'));sys.modules[m.__name__]=m
 exec(compile((C/(name+'.py')).read_bytes(),m.__file__,'exec'),vars(m))
rs=sys.modules[prefix+'.real_pilot_storage'];ws=sys.modules[prefix+'.workflow_storage']
root=H/'exact-boundary';root.mkdir();paths=rs.residual_paths(root)['training_and_lifecycle']
paths[0].mkdir(parents=True);paths[1].mkdir(parents=True)
for n in range(68):(paths[0]/('file%02d'%n)).write_bytes(b'x')
try:rs.residual_check(root)
except ws.StorageLimit as e:
 counter={'observed_error':str(e),'observation':e.observation}
else:raise AssertionError('expected candidate counterexample no longer reproduces')
# Independent actual current totals over only the selected roots, not their ancestors.
files=[p for base in paths if base.exists() for p in base.rglob('*') if p.is_file()]
dirs=sum(1+sum(p.is_dir() for p in base.rglob('*')) for base in paths if base.exists())
actual={'logical_bytes':sum(p.stat().st_size for p in files),'regular_files':len(files),'directories':dirs,'max_file_bytes':max(p.stat().st_size for p in files)}
policy=rs.RESIDUAL_POLICY['training_and_lifecycle'];need(all(actual[k]<=policy[k] for k in actual),'fixture exceeds actual domain policy')
need(counter['observed_error']=='storage residual reserved slots limit exceeded','unexpected failure')
result={'status':'REPRODUCED_FALSE_REFUSAL_AT_EXACT_FILE_THRESHOLD','candidate_sha256':sha(C/'MANIFEST01.json'),'actual_totals':actual,'unchanged_policy':policy,'error':counter,'cause':'remaining regular_files=0 is rejected before scanning an existing empty second root; empty roots need zero remaining regular files','numerical_imports':False,'source_pairs':4}
(H/'CHECK01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
