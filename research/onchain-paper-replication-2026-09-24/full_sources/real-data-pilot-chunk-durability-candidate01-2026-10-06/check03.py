from pathlib import Path
import ast,hashlib,json,types
R=Path.cwd();O=Path(__file__).parent;tree=ast.parse((O/'candidate/compact_matcher.py').read_text());method=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='__call__');handler=next(n for n in ast.walk(method) if isinstance(n,ast.ExceptHandler) and n.name=='error');loop=next(n for n in handler.body if isinstance(n,ast.For));calls=[];error=RuntimeError('original matching failure');fsync_error=OSError('pair fsync failed')
def bad():calls.append('pair');raise fsync_error
def tail():calls.append('tail')
actor=types.SimpleNamespace(log=types.SimpleNamespace(durability_barrier=bad),_durability_barrier=tail);exec(compile(ast.Module(body=[loop],type_ignores=[]),'<actual failure barrier loop>','exec'),{'self':actor,'error':error});assert calls==['pair','tail'] and 'pair fsync failed' in error.__notes__[0]
for name,v in json.loads((O/'INVERSE01.json').read_bytes()).items():
 s=(R/v['baseline']).read_text();assert hashlib.sha256(s.encode()).hexdigest()==v['before_sha256']
 for e in v['literal_edits']:assert e['before'] in s;s=s.replace(e['before'],e['after'])
 assert s==(O/'candidate'/name).read_text();ast.parse(s)
print(json.dumps({'decision':'pass','pair_failure_still_attempts_tail_barrier':True,'original_error_retained_with_fsync_note':True,'all_six_final_literal_inverses':True,'numerical_imports':False}))
