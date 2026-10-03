import json,hashlib,datetime
from pathlib import Path
D=Path(__file__).resolve().parent;C=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source');I='original-import-held-success-20261003-01';J=C/'research_artifacts/onchain_representations/851f1ac5645b8ce7d15d83fc4b545c1d79d8a6817ecb6a802bf0a15247ed4b9c'/I/'compact';G=C/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/I/'guard';refs={}
for p in [J/'dictionary-import/import-complete.json',G/'live.json']:
 assert p.stat().st_size<65536;b=p.read_bytes();x=json.loads(b);refs[str(p.relative_to(C))]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'body':x}
markers=[]
for p in [C/'research_runs'/I/'complete.json',C/'research_runs'/I/'failed.json',G/'final.json']+list(J.glob('mcm-*/complete.json'))+list(J.glob('mcm-*/matching/events-*.bin')):
 s=p.lstat() if p.exists() else None;markers.append({'path':str(p.relative_to(C)),'exists':s is not None,'bytes':s.st_size if s else None,'mtime_ns':s.st_mtime_ns if s else None})
out={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'references':refs,'marker_metadata':markers,'qualification':'Only control JSON bodies and binary event lstat, no binary event read or numerical/array decode.'}
(D/'READBACK03.json').write_text(json.dumps(out,indent=2)+'\n');print(out['utc']);print(markers)
