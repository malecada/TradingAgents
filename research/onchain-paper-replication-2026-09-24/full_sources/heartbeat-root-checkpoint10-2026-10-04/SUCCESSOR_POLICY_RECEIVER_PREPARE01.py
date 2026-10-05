import ast,hashlib,json
from pathlib import Path
root=Path.cwd();f=root/'research/onchain-paper-replication-2026-09-24/full_sources';c=f/'heartbeat-root-checkpoint10-2026-10-04';old=f/'financial-wrapper-continuation-refused-outcome-remote01-2026-10-05';new=f/'financial-wrapper-continuation-successor-policy-remote01-2026-10-05';assert not new.exists();new.mkdir(mode=0o700)
paths=[]
a=f/'financial-wrapper-continuation-successor-source01-2026-10-05';d=f/'financial-wrapper-continuation-successor-preparation02-2026-10-05';r=f/'financial-wrapper-continuation-successor-review01-2026-10-05'
for base,names in ((a,('operational_source_compatibility.py','financial_wrapper_fixture.py','preclaim01.py','MANIFEST01.json')),(d,('successor.json','source_closure.json','continue-plan.json','refusal.json')),(r,('SOURCE_REVIEW_PROOF01.json','SOURCE_CHECK01.json','SOURCE_SEAL_CHECK01.json','REPORT01.md'))):paths.extend(base/name for name in names)
rows=[]
for p in sorted(paths):
 b=p.read_bytes();rows.append({'path':p.relative_to(root).as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
assert len(rows)==12
required={r['path']:{k:r[k] for k in ('bytes','sha256')} for r in rows}
text=(old/'recover01.py').read_text();line=next(x for x in text.splitlines() if x.startswith('REQUIRED = '));assert text.count(line)==1;text=text.replace(line,'REQUIRED = '+repr(required))
assert text.count('FINAL_POPULATION_COUNT = 8')==1;text=text.replace('FINAL_POPULATION_COUNT = 8','FINAL_POPULATION_COUNT = 12')
assert text.count('fresh-refused-continuation-outcome01.git')==1;text=text.replace('fresh-refused-continuation-outcome01.git','fresh-successor-policy01.git')
start=text.index("'qualification': 'Actual terminal not-admitted continuation launch:");end=text.index("'}",start)
text=text[:start]+"'qualification': 'Exact twelve new source, policy, opaque refusal, plan and independent source-review bodies recovered from actual remote Git. Historical accepted baseline evidence reused; no complete current capsule/caller/gate recovery, runtime package bodies, lifecycle claim, numerical capacity, paper-fit or wire-volume credit. Original receiver guards and observed controls unchanged.'"+text[end+1:]
ast.parse(text)
for name,b in {'recover01.py':text.encode(),'watch01.py':(old/'watch01.py').read_bytes()}.items():
 with (new/name).open('xb') as w:w.write(b)
(new/'utilities').mkdir(mode=0o700)
with (new/'utilities/owned_io.py').open('xb') as w:w.write((old/'utilities/owned_io.py').read_bytes())
with (new/'SELECTED_ROWS_DRAFT01.json').open('x') as w:json.dump({'status':'remote-commit-binding-pending','rows':rows},w,sort_keys=True,indent=2);w.write('\n')
with (c/'SUCCESSOR_POLICY_RECEIVER_PREPARATION01.json').open('x') as w:json.dump({'schema_version':1,'new_root':str(new),'selected_count':12,'selected_bytes':sum(r['bytes'] for r in rows),'source_sha256':hashlib.sha256(text.encode()).hexdigest(),'prior_source_sha256':hashlib.sha256((old/'recover01.py').read_bytes()).hexdigest(),'literal_changes':4,'guards_changed':False,'executed':False},w,sort_keys=True,indent=2);w.write('\n')
print(json.dumps({'selected_count':12,'selected_bytes':sum(r['bytes'] for r in rows),'receiver':str(new)}))
