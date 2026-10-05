import ast,hashlib,json
from pathlib import Path
root=Path.cwd();f=root/'research/onchain-paper-replication-2026-09-24/full_sources';old=f/'financial-wrapper-continuation-refused-outcome-remote01-2026-10-05';new=f/'financial-wrapper-continuation-successor-current-remote01-2026-10-05';assert not new.exists();new.mkdir(mode=0o700)
cap=f/'financial-wrapper-continuation-successor-current-capture01-2026-10-05';r=f/'financial-wrapper-continuation-successor-review01-2026-10-05';c=f/'heartbeat-root-checkpoint10-2026-10-04';paths=[cap/'CAPTURE01.json',cap/'archive-manifest.json',cap/'increment.tar.gz',r/'CURRENT_CAPTURE_CHECK01.json',r/'CUMULATIVE_PROOF01.json',r/'SOURCE_INPUT_RUNTIME_PROOF01.json',c/'SUCCESSOR_CURRENT_CAPTURE01.py'];rows=[]
for p in sorted(paths):
 b=p.read_bytes();assert len(b)<=4*1024**2;rows.append({'path':p.relative_to(root).as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
required={r['path']:{k:r[k] for k in ('bytes','sha256')} for r in rows};text=(old/'recover01.py').read_text();line=next(x for x in text.splitlines() if x.startswith('REQUIRED = '));assert text.count(line)==1;text=text.replace(line,'REQUIRED = '+repr(required)).replace('FINAL_POPULATION_COUNT = 8','FINAL_POPULATION_COUNT = 7').replace('fresh-refused-continuation-outcome01.git','fresh-successor-current01.git');start=text.index("'qualification': 'Actual terminal not-admitted continuation launch:");end=text.index("'}",start);text=text[:start]+"'qualification': 'Seven exact archive, capture source and independent changed-scope review bodies for complete current successor CAP839/1068 by actual9 changed regulars and accepted830 unchanged basis, complete current physical Git438 logical objects and12 Parent bodies plus review/Root scope. This is actual byte recovery only, not final released envelope recovery, POSIX reconstruction, installed runtime package bodies, numerical capacity or paper fit. Original receiver guards unchanged.'"+text[end+1:];ast.parse(text)
for name,b in {'recover01.py':text.encode(),'watch01.py':(old/'watch01.py').read_bytes()}.items():
 with (new/name).open('xb') as w:w.write(b)
(new/'utilities').mkdir(mode=0o700)
with (new/'utilities/owned_io.py').open('xb') as w:w.write((old/'utilities/owned_io.py').read_bytes())
with (new/'SELECTED_ROWS_DRAFT01.json').open('x') as w:json.dump({'status':'remote-commit-binding-pending','rows':rows},w,sort_keys=True,indent=2);w.write('\n')
print(json.dumps({'receiver':str(new),'source_sha256':hashlib.sha256(text.encode()).hexdigest(),'selected_count':7,'selected_bytes':sum(r['bytes'] for r in rows)}))
