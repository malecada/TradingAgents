import ast,pathlib,stat,hashlib,json,tempfile
from unittest.mock import patch
D=pathlib.Path(__file__).parent;P=D.parent/'neural-cold-feature-handoff-held-consumer-wiring-preparation01-2026-10-03';t=ast.parse((P/'held_score_consumer.py').read_text());nodes=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in {'require','_body'}];ns={'stat':stat};exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-consumer-body','exec'),ns)
fatal=MemoryError('actual body read sentinel');ordinary=OSError('owned close sentinel');events=[]
class Stream:
 def __enter__(self):events.append('enter');return self
 def read(self):events.append('read');raise fatal
 def __exit__(self,*args):events.append('close');raise ordinary
with tempfile.TemporaryDirectory(dir=D) as tmp:
 p=pathlib.Path(tmp)/'source.py';p.write_bytes(b'x')
 with patch.object(pathlib.Path,'open',return_value=Stream()):
  try:ns['_body'](p)
  except BaseException as e:observed=e
  else:raise AssertionError('unexpected success')
assert observed is fatal, 'HCW1: original first MemoryError masked by later close OSError'
print(json.dumps({'finding':'HCW1','actual_extracted_function':'_body','first_fatal':'MemoryError','observed_primary':'OSError','first_fatal_preserved':False,'events':events,'qualification':'Actual source _body calls unchanged Path.read_bytes; synthetic file-context read/close failure injection, not genuine authority/native execution.'},indent=2))
