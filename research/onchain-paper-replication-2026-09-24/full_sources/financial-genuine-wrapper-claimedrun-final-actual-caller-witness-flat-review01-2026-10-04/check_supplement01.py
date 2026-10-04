import gzip,hashlib,io,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;sys.path.insert(0,str(B/'held-consumer-final-recovery-preparation04-2026-10-03'));import recovery04 as R
sha=lambda b:hashlib.sha256(b).hexdigest();review=B/'financial-genuine-wrapper-claimedrun-final-actual-two-batch-remote-review01-2026-10-04';raw=R.read(review,'MACHINE01.json');assert sha(raw)=='236918fc76a2ce7119a4ac959b2398e849307528a9ede73566328571626c501f';m=json.loads(raw);assert m['decision']=='accepted-actual-two-batch-external-selected-byte-union' and m['commit']=='a9b219042109be78498185cc6539c1454736e3eb' and m['batches'][0]['receipt_sha256']=='ec84e55cfeae3da74557341d3395a84ce5fe4c0a2f187eaec89acc1ded212440'
out=B/'financial-genuine-wrapper-claimedrun-witness-sharded-flat-20261004-01';v=json.loads(R.read(out,'VIRTUAL_RECOVERY01.json'));d=R.read(out,'direct-selected/original.body');assert sha(d)=='c47fcb6875375ecb8ea5c60926bae307955007751cdf52bec2473c44964e17e3'
variants=[]
for name,ref in sorted(v['flat_members'].items()):
 if name.startswith('actual-capture-review/') and any(part in name for part in ('RAW_DETAILED_READBACK','READBACK_COMPACT02','EVIDENCE_HISTORY02','frozen-first-seal-view01/','MANIFEST02.json','VERDICT02.json')):
  raw=R.read(out/ref['shard'],ref['file']);assert sha(raw)==ref['sha256'];variants.append({'path':name,'bytes':len(raw),'sha256':sha(raw)})
compressed=v['flat_members']['actual-capture-review/RAW_DETAILED_READBACK01.json.gz'];raw=R.read(out/compressed['shard'],compressed['file']);z=gzip.GzipFile(fileobj=io.BytesIO(raw),mode='rb')
try:decoded=z.read(2532974);assert decoded==d and z.read(1)==b''
finally:z.close()
assert variants
p=H/'SUPPLEMENT01.json';p.write_text(json.dumps({'accepted_actual_remote_review_machine_sha256':sha(R.read(review,'MACHINE01.json')),'exact_remote_commit':'a9b219042109be78498185cc6539c1454736e3eb','original_raw_format_history_recovered':variants,'bounded_compressed_original_equals_actual_direct_raw':True,'old_failed_partial_archive_parsed':False,'new_actual_restore_or_network':False},sort_keys=True,indent=2)+'\n');print(len(variants))
