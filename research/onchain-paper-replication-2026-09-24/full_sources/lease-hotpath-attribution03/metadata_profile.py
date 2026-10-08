import ast,hashlib,json,os,stat,sys,time,statistics
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3]
source=ROOT/'tradingagents/research/onchain_replication'
def definitions(name,names,namespace):
 tree=ast.parse((source/name).read_text());tree.body=[v for v in tree.body if isinstance(v,ast.FunctionDef) and v.name in names];exec(compile(tree,str(source/name),'exec'),namespace)
ns={'json':json};definitions('provenance.py',{'canonical_bytes','thaw'},ns)
canonical=ns['canonical_bytes']
def require(ok,why):
 if not ok:raise ValueError(why)
io={'os':os,'stat':stat,'json':json,'_require':require,'_release':lambda fn:fn(),'META_LIMIT':8192};definitions('score_batches.py',{'_read','_root','_json','_signature'},io)
exp='eth-paper-real-data-end-to-end-resource-20261008-22';workflow='57f440b1f12a5b495f9a346a787441d334b9a8723fb97482adcfb6a04a64fb80';key='0114d61904938208c75497bdabe82c5dae32b7d2110a4e460d1942f84dc473ba'
refs={'receipt':ROOT/'research_artifacts/onchain_representations'/workflow/exp/'compact/dictionary-import/import-complete.json','start':ROOT/'research_artifacts/onchain_compact_mcm'/workflow/exp/('mcm-'+key)/'start.json','job':ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-final22-2026-10-08/inputs02/execution_job.json'}
raw={name:path.read_bytes() for name,path in refs.items()};objects={name:json.loads(v) for name,v in raw.items()};receipt=objects['receipt'];start=objects['start'];job=objects['job'];selected=next(iter(job['payload']['representation_jobs'].values()))
execution={'execution_identity':'0'*64,'import_receipt_sha256':hashlib.sha256(raw['receipt']).hexdigest(),'current':receipt['execution'],'original':receipt['numeric'],'financial_representation_admitted':False}
mapping=selected['descriptor']['resource_graph_inputs'];scope=start['scope']
fixtures={'mapping':mapping,'execution':execution,'scope':scope};pins={name:canonical(obj) for name,obj in fixtures.items()}
local=P/'synthetic-producer';local.mkdir(exist_ok=False);(local/'start.json').write_bytes(raw['start']);fd=os.open(local,os.O_RDONLY|os.O_DIRECTORY)
def target_pins():
 for name,obj in fixtures.items():require(canonical(obj)==pins[name],'changed')
def producer():
 io['_root'](local,fd);require(io['_read'](fd,'start.json',8192)==io['_json'](start),'changed')
def serialization():io['_json'](start)
timings={}
try:
 for name,fn in [('three_target_serializations',target_pins),('producer_root_read_serialize',producer),('producer_serialize_only',serialization)]:
  samples=[]
  for _ in range(5):
   before=time.perf_counter()
   for _ in range(1000):fn()
   samples.append((time.perf_counter()-before)/1000)
  timings[name]={'seconds_per_call':samples,'median_seconds':statistics.median(samples)}
finally:os.close(fd)
record={'status':'completed_metadata_only','metadata_pins':{name:{'path':str(refs[name].relative_to(ROOT)),'bytes':len(value),'sha256':hashlib.sha256(value).hexdigest()} for name,value in raw.items()},'target_canonical_bytes':{name:len(v) for name,v in pins.items()},'source_summary':start['sources'],'timings':timings,'qualification':'Offline exact-shaped metadata fixture. Execution identity placeholder same width; original current/numeric shapes copied from receipt. Producer path is local synthetic path, not real hotpath I/O. Does not measure authority or scheduler; no actual22 throughput attribution.','numerical_imports':any(n in sys.modules for n in ('numpy','scipy','torch')),'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0)}
assert not record['numerical_imports'];(P/'METADATA_PROFILE01.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
