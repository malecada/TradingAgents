"""Exact successor inverse and owned typed source inventory, stdlib only."""
import ast,hashlib,json,stat
from pathlib import Path
P=Path(__file__).resolve().parent;OLD=P.parent/'financial-genuine-wrapper-preparation01-2026-10-03'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,v):(P/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
a=(OLD/'financial_wrapper_fixture.py').read_text();b=(P/'financial_wrapper_fixture.py').read_text();reverse=b
for row in reversed(json.loads((P/'fixture_adaptations02.json').read_bytes())):assert reverse.count(row['after'])==1;reverse=reverse.replace(row['after'],row['before'])
assert reverse==a
old={n.name:n for n in ast.parse(a).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};new={n.name:n for n in ast.parse(b).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
unchanged=[name for name,node in old.items() if ast.dump(node)==ast.dump(new[name])]
assert set(old)-set(unchanged)=={'_parent','execute'}
copies={n:sha(P/n) for n in ('job.py','job.baseline.py','replay.py','model.json','training.json','adaptations.json','prepare_templates.py','check_source01.py')}
for n,h in copies.items():assert sha(OLD/n)==h
candidate={q.name:sha(q) for q in (P/'candidate02').glob('*.py')};assert len(candidate)==7
for n,h in candidate.items():assert sha(OLD/'candidate02'/n)==h
before=json.loads((OLD/'SOURCE_CLOSURE01.json').read_bytes())['installed'];after=json.loads((P/'SOURCE_CLOSURE01.json').read_bytes())['installed'];assert set(before)==set(after) and len(after)==194
changed=[n for n in before if before[n]!=after[n]];assert changed==['tradingagents/research/onchain_replication/financial_wrapper_fixture.py']
put('INVERSE02.json',{'schema_version':1,'complete_text_inverse':True,'old_source_sha256':sha(OLD/'financial_wrapper_fixture.py'),'new_source_sha256':sha(P/'financial_wrapper_fixture.py'),'unchanged_ast':unchanged,'changed_original_functions':['_parent','execute'],'unchanged_companion_bodies':copies,'seven_candidate02_bodies':candidate,'source_targets':194,'changed_source_targets':changed})
put('PINS02.json',{'source_sha256':sha(P/'financial_wrapper_fixture.py'),'protocol_sha256':sha(P/'PROTOCOL02.md'),'inverse_sha256':sha(P/'INVERSE02.json'),'prior_pins_sha256':sha(P/'PRIOR_PINS02.json'),'witness_sha256':sha(P/'WITNESS_RESULTS02.json'),'closure_sha256':sha(P/'SOURCE_CLOSURE01.json')})
rows=[]
for p in sorted(P.rglob('*')):
 if p.name in ('MANIFEST02.json','MANIFEST02.sha256'):continue
 s=p.lstat();r={'path':str(p.relative_to(P)),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISDIR(s.st_mode):r['kind']='directory'
 elif stat.S_ISREG(s.st_mode):r.update(kind='file',bytes=s.st_size,sha256=sha(p))
 else:raise ValueError('unexpected source fixture special file')
 rows.append(r)
put('MANIFEST02.json',{'schema_version':1,'status':'source correction only; independent review pending','members':rows});pin=sha(P/'MANIFEST02.json');(P/'MANIFEST02.sha256').write_text(pin+'  MANIFEST02.json\n')
print(json.dumps({'members':len(rows),'manifest_sha256':pin,'source_sha256':sha(P/'financial_wrapper_fixture.py'),'protocol_sha256':sha(P/'PROTOCOL02.md'),'inverse':True}))
