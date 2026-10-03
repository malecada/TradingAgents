"""Full actual tar body, excluding all network/Git/collector invocation code."""
import ast,copy,hashlib,io,json,os,stat,tarfile
from pathlib import Path,PurePosixPath
HERE=Path(__file__).resolve().parent;MAIN=HERE.parents[3];OUT=HERE.parent/'neural-cold-feature-handoff-comparison-outcome01-2026-10-03';source=OUT/'recover_comparison_outcome03.py';body=source.read_bytes();assert hashlib.sha256(body).hexdigest()=='b723ffc77b340cc054a3f4a9d2ab5812777d125d1432b73fefdb5320e98a3f9f';tree=ast.parse(body)
retained=json.loads((OUT/'OUTCOME_RETENTION01.json').read_bytes());archive=OUT/'comparison-outcome01.tar.gz';assert hashlib.sha256(archive.read_bytes()).hexdigest()==retained['archive_sha256'];out=HERE/'actual-loop01';out.mkdir();bindingpath=out/'selected'/str((OUT/'COLLECTION_ROOT_MODE_BINDING01.json').relative_to(MAIN));bindingpath.parent.mkdir(parents=True);bindingpath.write_bytes((OUT/'COLLECTION_ROOT_MODE_BINDING01.json').read_bytes())
start=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.For) and ast.unparse(n.iter)=="retained['members']");end=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='capsule' for x in n.targets))
funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('digest','put')]
ns={'Path':Path,'PurePosixPath':PurePosixPath,'hashlib':hashlib,'os':os,'stat':stat,'json':json,'tarfile':tarfile,'MAX':4194304,'retained':retained,'archive':archive,'out':out,'HERE':OUT,'ROOT':MAIN}
exec(compile(ast.Module(body=funcs+tree.body[start:end],type_ignores=[]),str(source),'exec'),ns)
assert len(ns['actual'])==2313 and ns['files']==1764 and ns['directories']==549 and ns['logical']==9963221 and stat.S_IMODE(ns['owned'].stat().st_mode)==509
schema=tree.body[start];results=[]
base={'kind':'file','mode':384,'path':'x','bytes':3,'sha256':hashlib.sha256(b'abc').hexdigest()}
for case in ('validfile','validdir','directory_bytes','missing_hash','boolbytes','boolmode','escape','dot','wronghash','negativebytes'):
 row=copy.deepcopy(base)
 if case in ('validdir','directory_bytes'):row={'kind':'directory','mode':448,'path':'d'}
 if case=='directory_bytes':row['bytes']=0
 elif case=='missing_hash':del row['sha256']
 elif case=='boolbytes':row['bytes']=True
 elif case=='boolmode':row['mode']=True
 elif case=='escape':row['path']='../x'
 elif case=='dot':row['path']='.'
 elif case=='wronghash':row['sha256']='z'*64
 elif case=='negativebytes':row['bytes']=-1
 context={'retained':{'members':[row]},'MAX':4194304,'PurePosixPath':PurePosixPath}
 try:exec(compile(ast.Module(body=[schema],type_ignores=[]),str(source),'exec'),context)
 except (AssertionError,KeyError):assert case not in ('validfile','validdir');results.append([case,'refused'])
 else:assert case in ('validfile','validdir');results.append([case,'accepted'])
loop=next(n for n in tree.body if isinstance(n,ast.With) and 'tarfile.open' in ast.unparse(n.items[0].context_expr))
for case in ('file','directory','wrongmode','wronghash','wrongextent','link','duplicate'):
 caseout=HERE/('tar-case-'+case);caseout.mkdir();dest=caseout/'owned';dest.mkdir();tarpath=caseout/'tiny.tar.gz';row=copy.deepcopy(base);name='x'
 if case=='directory':name='d';row={'kind':'directory','mode':448,'path':'d'}
 with tarfile.open(tarpath,'w:gz') as tf:
  member=tarfile.TarInfo('collection/'+name);member.mode=row['mode'];data=b'abc'
  if case=='directory':member.type=tarfile.DIRTYPE
  elif case=='link':member.type=tarfile.SYMTYPE;member.linkname='other'
  else:member.size=3
  if case=='wrongmode':member.mode=448
  if case=='wrongextent':member.size=2;data=b'ab'
  tf.addfile(member,io.BytesIO(data) if member.isfile() else None)
  if case=='duplicate':tf.addfile(member,io.BytesIO(data))
 if case=='wronghash':row['sha256']='0'*64
 context={'archive':tarpath,'tarfile':tarfile,'PurePosixPath':PurePosixPath,'owned':dest,'expected':{name:row},'seen':set(),'files':0,'directories':0,'logical':0,'MAX':4194304,'os':os,'hashlib':hashlib}
 exec(compile(ast.Module(body=funcs,type_ignores=[]),str(source),'exec'),context)
 try:exec(compile(ast.Module(body=[loop],type_ignores=[]),str(source),'exec'),context)
 except AssertionError:assert case not in ('file','directory');results.append([case,'refused'])
 else:assert case in ('file','directory');results.append([case,'accepted'])
missing=HERE.parent/'neural-cold-feature-handoff-comparison-outcome-recovery-source-review02-2026-10-03/MANIFEST01.json';assert not missing.exists()
r={'schema_version':1,'full_actual_tar_and_rewalk':'PASS','members':2313,'files':1764,'directories':549,'logical_bytes':9963221,'root_mode':509,'schema_and_tar_cases':results,'source03_release':'WITHHELD_RCO3_WRONG_SELECTED_MANIFEST_PATH','missing_path':str(missing),'actual_required_path':str(missing.with_name('MANIFEST02.json')),'network_or_numeric_import_or_full_helper_invocation':False}
(HERE/'READBACK03.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,sort_keys=True))
