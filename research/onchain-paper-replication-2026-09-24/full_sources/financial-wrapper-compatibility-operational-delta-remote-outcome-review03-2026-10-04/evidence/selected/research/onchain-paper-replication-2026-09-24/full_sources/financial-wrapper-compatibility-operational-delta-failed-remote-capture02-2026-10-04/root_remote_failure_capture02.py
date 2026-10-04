from pathlib import Path
import json,hashlib,os,sys,datetime
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';S=F/'financial-wrapper-compatibility-operational-delta-root-remote02-2026-10-04';V=F/'financial-wrapper-compatibility-operational-delta-root-remote-failed-outcome-review02-2026-10-04';D=F/'financial-wrapper-compatibility-operational-delta-failed-remote-capture02-2026-10-04';D.mkdir(mode=0o700);snap=D/'snapshot';snap.mkdir(mode=0o700)
U=F/'financial-wrapper-complete100-failed-root-remote03-2026-10-04/utilities';sys.path.insert(0,str(U));import recovery_pax01 as P
def h(b):return hashlib.sha256(b).hexdigest()
assert h((V/'MACHINE01.json').read_bytes())=='ef32053eee187849418a90faa4fb3891a3c23fd5611f88312e419381fd758e86';scope=json.loads((V/'FAILED_ROOT_SCOPE01.json').read_bytes());assert h((V/'FAILED_ROOT_SCOPE01.json').read_bytes())=='7995f07ef7660d77a40fed81f9a7fc14054a5d1b609b6e81002332c8033b6a4b';assert len(scope['members'])==43
origin=[]
for row in scope['members']:
 if row['path']=='.':assert row['kind']=='directory';continue
 src=S/row['path'];dst=snap/row['path'];assert src.lstat().st_mode&0o7777==row['mode']
 if row['kind']=='directory':dst.mkdir(parents=True,exist_ok=True)
 else:
  raw=src.read_bytes();assert h(raw)==row['sha256'] and len(raw)==row['bytes']<4194304;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw)
 os.chmod(dst,row['mode']);origin.append(row)
manifest=P.scan(snap);assert len(manifest['members'])==42 and sum(x['kind']=='file' for x in manifest['members'])==31;P.put(D/'FAILED_PAYLOAD_MANIFEST01.json',manifest);archive=P.pack(snap,manifest,D/'failed-remote02.tar.gz');assert archive['bytes']<4194304
(D/'ORIGINAL_FAILED_ROOT_SCOPE43.json').write_bytes((V/'FAILED_ROOT_SCOPE01.json').read_bytes());P.put(D/'CAPTURE01.json',{'schema_version':1,'status':'COMPLETE_ORIGINAL_FAILED_FORENSIC_ROOT02_LOCAL_CAPTURE_NO_EXTERNAL_RECOVERY','time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'original_root':str(S),'snapshot':str(snap),'permanent_disposition':'FAILED_SPENT_FORENSIC_NAMESPACE_NO_NUMERICAL_CLAIM','original_scope_sha256':h((V/'FAILED_ROOT_SCOPE01.json').read_bytes()),'original_typed_including_root':43,'payload_descendants':42,'regular_bodies':31,'logical_original_body_bytes':114237,'manifest_sha256':h((D/'FAILED_PAYLOAD_MANIFEST01.json').read_bytes()),'archive':archive,'actual_outcome_review_machine_sha256':h((V/'MACHINE01.json').read_bytes()),'actual_FAILED_sha256':h((S/'FAILED01.json').read_bytes()),'Root_outer_exit':1,'original_init_observed_exit':None,'separate_init_actual_reaped_exit':0,'historical_changed_directory_path_or_field':None,'native_or_ResearchRun_claim_started':False,'actual_external_or_flat_receipt':None,'qualification':'Complete opaque failed root/source/partialGit/outputs and literal modes, with rootmode separately retained. No POSIX reconstruction or failed attempt rerun. Original unknowns remain unknown.'});print(h((D/'CAPTURE01.json').read_bytes()),archive)
