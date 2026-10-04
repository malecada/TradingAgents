from pathlib import Path
import ast,json,hashlib,stat,os,sys
import npy_bytes02 as N
H=Path(__file__).resolve().parent;A=H.with_name('financial-graph-feature-npy-byte-preparation01-2026-10-04');sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ok(v,n):assert v,n;checks.append(n)
b=(A/'MANIFEST01.json').read_bytes();ok(sha(b)=='c8b40a1d731d8fbef5e7e55712bd87b92454eeda3e4893df03a6764be22987c9','seal');rows=json.loads(b)['members'];ok(len(rows)==187,'187');ok(sorted(['.']+[str(p.relative_to(A)) for p in A.rglob('*') if p!=A/'MANIFEST01.json'])==sorted(r['path'] for r in rows),'complete')
for r in rows:
 p=A/r['path'];s=p.lstat();ok(stat.S_IMODE(s.st_mode)==r['mode'],'mode')
 if r['kind']=='file':b=p.read_bytes();ok(stat.S_ISREG(s.st_mode) and len(b)==r['bytes'] and sha(b)==r['sha256'],'body')
 else:ok(stat.S_ISDIR(s.st_mode),'directory')
pins=json.loads((A/'SOURCE_PINS03.json').read_text());ok(sha(Path(pins['executable']).read_bytes())==pins['executable_sha256'],'interpreter')
for r in pins['sources']:
 p=Path(r['path']);b=p.read_bytes();ok(len(b)==r['bytes'] and sha(b)==r['sha256'] and stat.S_IMODE(p.stat().st_mode)==r['mode'],'source '+p.name)
 if p.name=='_format_impl.py':
  n=next(n for n in ast.parse(b).body if isinstance(n,ast.FunctionDef) and n.name=='_wrap_header');copied=ast.parse((A/'PINNED_WRAP_HEADER03.py').read_bytes());other=next(n for n in copied.body if isinstance(n,ast.FunctionDef) and n.name=='_wrap_header');ok(ast.dump(n)==ast.dump(other),'actual writer AST')
record=json.loads((A/'SAMPLED_BOUNDARY01.json').read_text());ok(len(record['records'])==12 and sum(r['accepted'] for r in record['records'])==5,'5 accepted12')
for r in record['records']:
 p=A/'boundary01'/str(r['case'])/'array-000000.npy';b=p.read_bytes();ok(sha(b)==r['current_sha256']!=r['expected_sha256'],'actual changed file hash');ok(list(N.fingerprint(p.stat()))==r['after'],'current retained fingerprint')
 ok((r['before']==r['after'])==r['accepted'],'exact collision acceptance')
 raw=b'bogus' # no numeric decoding
code=(A/'sampled_boundary01.py').read_text();t=ast.parse(code);ok(not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='utime' for n in ast.walk(t)),'no timestamp reset');ok('original(fd);seen.append(fd)' in code and "if len(seen)==2:" in code,'actual final descriptor close');ok((H/'npy_bytes02.py').read_bytes()==(A/'npy_bytes02.py').read_bytes(),'exact tested source');ok(all(n not in sys.modules for n in ('numpy','torch','pandas','scipy')),'no numerical imports')
(H/'AUTHENTICATION01.json').write_text(json.dumps({'count':len(checks),'checks':checks,'accepted_corrupt':5,'refused_changed_fingerprint':7,'original_case_reexecution':False},indent=2)+'\n');print(len(checks))
