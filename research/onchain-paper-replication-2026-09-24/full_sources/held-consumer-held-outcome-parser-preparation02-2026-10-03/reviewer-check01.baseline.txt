import ast,hashlib,json,os,stat,sys,types,importlib.util
from pathlib import Path
from unittest.mock import patch
R=Path(__file__).resolve().parent
A=R.parent/'held-consumer-held-outcome-parser-preparation01-2026-10-03'
H=lambda x:hashlib.sha256(x).hexdigest()
assert H((A/'MANIFEST01.json').read_bytes())=='45aa34471ffe66b6329609353cbe5491758f78da998baa3595145343daa8f719'
assert H((A/'held_outcome01.py').read_bytes())=='9c6c4ba2fc45495b4f9c02f4c34afa17b9bf9aebaaff7b897a6c8dce165815ec'
manifest=json.loads((A/'MANIFEST01.json').read_bytes());rows=manifest['files'];verified=[]
for row in rows:
 p=A/row['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==row['mode'],row
 if row['type']=='file':
  assert stat.S_ISREG(s.st_mode) and s.st_nlink==row['links'] and s.st_size==row['bytes'] and H(p.read_bytes())==row['sha256'],row
 elif row['type']=='directory':assert stat.S_ISDIR(s.st_mode),row
 elif row['type']=='symlink':assert stat.S_ISLNK(s.st_mode) and os.readlink(p)==row['target'],row
 else:raise AssertionError(row)
 verified.append(row['path'])
actual=[]
for parent,dirs,files in os.walk(A,followlinks=False):
 for name in dirs+files:
  rel=str((Path(parent)/name).relative_to(A))
  if rel!='MANIFEST01.json':actual.append(rel)
assert sorted(actual)==sorted(verified),(set(actual)-set(verified),set(verified)-set(actual))
spec=importlib.util.spec_from_file_location('reviewed_held_parser',A/'held_outcome01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
imports=[]
for node in ast.walk(ast.parse((A/'held_outcome01.py').read_bytes())):
 if isinstance(node,ast.Import):imports.extend(x.name for x in node.names)
 if isinstance(node,ast.ImportFrom):imports.append(node.module)
assert set(imports)<=set('ast hashlib json os selectors stat subprocess sys time pathlib'.split())
# Actual current original Git/source and opaque input bodies only.
template=A.parent/'held-consumer-native-release-prerequisite-investigation01-2026-10-03/RELEASE_TEMPLATE01.json'
q=m.parse(template.read_bytes());reader=m.Reader(q['capsule_root']);reg=m.sources(reader,q);exp=reg['experiments'][m.IDENTITY]
assert len(q['source_files'])==204 and q['registration'] not in q['source_files']
assert len(exp['inputs'])==33 and len(exp['outputs'])==6
inp={k:{'path':v['path'],'sha256':H(m.input_body(reader,exp,k))} for k,v in exp['inputs'].items()}
reader.recheck()
# Actual stdlib helper boundary. Popen/selector only are error-injection stand-ins,
# not real native jobs, authorities, receipts or proof of OS cleanup.
failures=[]
for later in (OSError('poll failed'),SystemExit('later fatal')):
 first=MemoryError('original selector allocation');calls=[]
 class Stream:
  closed=False
  def close(self):calls.append('close');self.closed=True
 class Child:
  stdin=Stream();stdout=Stream();stderr=Stream()
  def poll(self):calls.append('poll');raise later
  def kill(self):calls.append('kill')
  def wait(self,timeout):calls.append('wait');return -9
 with patch.object(m.subprocess,'Popen',return_value=Child()),patch.object(m.selectors,'DefaultSelector',side_effect=first):
  try:m.git(R,['--version'])
  except BaseException as e:observed=e
  else:raise AssertionError('missing failure')
 assert observed is later and calls==['poll']
 failures.append({'prior':'MemoryError','later':type(later).__name__,'observed':type(observed).__name__,'original_fatal_preserved':observed is first,'cleanup_calls':calls})
 print('REPRODUCED HOP1:',failures[-1])
# Positive reader and independent-close control on real owned tiny bytes.
p=R/'tiny';p.mkdir();(p/'body').write_bytes(b'opaque');assert m.Reader(p).body('body',6)==b'opaque'
first=MemoryError('actual reader boundary');close=os.close;seen=[]
def close_later(fd):seen.append(fd);close(fd);raise OSError('after original close')
with patch.object(m.os,'read',side_effect=first),patch.object(m.os,'close',close_later):
 try:m.Reader(p).body('body')
 except BaseException as e:assert e is first
 else:raise AssertionError('missing reader fatal')
assert len(seen)==len(set(seen))==2
# Duplicate JSON and type strictness controls.
try:m.parse(b'{"a":1,"a":2}')
except ValueError:pass
else:raise AssertionError('duplicate accepted')
assert not m.equal({'x':True},{'x':1})
assert not any(n in sys.modules for n in ('numpy','torch','scipy'))
result={'status':'WITHHELD_HOP1','author_manifest_members':len(rows),'author_member_paths':verified,'helper_sha256':H((A/'held_outcome01.py').read_bytes()),'source':m.SOURCE,'source_registration_git_bodies':205,'input_count':len(inp),'inputs':inp,'outputs':exp['outputs'],'actual_current_read_bytes':reader.total,'error_injection_counterexamples':failures,'real_reader_closes_once':2,'numerical_imports':False,'actual_outcome_or_authority_tested':False,'positive_full_authenticate_tested':False}
(R/'READBACK01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print('PASS independent manifest, actual205 Git/current +33 opaque inputs/six outputs, bounded reader controls; WITHHELD two HOP1 counterexamples')
