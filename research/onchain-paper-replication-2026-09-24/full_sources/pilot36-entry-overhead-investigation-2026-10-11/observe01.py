"""Scoped metadata snapshot only: no project imports, array reads or process tracing."""
import datetime,hashlib,json,os
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[3]
claim=R/'research_runs/eth-paper-real-data-end-to-end-resource-20261011-36/claim.json'
live=R/'research_artifacts/onchain-paper-replication-2026-09-24/runs/eth-paper-real-data-end-to-end-resource-20261011-36/guard/live.json'
d=json.loads(claim.read_bytes());l=json.loads(live.read_bytes());process=[]
for pid in (131916,132478):
 p=Path('/proc')/str(pid)
 try:
  st=(p/'stat').read_text().split(') ',1)[1].split()
  process.append(dict(pid=pid,comm=(p/'comm').read_text().strip(),io={k:int(v) for k,v in (x.split(':') for x in (p/'io').read_text().splitlines())},stat=dict(state=st[0],utime_ticks=int(st[11]),stime_ticks=int(st[12]),cutime_ticks=int(st[13]),cstime_ticks=int(st[14]),starttime_ticks=int(st[19]))))
 except FileNotFoundError:process.append(dict(pid=pid,ended=True))
rows=sorted((dict(path=k,bytes=(R/k).stat().st_size) for k in d['experiment']['source_files']),key=lambda x:-x['bytes'])
source_names=['admission.py','lifecycle.py','budget_extensions.py']
source_names+=['onchain_replication/'+x+'.py' for x in ('resources','workflow_storage','real_pilot_storage','real_pilot_import_caller','real_pilot_population','matching_owner','original_import_preparation','original_import_stage','imported_authority_lease','imported_authority_interval')]
source={}
for name in source_names:
 q=R/'tradingagents/research'/name;body=q.read_bytes();source[str(q.relative_to(R))]=dict(bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
s=l['storage_observation']
out=dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_anchor=d['source'],clock_ticks_per_second=os.sysconf('SC_CLK_TCK'),processes=process,guard={k:l[k] for k in ('phase','elapsed_seconds','sample_seconds') if k in l},storage={k:s[k] for k in ('elapsed_seconds','entries','directories','regular_files','logical_file_bytes','allocated_bytes')},source_count=len(rows),source_bytes=sum(x['bytes'] for x in rows),source_size_roster=rows,registration_bytes=(R/d['registration']).stat().st_size,registered_input_count=len(d['inputs']),registered_input_total_stat_bytes=sum((R/x['path']).stat().st_size for x in d['inputs'].values()),claim_sha256=hashlib.sha256(claim.read_bytes()).hexdigest(),source_pins=source,qualification='Point observations only; no causal profile, read-input contents, arrays, connection/environment/credential bodies, claims or authority exercise.')
(P/'OBSERVATION01.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ('at','source_anchor','clock_ticks_per_second','processes','guard','storage','source_count','source_bytes','registration_bytes','registered_input_count','registered_input_total_stat_bytes')},indent=2))
