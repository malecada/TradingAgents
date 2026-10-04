import ast,hashlib,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-native-20261003-01/source')
assert Path.cwd()==CAP and str(CAP) in sys.path

def load(path,label):
 spec=importlib.util.spec_from_file_location('tradingagents.research.onchain_replication.'+label,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
old=load(HERE/'original.py','record_original');new=load(HERE/'candidate.py','record_candidate');mapping=json.loads((HERE/'runtime_mapping.json').read_bytes());failure=None
try:old.runtime_check(CAP,mapping)
except old.Unavailable as e:failure=str(e)
assert failure=='runtime installed RECORD unavailable'
result=new.runtime_check(CAP,mapping);assert result=={'qualification':'exact interpreter/lock/version/RECORD mapping; dependency bodies not fully rehashed'}
rows=[new._runtime_record(row) for row in mapping['distribution_records']]
assert len(rows)==251 and not any(n in sys.modules for n in ('numpy','torch','scipy','pandas'))
source=(HERE/'candidate.py').read_text();inverse=source.replace((HERE/'record_helpers.py.txt').read_text(),'').replace((HERE/'replacement01.txt').read_text(),(HERE/'removed01.txt').read_text());assert inverse==(HERE/'original.py').read_text();assert ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ast.parse((HERE/'original.py').read_text()),include_attributes=False)
print(json.dumps({'cwd':str(Path.cwd()),'sys_path':sys.path,'python':sys.executable,'old_actual_refusal':failure,'new_actual_runtime_result':result,'unchanged_runtime_mapping_sha256':hashlib.sha256((HERE/'runtime_mapping.json').read_bytes()).hexdigest(),'checked_records':rows,'byte_inverse':True,'AST_inverse':True,'no_numeric_imports':True},sort_keys=True,indent=2))
