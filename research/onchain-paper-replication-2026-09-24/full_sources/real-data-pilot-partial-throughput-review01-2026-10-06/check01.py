"""One independent finite seven-graph telemetry control, stdlib scalar fixtures only."""
import hashlib, importlib.util, io, json
from pathlib import Path
from types import SimpleNamespace
H=Path(__file__).resolve().parent
S=H.parent/'real-data-pilot-partial-throughput-telemetry01-2026-10-06'
D=S/'candidate/tradingagents/research/onchain_replication'
spec=importlib.util.spec_from_file_location('partial_progress_review',D/'real_pilot_partial_progress.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
manifest=json.loads((S/'MANIFEST01.json').read_text())
for name,row in manifest['files'].items():
 raw=(S/name).read_bytes();assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
for name,row in json.loads((S/'SOURCE_DELTA01.json').read_text()).items():
 body=(D/name).read_text()
 for change in reversed(row['literal_edits']):assert body.count(change['after'])==1;body=body.replace(change['after'],change['before'])
 assert body==(S/'baseline'/name).read_text() and hashlib.sha256(body.encode()).hexdigest()==row['before_sha256']
clock=SimpleNamespace(now=0);sink=io.StringIO();nodes={format(i,'064x'):100 for i in range(7)}
r=p.MCMProgress({'schema_version':1,'interval_seconds':1,'max_records':1024},nodes,claim_sha256='a'*64,source='b'*40,output=sink,clock=lambda:clock.now)
for key in nodes:
 r.begin(key,100,32)
 for cell in range(150):
  clock.now+=1
  r.poll(SimpleNamespace(state={'started_pairs':cell+1,'completed_pairs':cell,'pending':{'ordinal':cell}}),SimpleNamespace(cells=cell,batches=SimpleNamespace(cells=cell//10*10,chunks=cell//10)))
rows=[json.loads(line) for line in sink.getvalue().splitlines()]
assert len(rows)==1024==r.records and len({x['graph_hash'] for x in rows})==7
assert [x['sequence'] for x in rows]==list(range(1024)) and rows[-1]['last_budget_slot']
assert len(sink.getvalue().encode())<=1024*2048<4*1024**2
assert all(not x['full_mcm_completion_verified_here'] and not x['joint_update_verified_here'] and x['representation_credit']==0 and x['paper_financial_fits']==0 and x['pending_pair'] for x in rows)
class Fatal(BaseException):pass
fatal=Fatal('flush failed after physical write')
class Broken(io.StringIO):
 def flush(self):raise fatal
broken=Broken();r=p.MCMProgress({'schema_version':1,'interval_seconds':1,'max_records':1},nodes,claim_sha256='a'*64,source='b'*40,output=broken,clock=lambda:clock.now)
r.begin(next(iter(nodes)),100,32);log=SimpleNamespace(state={'started_pairs':0,'completed_pairs':0,'pending':None})
try:r.poll(log,None)
except Fatal as actual:assert actual is fatal
else:raise AssertionError('fatal suppressed')
before=broken.getvalue();r.poll(log,None);assert broken.getvalue()==before and r.records==0 and r.last is None and r.error=='Fatal'
print(json.dumps({'passed':True,'sealed_members':len(manifest['files']),'literal_inverses':2,'graphs':7,'records':1024,'total_stdout_bytes':len(sink.getvalue().encode()),'flush_fatal_identity_preserved':True,'failed_flush_not_acknowledged':True,'no_retry_poll_after_error':True,'no_numerical_authority_or_payload':True},indent=2))
