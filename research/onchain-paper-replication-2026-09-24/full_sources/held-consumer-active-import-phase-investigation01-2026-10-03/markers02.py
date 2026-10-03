import json,os,hashlib,datetime
from pathlib import Path
D=Path(__file__).resolve().parent;C=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source');ID='original-import-held-success-20261003-01';rows=[]
roots=[C/'research_artifacts/onchain_representations/851f1ac5645b8ce7d15d83fc4b545c1d79d8a6817ecb6a802bf0a15247ed4b9c'/ID,C/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/ID,C/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/ID]
for root in roots:
 for folder,dirs,files in os.walk(root,followlinks=False):
  dirs.sort();files.sort()
  if len(Path(folder).relative_to(root).parts)>=4:dirs[:]=[]
  for p in [Path(folder)]+[Path(folder)/n for n in files]:
   s=p.lstat();rows.append(dict(path=str(p.relative_to(C)),size=s.st_size,mode=s.st_mode,mtime_ns=s.st_mtime_ns))
   if len(rows)>200:raise ValueError('metadata census cap')
source_names=['tradingagents/research/admission.py','tradingagents/research/verify.py','tradingagents/research/lifecycle.py','tradingagents/research/budget_extensions.py']+['tradingagents/research/onchain_replication/'+n+'.py' for n in ['job','resource_fixture','resource_binding','matching_owner','original_dictionary','original_import_preparation','original_import_stage','environment']]
sources={n:hashlib.sha256((C/n).read_bytes()).hexdigest() for n in source_names}
out=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),members=rows,source_hashes=sources)
(D/'MARKERS02.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
