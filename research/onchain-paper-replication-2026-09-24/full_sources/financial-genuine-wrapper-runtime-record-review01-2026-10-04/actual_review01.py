"""Metadata-only actual capsule cwd; no admission, execution or outcome read."""
import ast,hashlib,importlib.metadata as M,importlib.util,json,os,stat,sys
from pathlib import Path
D=Path(__file__).resolve().parent;S=D/'source';P=D.parent/'financial-genuine-wrapper-runtime-record-correction01-2026-10-04';CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-native-20261003-01/source');checks=[];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def ok(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
ok('actual cwd/PYTHONPATH',Path.cwd()==CAP and os.environ['PYTHONPATH']==str(CAP) and str(CAP) in sys.path)
def load(name,file):
 spec=importlib.util.spec_from_file_location('tradingagents.research.onchain_replication.'+name,S/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
old=load('independent_old','original.py');new=load('independent_new','candidate.py');mapping=json.loads((S/'runtime_mapping.json').read_bytes())
ok('source pin',sha(S/'candidate.py')=='e2d9208ac51fd5876b63b6a72f734fc4fedd28fa42ac9c7fa1014346feb8404c');ok('manifest pin',sha(P/'MANIFEST01.json')=='f6950286d0bcb6203e374cee446a5d804db7ee8de14896485a4df323877419f0')
m=json.loads((P/'MANIFEST01.json').read_text());ok('complete manifest',{p.relative_to(P).as_posix() for p in P.rglob('*') if p!=P/'MANIFEST01.json'}=={r['path'] for r in m['members']})
for r in m['members']:
 p=P/r['path'];s=p.lstat();good=stat.S_IMODE(s.st_mode)==r['mode']
 if r['kind']=='file':good=good and stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and s.st_nlink==r['nlink'] and sha(p)==r['sha256']
 elif r['kind']=='directory':good=good and stat.S_ISDIR(s.st_mode)
 elif r['kind']=='owned-symlink-control':good=good and stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target']
 else:good=False
 ok('member '+r['path'],good)
recipe=json.loads((S/'SOURCE_RECIPE01.json').read_text());ok('194/one delta',len(recipe['rows'])==recipe['implementation_count']==194 and sum(r['changed'] for r in recipe['rows'])==1)
for r in recipe['rows']:
 p=CAP/r['path'];ok('actual original '+r['path'],sha(p)==r['original_sha256'] and stat.S_IMODE(p.stat().st_mode)==r['mode']);ok('candidate '+r['path'],sha(S/'candidate.py' if r['changed'] else p)==r['candidate_sha256'])
ok('future authority withheld',recipe['release'] is False and all(recipe[k] is None for k in ('future_source','future_registration','future_identity','cumulative_review','full_recovery','independent_source_review')))
source=(S/'candidate.py').read_text();helpers=(S/'record_helpers.py.txt').read_text();replacement=(S/'replacement01.txt').read_text();removed=(S/'removed01.txt').read_text();ok('unique inverse seams',source.count(helpers)==source.count(replacement)==1);inverse=source.replace(helpers,'').replace(replacement,removed);ok('full byte inverse',inverse==(S/'original.py').read_text());ok('full AST inverse',ast.dump(ast.parse(inverse))==ast.dump(ast.parse((S/'original.py').read_text())))
ok('original installed fixture',sha(S/'original.py')==sha(CAP/'tradingagents/research/onchain_replication/financial_wrapper_fixture.py'))
q=json.loads((D.parent/'financial-genuine-wrapper-first-outcome-verifier-preparation01-2026-10-04/REQUEST_FINAL03.json').read_text());ok('unchanged mapping251',mapping==q['runtime_mapping'] and len(mapping['distribution_records'])==251 and sha(S/'runtime_mapping.json')==q['input_hashes']['runtime_mapping'])
error=None
try:old.runtime_check(CAP,mapping)
except old.Unavailable as e:error=str(e)
ok('actual original RED',error=='runtime installed RECORD unavailable');result=new.runtime_check(CAP,mapping);ok('actual GREEN',result=={'qualification':'exact interpreter/lock/version/RECORD mapping; dependency bodies not fully rehashed'})
records=[];ambiguities=[]
for row in mapping['distribution_records']:
 value=new._runtime_record(row);d=M.distribution(row['name']);paths=[str(f) for f in d.files or () if str(f).endswith('.dist-info/RECORD')]
 if len(paths)!=1:ambiguities.append({'name':row['name'],'count':len(paths),'paths':paths,'origin':str(d._path)})
 p=Path(row['record']);ok('actual unchanged runtime '+row['name'],value['record_sha256']==row['record_sha256'] and value['version']==row['version'] and sha(p)==row['record_sha256']);records.append({**value,'record_nlink':p.stat().st_nlink,'metadata_nlink':(p.parent/'METADATA').stat().st_nlink})
ok('setuptools sole17 cause',len(ambiguities)==1 and ambiguities[0]['name']=='setuptools' and ambiguities[0]['count']==17);ok('actual metadata hardlinks permitted',all(r['metadata_nlink']>1 and r['record_nlink']==1 for r in records))
for n,m in list(sys.modules.items()):
 if n in ('tradingagents','tradingagents.research','tradingagents.research.onchain_replication','tradingagents.research.onchain_replication.owned_io'):ok('actual module origin '+n,Path(m.__file__).resolve().is_relative_to(CAP))
ok('no numerical imports',not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')))
(D/'ACTUAL_REVIEW01.json').write_text(json.dumps({'checks':len(checks),'names':checks,'cwd':str(Path.cwd()),'python':sys.executable,'pythonpath':os.environ['PYTHONPATH'],'old_refusal':error,'new_result':result,'original_source':recipe['original_source'],'unchanged_runtime_mapping_sha256':sha(S/'runtime_mapping.json'),'records':records,'inventory_ambiguities':ambiguities,'no_numerical_imports':True,'actual_outcome_inspected':False,'source_adoption':False,'authority':None},indent=2,sort_keys=True)+'\n');print(json.dumps({'checks':len(checks),'records':len(records),'old':error,'ambiguities':[(r['name'],r['count']) for r in ambiguities]}))
