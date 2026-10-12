from pathlib import Path
import ast,json,hashlib,difflib
P=Path(__file__).resolve().parent;R=P.parents[3]
paths={'admission.py':'tradingagents/research/admission.py','lifecycle.py':'tradingagents/research/lifecycle.py','compact_mcm_batched.py':'tradingagents/research/onchain_replication/compact_mcm_batched.py'}
checks=[]
for name,target in paths.items():
 a=(P/('BASELINE_'+name)).read_text();b=(P/name).read_text();compile(b,str(P/name),'exec')
 (P/(name+'.diff')).write_text(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+target,tofile='b/'+target)))
 (P/(name+'.inverse.diff')).write_text(''.join(difflib.unified_diff(b.splitlines(True),a.splitlines(True),fromfile='b/'+target,tofile='a/'+target)))
 checks.append({'target':target,'baseline_sha256':hashlib.sha256(a.encode()).hexdigest(),'candidate_sha256':hashlib.sha256(b.encode()).hexdigest(),'compiled':True})
a=ast.parse((P/'BASELINE_lifecycle.py').read_text());b=ast.parse((P/'lifecycle.py').read_text())
def start(t):return next(n for c in t.body if isinstance(c,ast.ClassDef) and c.name=='ResearchRun' for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='start')
assert ast.dump(start(a))==ast.dump(start(b))
(P/'STATIC01.json').write_text(json.dumps({'source':checks,'start_literal_ast_unchanged':True,'benchmark_executed':False},indent=2)+'\n')
def pin(p):return {'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
m={'status':'UNINSTALLED_EXPLICIT_FRESHNESS_PROTOCOL_CHANGE','targets':checks,'unchanged_verify':pin(R/'tradingagents/research/verify.py'),'files':[pin(p) for p in sorted(P.iterdir()) if p.is_file() and p.name!='SOURCE_MANIFEST01.json']}
(P/'SOURCE_MANIFEST01.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps({'manifest':pin(P/'SOURCE_MANIFEST01.json'),'targets':checks},indent=2))
