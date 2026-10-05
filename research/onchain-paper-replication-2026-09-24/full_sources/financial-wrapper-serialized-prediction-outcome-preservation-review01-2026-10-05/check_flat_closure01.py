from pathlib import Path
import json,hashlib,io,gzip,tarfile,stat,collections
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'financial-wrapper-serialized-prediction-outcome-preservation-review01-2026-10-05';Q=F/'financial-wrapper-serialized-prediction-outcome-capture01-2026-10-05';T=F/'financial-wrapper-serialized-prediction-outcome-flat01-2026-10-05';R=F/'financial-wrapper-serialized-prediction-outcome-remote01-2026-10-05';V=F/'financial-wrapper-serialized-prediction-outcome-review01-2026-10-05';B=F/'financial-wrapper-serialized-prediction-binding-review01-2026-10-05';C=F/'heartbeat-root-checkpoint10-2026-10-04'
def h(b):return hashlib.sha256(b).hexdigest()
def ref(p):return {'path':str(p),'sha256':h(p.read_bytes())}
def load(p):return json.loads(p.read_bytes())
def put(n,v):
 p=D/n;b=(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
 with p.open('xb') as f:f.write(b)
 p.chmod(0o444);print(n,h(b))
rec=load(T/'RECOVERY01.json');root=load(T/'ACTUAL_ROOT_EXIT01.json');meta=load(T/'flat/body-metadata.json')
assert ref(T/'RECOVERY01.json')['sha256']==root['recovery_sha256']=='024df55c172622c8a1c78ebcd7cb65246e5a9f95c516e405d43534f4abf1d013'
assert ref(T/'ACTUAL_ROOT_EXIT01.json')['sha256']=='cbf3e3df533552e59c3f81ed0ecf4b9e0d02823ef4fa82f4078a3e808ee1d779' and root['actual_root_exit_code']==0
assert ref(C/'SERIALIZED_PREDICTION_OUTCOME_FLAT01.py')['sha256']==root['source_sha256']==load(D/'FLAT_SOURCE_CHECK01.json')['source']['sha256']
assert ref(T/'flat/body-metadata.json')['sha256']==rec['primitive']['metadata_sha256']=='0e2f58161c36e7e1aaf777171a9589f97ca552c6ad29f517fe03873ac45f4628'
assert meta['manifest']==load(Q/'archive-manifest.json') and meta['archive']==load(Q/'CAPTURE01.json')['archive']
m=meta['manifest'];mapping=meta['flat_members'];assert len(mapping)==len(m['members'])==86
assert {p.name for p in (T/'flat').iterdir()}==set(mapping.values())|{'body-metadata.json'}
bodies={}
for x in m['members']:
 p=T/'flat'/mapping[x['path']];assert p.is_file() and not p.is_symlink();b=p.read_bytes();assert len(b)==x['bytes'] and h(b)==x['sha256'];bodies[x['path']]=b
sink=io.BytesIO()
with gzip.GzipFile(filename='',mode='wb',fileobj=sink,mtime=0) as gz:
 with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tar:
  for r in m['members']:
   t=tarfile.TarInfo(r['path']);t.mode=r['mode'];t.uid=t.gid=0;t.uname=t.gname='';t.mtime=0;t.size=len(bodies[r['path']]);tar.addfile(t,io.BytesIO(bodies[r['path']]))
prefix='research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-outcome-capture01-2026-10-05'
assert sink.getvalue()==(R/'selected'/prefix/'increment.tar.gz').read_bytes() and h(sink.getvalue())==rec['archive_sha256']
c=json.loads(bodies['COMPOSITION01.json']);assert bodies['COMPOSITION01.json']==(Q/'snapshot/COMPOSITION01.json').read_bytes()
assert len(c['materialized'])==85
counts=collections.Counter()
for name,row in c['materialized'].items():
 b=bodies[row['flat']];assert len(b)==row['bytes'] and h(b)==row['sha256'];prefix,n=name.split('/',1);counts[prefix]+=1
 if prefix in ('CAP','Git','Parent'):
  mm=c['capsule'] if prefix=='CAP' else c[prefix]['manifest'];typed={r['path']:r for r in mm['members']}[n];assert typed['kind']=='file' and typed['sha256']==row['sha256'] and typed['bytes']==row['bytes']
assert counts['CAP']==25 and counts['Parent']==15
old=load(F/'financial-wrapper-serialized-prediction-current-capture01-2026-10-05/snapshot/COMPOSITION01.json')
for key in ('capsule','Git','Parent'):
 now=c[key] if key=='capsule' else c[key]['manifest'];before=old[key] if key=='capsule' else old[key]['manifest'];by={r['path']:r for r in now['members']};assert now['root_mode']==before['root_mode']
 for r in before['members']:assert by[r['path']]==r
assert (sum(x['kind']=='file' for x in c['capsule']['members']),len(c['capsule']['members']))==(1213,1563)
assert sum(x['kind']=='file' for x in c['Parent']['manifest']['members'])==28
assert c['Git_object_inventory']==old['Git_object_inventory'] and len(c['Git_object_inventory'])==473
for k in ('basis','final_envelope_basis'):assert ref(Path(c[k]['path']))==c[k]
assert c['basis']['sha256']=='105330459532576a56dc3aee8b035ca411bd058385c2b441f15b705cb431da41' and c['final_envelope_basis']['sha256']=='aab3471c56911bf01aaffc9fdd6d13ab8e4fe8699e65409d38b8d151a13c89b7'
# Typed final Parent supplement is already independently accepted; join its exact two rows again without old body reads.
scope=load(F/'financial-wrapper-serialized-prediction-final-direct02-2026-10-05/FINAL_TYPED_SCOPE01.json')
assert ref(F/'financial-wrapper-serialized-prediction-final-direct02-2026-10-05/FINAL_TYPED_SCOPE01.json')['sha256']=='0ace87f6df2270e8cb7fda94d64d19245a7805df5151b72ab109e3f694f305c0'
assert c['original_parent_exit'] is None and c['actual_Root_exit']==c['actual_child_exit']==0 and c['native_PID_history_complete'] is False
cum=load(V/'CUMULATIVE_PROOF01.json');assert (cum['spent_claims'],cum['complete'],cum['failed'],cum['remaining'],cum['effective_attempt_budget'])==(6,3,3,14,20)
assert h(bodies[c['materialized']['outcome-review/CUMULATIVE_PROOF01.json']['flat']])==ref(V/'CUMULATIVE_PROOF01.json')['sha256']
assert h(bodies[c['materialized']['outcome-review/OUTCOME_CHECK01.json']['flat']])=='ff9ca638eb3ff4a9f153a218594f4d46d45f5d7057365533186ab5e01ed4a364'
ID=c['identity'];claim=c['materialized']['CAP/research_runs/'+ID+'/claim.json']['sha256'];terminal=c['materialized']['CAP/research_runs/'+ID+'/complete.json']['sha256']
assert claim=='ad9e3d8a40caa468a69f77af9488bdf25675d44080736d9adf9ca8048b03068b' and terminal=='f915624f0f328f6bc0cceb299878427f97d864029f2f7d94a7920951c1712e04'
put('FLAT_CHECK01.json',{'schema_version':1,'decision':'accepted-actual86-body-outcome-flat-recovery','recovery':ref(T/'RECOVERY01.json'),'actual_root_exit':ref(T/'ACTUAL_ROOT_EXIT01.json'),'metadata':ref(T/'flat/body-metadata.json'),'composition':{'path':str(T/'flat'/mapping['COMPOSITION01.json']),'sha256':h(bodies['COMPOSITION01.json'])},'regular_bodies_read_once':86,'original_mappings':85,'original_body_counts':dict(counts),'deterministic_PAX_gzip_reencoding_equal_received_archive':True,'previous_typed_manifests_exact_subsets':True,'historical_body_reread':False,'qualification':'All restored opaque body hashes/lengths and original typed mappings joined. Complete composition inherits accepted unchanged byte bases; no POSIX instantiation, runtime package recovery, writer exclusion, tensor interpretation or new scientific result.'})
put('FULL_OUTCOME_RECOVERY_PROOF01.json',{'schema_version':1,'kind':'prediction_outcome_recovery','decision':'accepted-actual-prediction-outcome-byte-recovery','source':c['source'],'identity':ID,'claim_sha256':claim,'terminal_sha256':terminal,'checkpoint_sha256':'50c0807fd0096111ab1503b0235ac0701b88e275052ac7f3db53cd4f1e874dd8','outcome':ref(V/'OUTCOME_CHECK01.json'),'accounting':ref(V/'CUMULATIVE_PROOF01.json'),'capture_check':ref(D/'CAPTURE_CHECK01.json'),'remote_check':ref(D/'REMOTE_CHECK01.json'),'flat_check':ref(D/'FLAT_CHECK01.json'),'accepted_unchanged_basis':c['basis'],'final_envelope_basis':c['final_envelope_basis'],'archive_sha256':rec['archive_sha256'],'composition_sha256':h(bodies['COMPOSITION01.json']),'CAP_regular':1213,'CAP_typed':1563,'Git_regular':sum(x['kind']=='file' for x in c['Git']['manifest']['members']),'Git_logical_objects':473,'Parent_regular':28,'Parent_typed':len(c['Parent']['manifest']['members']),'new_original_bodies':85,'new_original_bytes':2837266,'fresh_restored_regular_bodies':86,'spent':6,'complete':3,'failed':3,'remaining':14,'highest_allowance':20,'paper_financial_fits':0,'optimizer_updates':0,'original_parent_exit':None,'separate_actual_Root_exit':0,'actual_child_exit':0,'native_PID_history_complete':False,'numerical_authority':False,'POSIX_reconstruction':False,'installed_runtime_body_recovery':False,'immutable_writer_exclusion':False,'qualification':'Actual complete declared prediction outcome BYTE scope through pinned previous current/final-envelope recoveries plus this actual remote-selected and freshly restored increment. Saved-model consistency only; no economic accuracy, whole capacity, new claim, refund or historical-failure reclassification. Later local review closure metadata is outside this already recovered increment.'})
