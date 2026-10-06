from pathlib import Path
import ast,hashlib,json,os,sys,types
D=Path(__file__).resolve().parent;F=D.parent;M=F.parents[2];C=F/'real-data-pilot-chunk-durability-candidate01-2026-10-06';P=M/'tradingagents/research/onchain_replication'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(C/'MANIFEST01.json').startswith('3247ff77')
for name,pin in json.loads((C/'MANIFEST01.json').read_bytes()).items():
 if name.startswith(('candidate/','tiny/','tiny02/')) and not name.startswith('candidate/'):continue # reuse accepted tiny evidence; do not replay/read fixture bodies
 assert sha(C/name)==pin
for name,v in json.loads((C/'INVERSE01.json').read_bytes()).items():
 old=(M/v['baseline']).read_text();assert hashlib.sha256(old.encode()).hexdigest()==v['before_sha256'];new=(C/'candidate'/name).read_text();x=old
 for e in v['literal_edits']:assert e['before'] in x;x=x.replace(e['before'],e['after'])
 assert x==new and sha(C/'candidate'/name)==v['after_sha256'];ast.parse(new)
 # Forward exact reconstruction already establishes no undisclosed delta.
pkg=types.ModuleType('independent_durability');pkg.__path__=[];sys.modules[pkg.__name__]=pkg
loaded=[]
def load(name,p,no_numpy=False):
 t=ast.parse(p.read_text())
 if no_numpy:t.body=[n for n in t.body if not isinstance(n,ast.Import) or all(x.name!='numpy' for x in n.names)]
 m=types.ModuleType(pkg.__name__+'.'+name);m.__package__=pkg.__name__;sys.modules[m.__name__]=m;setattr(pkg,name,m);exec(compile(t,str(p),'exec'),m.__dict__);loaded.append(str(p.relative_to(M)));return m
load('owned_io',P/'owned_io.py');io=load('score_batches',P/'score_batches.py',True);helper=load('chunk_durability',C/'candidate/chunk_durability.py');pair=load('compact_pair_log',C/'candidate/compact_pair_log.py')
base=D/'auto-threshold-fsync-failure';assert not base.exists()
policy={'schema_version':1,'scope':'resource-pilot-only','pair_records':2,'tail_records':2,'max_interval_ms':60000};scope={x:'1'*64 for x in pair.FIELDS};limits={'chunk_events':4,'max_events':8,'max_pairs':4,'max_logical_bytes':8*pair.RECORD_BYTES+2*io.META_LIMIT}
log=pair.PairLog(base,owner='2'*64,scope=scope,limits=limits,max_iterations=3,lease=lambda:None);log.enable_durability(policy);log.begin('3'*64,'4'*64);assert log.events==1 and log.durability_status['durable_records']==0
fd=log.chunk_fd;rootfd=log.fd;original=os.fsync;primary=OSError('independent auto-threshold fsync failure')
def failing(target):
 if target==fd:raise primary
 return original(target)
os.fsync=failing
try:
 try:log.complete(.5,'temperature_complete',1)
 except OSError as e:assert e is primary
 else:raise AssertionError('automatic failed flush accepted')
 assert log.events==2 and log.poisoned and log.durability_status['acknowledged_records']==2 and log.durability_status['durable_records']==0
finally:os.fsync=original
try:log.finish()
except BaseException:pass
else:raise AssertionError('poisoned log produced success')
assert not (base/'terminal.json').exists()
try:log.close()
except BaseException as e:close_error=type(e).__name__
else:close_error=None
assert log.closed
for f in (fd,rootfd):
 try:os.fstat(f)
 except OSError:pass
 else:raise AssertionError('descriptor leaked')
assert (base/'events-000000000000.bin').stat().st_size==2*pair.RECORD_BYTES and (base/'start.json').exists()
assert not {'numpy','torch','scipy','pyarrow'}&set(sys.modules)
result={'status':'passed-source-only','six_exact_source_reconstructions':True,'automatic_threshold_failure_original_error_retained':True,'raw_failed_partial_bytes_retained':2*pair.RECORD_BYTES,'durable_watermark_unchanged':0,'acknowledged_not_crash_durable':2,'successful_terminal_absent':True,'all_descriptors_closed':True,'close_failure_type':close_error,'source_modules_loaded':loaded,'not_genuine_owner_fixture':True,'numerical_or_native_network_execution':False,'scope':'One changed-seam synthetic failure; reuse author successful byte/default parity and boundary checks, not scientific equivalence.'}
(D/'DURABILITY_CHECK01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result))
