from pathlib import Path
import hashlib,json,subprocess
D=Path(__file__).resolve().parent;M=D.parents[3];E=M/'research/onchain-paper-replication-2026-09-24/storage/closed-array-pilot-offload-2026-10-05-01';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();c=json.loads((E/'manifest.json').read_text());draft=json.loads((M/c['draft']['path']).read_text())
assert h(E/'manifest.json')=='5c62255f8dfce1ffa8d8efed5da3457f0af6a51a1de6ff626a639fdb3b8a0b13'
assert h(E/'offload.py')=='f24adff243d753c68c9467a92e1e7d0d44580cd6c339444587d6a0d0e0a8f3e2'
assert h(E/'entry01.py')=='55a97d487003f0695fc8000a2b34af40a68a44f7cdafa1da20dd2520d84af734'
assert (E/'offload.py').read_text().replace('maximum_payload_bytes=8*GIB','maximum_payload_bytes=MAX_BODY')==(D/'offload.before-budget-correction.py').read_text()
assert c['source_commit']=='8fbe0d4821b9405c0262a18a98469de4beb2cac2'
# Source-only read-only Git batch; no credentials or array paths are included.
pins=c['source_files'];assert len(pins)==165 and c['connection']['path'] not in pins
objects=[]
for p,pin in pins.items():
 path=M/p;assert path.stat().st_size<=4*1024**2 and path.suffix not in ('.npy','.npz','.pt','.sqlite') and '/keys/' not in p and '/apis/' not in p and path.name!='.env';assert h(path)==pin;objects.append(c['source_commit']+':'+p)
proc=subprocess.run(['git','cat-file','--batch'],input=('\n'.join(objects)+'\n').encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=M,check=True);raw=proc.stdout;offset=0
for p,pin in pins.items():
 end=raw.index(b'\n',offset);header=raw[offset:end].split();assert header[1]==b'blob';size=int(header[2]);assert size<=4*1024**2;body=raw[end+1:end+1+size];assert hashlib.sha256(body).hexdigest()==pin;assert raw[end+1+size:end+2+size]==b'\n';offset=end+2+size
assert offset==len(raw)
# Exact serialized size accounting for existing put and padded-dd get reservations.
size=lambda v:len((json.dumps(v,indent=2)+'\n').encode())
roundtrip=lambda n:n+(n//32768+1)*32768
records=[];body_budget=0;metadata_budget=roundtrip((E/'manifest.json').stat().st_size)
for i,row in enumerate(draft['files']):
 body_budget+=roundtrip(row['bytes'])
 record={**row,'remote_object':c['remote']+f'/{i:02d}.bin','remote_restore':c['remote']+f'/{i:02d}-restore.json','body_roundtrip_verified':True,'restoration':'Download remote_object to a new temporary file; verify bytes and SHA-256; restore original path only when absent. Never launch the old job.'}
 records.append(record);metadata_budget+=roundtrip(size(record))
complete={'identity':c['identity'],'files':records,'bytes_moved':3021553488,'no_automatic_retry':True,'restoration_required_before_future_local_array_use':True};metadata_budget+=roundtrip(size(complete));total=body_budget+metadata_budget
assert total<8*1024**3
for k in ('offload_source','transport_source','environment'):assert h(M/c[k]['path'])==c[k]['sha256']
print(json.dumps({'decision':'pass','literal_budget_inverse':True,'source_anchor':c['source_commit'],'actual_current_and_anchor_source_pins':len(pins),'array_put_get_reservation_bytes':body_budget,'exact_manifest_restore_completion_put_get_bytes':metadata_budget,'exact_success_path_network_reservation_bytes':total,'finite_network_budget_bytes':8*1024**3,'network_headroom_bytes':8*1024**3-total,'max_body_scratch_unchanged':387431648,'connection_not_read':True,'large_array_bodies_not_read_or_hashed':True,'remote_or_native_execution':False},sort_keys=True,indent=2))
