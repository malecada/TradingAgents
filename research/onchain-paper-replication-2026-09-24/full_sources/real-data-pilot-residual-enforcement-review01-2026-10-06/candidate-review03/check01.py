"""Exact successor and corrected boundary only; prior unchanged seams reused."""
from pathlib import Path
import ast,hashlib,json,sys,types
H=Path(__file__).resolve().parent;F=H.parent.parent;C=F/'real-data-pilot-residual-enforcement-candidate02-2026-10-06';P=F/'real-data-pilot-residual-enforcement-candidate01-2026-10-06'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(v,m):
 if not v:raise AssertionError(m)
need(sha(C/'MANIFEST01.json')=='4cc3a56862d88cb884a57eba55a58e518131d622fc0fc91b02f3611d181dc15e','exact manifest')
need(sha(C/'SOURCE_DELTA01.json')=='c3f563b6da144d61f9f4d6dbc24584b2ebc98c1cc0b53e37389f8a1a42df37fd','exact source delta')
for name,h in json.loads((C/'MANIFEST01.json').read_text()).items():need(sha(C/name)==h,'member '+name)
for name in ['job.py','workflow_storage.py','resources.py']:need((C/name).read_bytes()==(P/name).read_bytes(),'unchanged source '+name)
before=ast.parse((P/'real_pilot_storage.py').read_text());after=ast.parse((C/'real_pilot_storage.py').read_text())
strip=lambda tree:ast.dump(ast.Module(body=[n for n in tree.body if not isinstance(n,ast.FunctionDef) or n.name!='residual_check'],type_ignores=[]),include_attributes=False)
need(strip(before)==strip(after),'changes outside residual_check')
pkg=types.ModuleType('review_boundary');pkg.__path__=[str(C)];sys.modules[pkg.__name__]=pkg
for name in ['workflow_storage','real_pilot_storage']:
 m=types.ModuleType(pkg.__name__+'.'+name);m.__package__=pkg.__name__;m.__file__=str(C/(name+'.py'));sys.modules[m.__name__]=m
 exec(compile((C/(name+'.py')).read_bytes(),m.__file__,'exec'),vars(m))
rs=sys.modules[pkg.__name__+'.real_pilot_storage'];ws=sys.modules[pkg.__name__+'.workflow_storage']
r=H/'file-boundary';r.mkdir();paths=rs.residual_paths(r)['training_and_lifecycle']
for p in paths:p.mkdir(parents=True)
for n in range(68):(paths[0]/('file%02d'%n)).write_bytes(b'x')
obs=rs.residual_check(r)['training_and_lifecycle'];need(obs['regular_files']==68 and obs['directories']==3 and obs['logical_file_bytes']==68,'exact file limit accepted')
(paths[1]/'file69').write_bytes(b'x')
try:rs.residual_check(r)
except ws.StorageLimit as e:need(e.observation.get('regular_files')==69,'69 file observation');file_error=str(e)
else:raise AssertionError('69 files accepted')
r=H/'directory-boundary';r.mkdir();paths=rs.residual_paths(r)['training_and_lifecycle']
for p in paths:p.mkdir(parents=True)
for n in range(13):(paths[0]/('dir%02d'%n)).mkdir()
obs2=rs.residual_check(r)['training_and_lifecycle'];need(obs2['directories']==16,'exact directory limit accepted')
(paths[2]/'dir17').mkdir()
try:rs.residual_check(r)
except ws.StorageLimit as e:need(e.observation.get('directories')==17,'17 dir observation');dir_error=str(e)
else:raise AssertionError('17 dirs accepted')
result={'status':'PASS_EXACT_BOUNDARY_SUCCESSOR','unchanged_runtime_files':3,'only_changed_function':'residual_check','file_boundary':{'accepted_files':68,'accepted_directories':3,'accepted_logical_bytes':68,'extra_file_refusal':file_error},'directory_boundary':{'accepted_directories':16,'extra_directory_refusal':dir_error},'fixed_policy':rs.RESIDUAL_POLICY,'prior_native_fatal_evidence_reused':'5b1c45','author_checks_reused':'1cfb7b exit0,13 tests','scientific_or_native_execution':False}
(H/'CHECK01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
