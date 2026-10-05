from pathlib import Path
import ast,json,hashlib,importlib.util,copy,stat,sys
D=Path(__file__).resolve().parent;P=D.parent/'financial-wrapper-continuation-proof-reuse01-2026-10-05';CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');H=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def check(v,label):assert v,label;checks.append(label)
man=json.loads((P/'MANIFEST01.json').read_bytes());expected={r['path'] for r in man['members']};actual={str(p.relative_to(P)) for p in P.rglob('*') if p.name!='MANIFEST01.json'};check(actual==expected,'complete original manifest membership')
for row in man['members']:
 p=P/row['path'];s=p.lstat();check(stat.S_IMODE(s.st_mode)==row['mode'],'original mode '+row['path'])
 if row['kind']=='file':check(stat.S_ISREG(s.st_mode) and s.st_size==row['bytes'] and H(p.read_bytes())==row['sha256'],'original body '+row['path'])
 else:check(stat.S_ISDIR(s.st_mode),'original directory '+row['path'])
s=(P/'preclaim_reuse01.py').read_text();old=(P/'original_preclaim01.py').read_text();iv=json.loads((P/'INVERSE01.json').read_text());check(s.replace(iv['remove_exact_added_block'],'',1).replace(iv['replace']['new'],iv['replace']['old'],1)==old,'complete literal inverse557')
a={n.name:ast.dump(n) for n in ast.parse(old).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};b={n.name:ast.dump(n) for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
for n,v in a.items():
 if n!='_proof_bundle':check(b[n]==v,'unchanged original AST '+n)
sp=importlib.util.spec_from_file_location('independent_reuse_source',P/'preclaim_reuse01.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
check((m.TOTAL,m.FILE,m.SECONDS)==(8388608,4194304,120),'original finite limits')
for key,ref in m.REUSE_ANCHORS.items():check(H(Path(ref['path']).read_bytes())==ref['sha256'],'actual pinned root '+key)
gatepath=CAP/'fixture_inputs/financial_wrapper_compatibility01/gates.json';oldraw=gatepath.read_bytes();oldgate=json.loads(oldraw);gate=json.loads((P/'GATE4_DRAFT01.json').read_bytes());req=json.loads((P/'GATE_REQUIREMENTS01.json').read_bytes());check(H(oldraw)==req['original_gate_preserved']['sha256'] and len(oldgate['experiments'])==13,'original13 gate exact')
shared=set(gate['experiments'])&set(oldgate['experiments']);check(len(shared)==2 and all(gate['experiments'][n]==oldgate['experiments'][n] for n in shared),'two historical definitions unchanged');check(len(set(gate['experiments'])|set(oldgate['experiments']))==15,'15 distinct global definitions')
for n in gate['experiments']:
 seen=set();p=n
 while p is not None:check(p in gate['experiments'] and p not in seen,'closed finite ancestry '+p);seen.add(p);p=gate['experiments'][p]['parent']
for n in shared:check(json.loads((CAP/'research_runs'/n/'claim.json').read_bytes())['experiment']==gate['experiments'][n],'actual original parent definition '+n)
reader=m.Reader();inputs=m.Inputs(CAP,oldgate['experiments'][m.REUSE_REFERENCE]['inputs'],reader);policy=inputs.json(m.ROLE);roots=m._reuse_known_roots(copy.deepcopy(m.REUSE_EXTERNAL),inputs,policy,reader);reader.finish();check(roots['outcome']['epochs']==100,'genuine known-root traversal and finish')
for k in m.REUSE_EXTERNAL:
 bad=copy.deepcopy(m.REUSE_EXTERNAL);bad[k]['sha256']='0'*64
 try:m._reuse_known_roots(bad,inputs,policy,m.Reader())
 except m.Unavailable:checks.append('wrong fixed ref refused '+k)
 else:raise AssertionError('wrong root accepted')
for side in ('historical','target'):
 bad=copy.deepcopy(policy);bad[side]['installed'][next(iter(bad[side]['installed']))]='0'*64
 try:m._reuse_known_roots(m.REUSE_EXTERNAL,inputs,bad,m.Reader())
 except m.Unavailable:checks.append('wrong complete map refused '+side)
 else:raise AssertionError('bad map accepted')
# Independently execute the genuine scalar budget routine, no Admission/Run.
sp=importlib.util.spec_from_file_location('original_budget_scalar',CAP/'tradingagents/research/budget_extensions.py');budget=importlib.util.module_from_spec(sp);sp.loader.exec_module(budget)
claims=[json.loads(p.read_bytes()) for p in sorted((CAP/'research_runs').glob('*/claim.json'))];check(len(claims)==4,'four actual spent claims')
identity=next(n for n in gate['experiments'] if 'continue100' in n);exp=gate['experiments'][identity];family=gate['families'][exp['family']]
def read(ref):
 raw=(CAP/ref['path']).read_bytes();assert H(raw)==ref['sha256'];return raw
check(budget.effective_budget(CAP,gate['program_id'],identity,exp,family,claims,read)==20,'genuine global ceiling20')
downgrade=copy.deepcopy(exp);downgrade.pop('cumulative_budget_extension',None)
try:budget.effective_budget(CAP,gate['program_id'],identity,downgrade,family,claims,read)
except ValueError:checks.append('budget downgrade refused')
else:raise AssertionError('budget reset accepted')
# Independently remeasure the exact declared opaque read set, preserving Reader.finish.
measure=json.loads((P/'MEASURED_READ_SET01.json').read_bytes());r=m.Reader();unique=set()
for row in measure['inventory']:
 check(row['path'] not in unique,'unique measured path');unique.add(row['path']);raw=r.read(Path(row['path']));check((len(raw),H(raw))==(row['bytes'],row['sha256']),'actual measured opaque body')
first=r.total;r.finish();check(first==3956693 and r.total==7913386 and (m.TOTAL-r.total)//2==237611,'exact scenario fullfinish headroom')
check(json.loads((P/'PROOF_REUSE_CONTRACT_DRAFT01.json').read_bytes())['outcome_recovery'] is None,'actual100 recovery still null')
check(not any(n in sys.modules for n in ('numpy','torch','pandas','scipy')),'no numerical imports')
(D/'READBACK01.json').write_text(json.dumps({'checks':checks,'count':len(checks),'source':H(s.encode()),'original_gate':H(oldraw),'actual_claims':len(claims),'ceiling':20,'measured_unique_paths':len(unique),'measured_finish_bytes':r.total,'unique_headroom':237611,'actual_admission':False,'actual_outcome_recovery':None},indent=2)+'\n');print(json.dumps({'checks':len(checks),'bytes':r.total,'headroom':237611}))
