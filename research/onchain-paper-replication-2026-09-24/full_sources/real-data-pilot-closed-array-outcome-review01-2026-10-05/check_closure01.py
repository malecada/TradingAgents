"""Run only after Root reports the actual terminal. Compact receipts/stat only."""
from pathlib import Path
import datetime,hashlib,json,stat,sys
D=Path(__file__).resolve().parent;M=D.parents[3];E=M/'research/onchain-paper-replication-2026-09-24/storage/closed-array-pilot-offload-2026-10-05-01'
evidence={}
def raw(p):
 p=Path(p);s=p.lstat()
 assert stat.S_ISREG(s.st_mode) and not p.is_symlink() and s.st_size<=4*1024**2 and p.suffix not in ('.npy','.npz','.bin','.pt','.sqlite'),str(p)
 b=p.read_bytes();evidence[str(p.relative_to(M))]=hashlib.sha256(b).hexdigest();return b
def read(p):return json.loads(raw(p))
def same(paths):
 values=[raw(p) for p in paths];assert all(v==values[0] for v in values);return json.loads(values[0])
def transport(p,expected):
 r=read(p);assert r['expected_bytes']==r['received_bytes']==expected and r['status']=='complete' and r['returncode']==0 and r['error_type'] is None;return r
if sys.argv[1:]!=['--terminal-notified']:raise SystemExit('Root terminal notification required; no running outcome read')
review=read(E/'RELEASE_REVIEW.json');assert review['decision']=='accepted'
assert hashlib.sha256(raw(E/'manifest.json')).hexdigest()==review['manifest_sha256']=='5c62255f8dfce1ffa8d8efed5da3457f0af6a51a1de6ff626a639fdb3b8a0b13'
assert hashlib.sha256(raw(E/'offload.py')).hexdigest()==review['worker_sha256'];assert hashlib.sha256(raw(E/'entry01.py')).hexdigest()==review['entry_sha256']
c=read(E/'manifest.json');draft=read(M/c['draft']['path']);assert evidence[c['draft']['path']]==c['draft']['sha256'];rows=draft['files'];assert len(rows)==30 and sum(r['bytes'] for r in rows)==3021553488
outer=read(E/'outer-exit01.json');guard=read(E/'guard01/final.json');preflight=read(E/'preflight01.json');launch=read(E/'launch-attempt01.json');assert launch==preflight and preflight['manifest_sha256']==review['manifest_sha256']
intent=read(E/'intent.json');assert intent['manifest_sha256']==review['manifest_sha256'] and intent['identity']==c['identity'] and intent['files']==30 and intent['bytes']==3021553488
summary=[];transports=[];records=[];pid_values=set()
if (E/'recovered-manifest.json').exists():
 same([E/'manifest.json',E/'recovered-manifest.json']);transports.append(transport(E/'recovered-manifest.json.transport.json',(E/'manifest.json').stat().st_size))
for i,row in enumerate(rows):
 source=M/row['path'];state={'index':i,'path':row['path'],'source_present':source.exists(),'sidecar_present':source.with_name(source.name+'.remote.json').exists(),'recovery_scratch_present':(E/f'{i:02d}-recovered.bin').exists()}
 for phase in ('attempted','verified','evicted','failed','skipped'):
  p=E/f'{i:02d}-{phase}.json';state[phase]=p.exists()
  if p.exists():read(p)
 if state['evicted']:
  record=same([E/f'{i:02d}-restore.json',E/f'{i:02d}-recovered-restore.json',E/f'{i:02d}-verified.json',E/f'{i:02d}-evicted.json',source.with_name(source.name+'.remote.json')])
  assert all(record[k]==v for k,v in row.items()) and record['body_roundtrip_verified'] is True
  assert record['remote_object']==c['remote']+f'/{i:02d}.bin' and record['remote_restore']==c['remote']+f'/{i:02d}-restore.json'
  assert state['attempted'] and not state['source_present'] and not state['recovery_scratch_present'] and not state['failed'] and not state['skipped']
  transports.append(transport(E/f'{i:02d}-recovered.bin.transport.json',row['bytes']));transports.append(transport(E/f'{i:02d}-recovered-restore.json.transport.json',(E/f'{i:02d}-restore.json').stat().st_size));records.append(record)
 summary.append(state)
complete=(E/'complete.json').exists();failed=(E/'failed.json').exists()
if complete:
 terminal=same([E/'completion-candidate.json',E/'recovered-complete.json',E/'complete.json']);assert terminal['files']==records and len(records)==30 and terminal['bytes_moved']==3021553488 and terminal['no_automatic_retry'] is True and terminal['restoration_required_before_future_local_array_use'] is True
 assert not failed and not list(E.glob('*-failed.json')) and not list(E.glob('*-skipped.json'))
 transports.append(transport(E/'recovered-complete.json.transport.json',(E/'complete.json').stat().st_size))
 assert guard['phase']=='complete' and guard['child_exit_code']==0 and guard['cleanup_verified'] is True
 assert outer['entry_selected_exit_code']==0 and outer['guard_phase']=='complete' and outer['guard_child_exit_code']==0 and outer['cleanup_verified'] is True and outer['fatal_type'] is None
if failed:read(E/'failed.json')
for r in transports:
 if type(r.get('pid')) is int:pid_values.add(r['pid'])
for name in ('monitor_pid','worker_pid','pid'):
 if type(guard.get(name)) is int:pid_values.add(guard[name])
for p in (E/'guard01').glob('*.json'):
 record=read(p)
 if isinstance(record,dict):
  for name in ('monitor_pid','worker_pid','pid'):
   if type(record.get(name)) is int:pid_values.add(record[name])
cleanup={'recorded_pids':sorted(pid_values),'recorded_pids_still_present':[p for p in sorted(pid_values) if Path('/proc',str(p)).exists()],'recorded_cgroup':guard.get('cgroup'),'recorded_cgroup_present':None if not guard.get('cgroup') else Path(guard['cgroup']).exists()}
if complete:assert not cleanup['recorded_pids_still_present'] and cleanup['recorded_cgroup_present'] is False
telemetry={k:v for k,v in guard.items() if any(term in k for term in ('memory','swap','cpu','disk','storage','elapsed','cleanup','limit_reason','unit_properties'))}
print(json.dumps({'decision':'complete_metadata_joins_passed' if complete else 'partial_or_failed_requires_review','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'manifest_sha256':review['manifest_sha256'],'guard_phase':guard.get('phase'),'guard_child_exit':guard.get('child_exit_code'),'outer':outer,'entry_HEAD':preflight['head'],'source_anchor':c['source_commit'],'file_states':summary,'verified_evicted':len(records),'transport_receipts':len(transports),'full_body_received_bytes':sum(r['received_bytes'] for r in transports if r['expected_bytes'] in {x['bytes'] for x in rows}),'cleanup':cleanup,'telemetry_unmodified_fields':telemetry,'evidence':evidence,'limits':['No body hash/retransfer or numerical/payload decoding; original byte recovery inferred from exact accepted worker and actual fresh-get/verified receipts','Outer entry-selected/guard codes are not a substitute for Root actual shell/tool exit','No perpetual remote availability or whole-pilot capacity claim']},sort_keys=True,indent=2))
