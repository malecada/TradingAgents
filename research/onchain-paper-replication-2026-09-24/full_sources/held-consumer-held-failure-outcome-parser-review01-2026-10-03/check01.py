import ast,hashlib,json,os,stat,sys,types,importlib.util,copy
from pathlib import Path
from unittest.mock import patch
R=Path(__file__).resolve().parent;A=R.parent/'held-consumer-held-failure-outcome-parser-preparation01-2026-10-03';H=lambda b:hashlib.sha256(b).hexdigest()
assert H((A/'MANIFEST01.json').read_bytes())=='1ab30d654e1a1897531ea4380ea3c6c98b0a082e533a2bd3a80ca830386bf161'
assert H((A/'held_failure01.py').read_bytes())=='e76bb9fc08168d6dd31d128c91a9aab8f47a3c4deff04752c2ce282173d518d5'
rows=json.loads((A/'MANIFEST01.json').read_bytes())['members'];names=[]
for row in rows:
 p=A/row['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==row['mode']
 if row['type']=='file':assert stat.S_ISREG(s.st_mode) and s.st_nlink==row['links'] and s.st_size==row['bytes'] and H(p.read_bytes())==row['sha256']
 elif row['type']=='directory':assert stat.S_ISDIR(s.st_mode)
 else:assert row['type']=='symlink' and stat.S_ISLNK(s.st_mode) and os.readlink(p)==row['target']
 names.append(row['path'])
actual=[]
for p,ds,fs in os.walk(A,followlinks=False):actual.extend(str((Path(p)/n).relative_to(A)) for n in ds+fs if str((Path(p)/n).relative_to(A))!='MANIFEST01.json')
assert sorted(names)==sorted(actual)
spec=importlib.util.spec_from_file_location('review_failure_parser',A/'held_failure01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
old=(A/'held_outcome.baseline01.py').read_bytes();assert H(old)=='9c6c4ba2fc45495b4f9c02f4c34afa17b9bf9aebaaff7b897a6c8dce165815ec'
oldtree=ast.parse(old);tree=ast.parse((A/'held_failure01.py').read_bytes())
olddefs={n.name:n for n in oldtree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};newdefs={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
for name,node in olddefs.items():
 if name not in ('git','authenticate'):assert ast.dump(node)==ast.dump(newdefs[name]),name
# Exact whole AST inverse of only declared identity/Git/authenticate/new failure helpers.
repaired=copy.deepcopy(tree);repaired.body=[n for n in repaired.body if not (isinstance(n,ast.FunctionDef) and n.name in ('absent','failure_shape','workflow_from_first'))]
for i,n in enumerate(repaired.body):
 if isinstance(n,ast.FunctionDef) and n.name in ('git','authenticate'):repaired.body[i]=copy.deepcopy(olddefs[n.name])
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='IDENTITY' for t in n.targets):n.value=ast.Constant('original-import-held-success-20261003-01')
assert ast.dump(repaired)==ast.dump(oldtree)
q=json.loads((A.parent/'held-consumer-native-release-prerequisite-investigation01-2026-10-03/RELEASE_TEMPLATE01.json').read_bytes())
r=m.Reader(q['capsule_root']);reg=m.sources(r,q);exp=reg['experiments'][m.IDENTITY];assert len(exp['inputs'])==33 and len(exp['outputs'])==6
inputs={name:{'path':v['path'],'sha256':H(m.input_body(r,exp,name))} for name,v in exp['inputs'].items()};r.recheck()
# Source-extract actual FeatureJournal.seal. This is a scalar object/capture seam,
# not a real FeatureJournal construction or capability and it writes no outcome.
cap=Path(q['capsule_root']);jp=cap/'tradingagents/research/onchain_replication/feature_journal.py';jtree=ast.parse(jp.read_bytes());cl=next(n for n in jtree.body if isinstance(n,ast.ClassDef) and n.name=='FeatureJournal');seal=next(n for n in cl.body if isinstance(n,ast.FunctionDef) and n.name=='seal');init=next(n for n in cl.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
assert any(isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='inherited_identity' for t in n.targets) and isinstance(n.value,ast.Constant) and n.value.value is None for n in init.body)
assert any(isinstance(n,ast.Assign) and any(isinstance(t,ast.Attribute) and t.attr=='identity' for t in n.targets) and isinstance(n.value,ast.Name) and n.value.id=='inherited_identity' for n in init.body)
ns={};exec(compile(ast.Module(body=[seal],type_ignores=[]),str(jp),'exec'),ns)
reason='FixturePublicationFailure: registered second-target publication boundary; retain first output; no retry';workflow='a'*64;captured=[]
owner={'experiment':m.IDENTITY,'source_commit':m.SOURCE,'producer':'synthetic-metadata-only','workflow_identity':workflow}
obj=types.SimpleNamespace(directory=R/'never-born-journal',sealed=False,records=[],identity=None,parent=None,owner=owner,required=list(m.TARGETS),_publish=lambda p,v:captured.append(v))
ns['seal'](obj,'failed',reason=reason);journal=captured[0];assert journal['workflow_identity'] is None and journal['owner']['workflow_identity']==workflow
cells=[{'id':'import-target-01','status':'complete','resource_only':True},{'id':'import-target-02','status':'failed','reason':reason,'resource_only':True}]
resource={'schema_version':2,'kind':'original-import-resource-terminal','status':'failed','resource_only':True,'financial_representation_admitted':False,'reason':reason}
try:m.failure_shape(cells,resource,journal,workflow)
except ValueError as e:rejection=str(e)
else:raise AssertionError('expected actual-schema refusal disappeared')
assert rejection=='actual expected failed journal differs'
synthetic_wrong=copy.deepcopy(journal);synthetic_wrong['workflow_identity']=workflow
assert m.failure_shape(cells,resource,synthetic_wrong,workflow)==reason
print('REPRODUCED HFOP1 actual-source seal top-level workflow=null refused; forged hash-valued top-level accepted')
# Corrected Git exact function: earlier fatal must survive all later actions.
cleanup=[]
for late in (OSError('kill failure'),SystemExit('later fatal')):
 first=MemoryError('selector first');calls=[]
 class Stream:
  def close(self):calls.append('close')
  @property
  def closed(self):raise AssertionError('closed property should not be read')
 class Child:
  stdin=Stream();stdout=Stream();stderr=Stream()
  def poll(self):raise AssertionError('external poll should not be read')
  def kill(self):calls.append('kill');raise late
  def wait(self,timeout):calls.append('wait');return -9
 with patch.object(m.subprocess,'Popen',return_value=Child()),patch.object(m.selectors,'DefaultSelector',side_effect=first):
  try:m.git(R,['--version'])
  except BaseException as e:assert e is first
  else:raise AssertionError('missing original fatal')
 assert calls==['kill','wait','close','close','close'];cleanup.append({'later':type(late).__name__,'calls':calls,'first_fatal_preserved':True})
assert m.git(R,['--version'],cap=128).startswith(b'git version ')
# Exact stdin first-close attempt flag: close raises first fatal, never retried.
first=MemoryError('stdin close');calls=[]
class Stream:
 def __init__(self,name):self.name=name
 def fileno(self):return 123
 def close(self):
  calls.append('close-'+self.name)
  if self.name=='stdin':raise first
class Child:
 stdin=Stream('stdin');stdout=Stream('stdout');stderr=Stream('stderr')
 def kill(self):calls.append('kill')
 def wait(self,timeout):calls.append('wait');return -9
child=Child()
class Selector:
 def register(self,*a):pass
 def unregister(self,*a):pass
 def get_map(self):return {'stdin':1}
 def select(self,*a):return [(types.SimpleNamespace(fileobj=child.stdin),1)]
 def close(self):calls.append('selector-close')
with patch.object(m.subprocess,'Popen',return_value=child),patch.object(m.selectors,'DefaultSelector',return_value=Selector()),patch.object(m.os,'set_blocking'):
 try:m.git(R,['--version'])
 except BaseException as e:assert e is first
 else:raise AssertionError('missing first stdin fatal')
assert calls==['close-stdin','kill','wait','close-stdout','close-stderr','selector-close'],calls
# Native pipeline is inspected as AST/text only; no arrays/imports/claims.
source_rows=[]
for name in ('compact_mcm','compact_mcm_publication','resource_fixture','feature_journal','matching_owner'):
 p=cap/'tradingagents/research/onchain_replication'/f'{name}.py';b=p.read_bytes();ast.parse(b);source_rows.append({'path':str(p.relative_to(cap)),'sha256':H(b),'bytes':len(b)})
for raw in (b'{"x":NaN}',b'{"x":Infinity}'):
 try:m.parse(raw)
 except ValueError:pass
 else:raise AssertionError('nonfinite accepted')
assert not any(n in sys.modules for n in ('numpy','torch','scipy'))
readback={'status':'WITHHELD_HFOP1','candidate_sha256':H((A/'held_failure01.py').read_bytes()),'manifest_members':len(rows),'actual_current_committed_bodies':205,'inputs':inputs,'outputs':exp['outputs'],'source_body_readback':source_rows,'actual_seal_extracted_record':journal,'wrong_top_level_fixture_accepted':True,'actual_schema_refusal':rejection,'git_cleanup_checks':cleanup,'stdin_close_once_calls':calls,'actual_authority_or_native_tested':False,'positive_full_authenticate_tested':False,'numerical_imports':False}
(R/'READBACK01.json').write_text(json.dumps(readback,sort_keys=True,indent=2)+'\n')
print('PASS manifest/inverse AST/205 Git +33 opaque inputs/six outputs; corrected Git cleanup and stdin-close controls; WITHHELD HFOP1')
