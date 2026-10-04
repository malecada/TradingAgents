import copy,hashlib,io,json,os,stat,sys
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.parent/'financial-batch-output-chunk-storage-preparation01-2026-10-04';sys.path.insert(0,str(A));import codec01 as C;import local_store01 as L
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha((A/'codec01.py').read_bytes())=='00d06377c4567bd7880dd7ddbf396b613a78968a7317a565f7e034319c9ed4fe';assert sha((A/'local_store01.py').read_bytes())=='2614242ebc8395f859e704db1971dd46172ff8ea9802fb4c77397c80970bdb52'
d={'schema_version':1,'kind':'mcm-batch-output-bytes','role':'mcm-output','dtype':'<f4','shape':[1,32],'order':'C','scope':{k:'a'*64 for k in C.SCOPE},'motifs':32,'spent_samples':512};raw=bytes(range(128));files={};terminal=C.encode_stream(io.BytesIO(raw),d,lambda n,b:files.setdefault(n,b),chunk_bytes=32)
# CS1: mutable expected descriptor changed by first reader call.
expected=copy.deepcopy(d);expected['scope']['graph']='b'*64;initial=copy.deepcopy(expected)
def reader(n):expected['scope']['graph']=d['scope']['graph'];return files[n]
result=C.verify_stream(reader,terminal,expected)
assert result['status']=='complete-byte-proof-only' and initial['scope']['graph']!=d['scope']['graph']
# Pure reader refuses the identical initially incorrect descriptor.
try:C.verify_stream(files.__getitem__,terminal,initial)
except ValueError as e:control=str(e)
else:raise AssertionError('expected ordinary descriptor refusal')
# CS2: failed provisional verification leaves sink reusable despite terminal-failure promise.
r=H/'verify-fatal';r.mkdir(mode=0o700);failure=KeyboardInterrupt('owned provisional callback fatal');seen=[]
with L.LocalStore(r) as store:
 pin=C.encode_stream(io.BytesIO(raw),d,store.put,chunk_bytes=32)
 def provisional(b):seen.append(b);raise failure
 try:store.verify(pin,d,provisional)
 except KeyboardInterrupt as e:assert e is failure
 else:raise AssertionError('fatal not propagated')
 poisoned_after=store.poisoned;reused=store.verify(pin,d)
 assert not poisoned_after and reused['status']=='complete-byte-proof-only'
# CS3: exact LocalStore methods, only engineering threshold scaled to two allocated blocks.
# This is NOT an actual64MiB use/capacity measurement.
r=H/'allocated-scaled';r.mkdir(mode=0o700);limit=max(8192,r.stat().st_blocks*512+4096);oldlimit=L.LIMIT;L.LIMIT=limit
try:
 with L.LocalStore(r) as store:
  before=r.stat().st_blocks*512
  store.put('start.json',b'x')
  try:store.put('terminal.json',b'y')
  except ValueError as e:allocated_error=str(e)
  else:raise AssertionError('expected allocated-bound failure')
  actual=r.stat().st_blocks*512+sum(p.stat().st_blocks*512 for p in r.iterdir());assert actual>limit and store.poisoned
finally:L.LIMIT=oldlimit
w={'codec_sha256':sha((A/'codec01.py').read_bytes()),'sink_sha256':sha((A/'local_store01.py').read_bytes()),'CS1':{'initial_expected':initial,'encoded_descriptor':d,'result':result,'pure_reader_control_refusal':control,'reader_mutates_only_expected_graph':True},'CS2':{'fatal_type':type(failure).__name__,'same_original_exception':True,'provisional_prefix_bytes':sum(map(len,seen)),'poisoned_after_failure':poisoned_after,'retry_result':reused},'CS3':{'scaled_test_only':True,'production_limit':oldlimit,'test_limit':limit,'root_allocated_before':before,'retained_allocated_after_failure':actual,'error':allocated_error,'partial_files_retained':sorted(p.name for p in r.iterdir()),'actual64MiB_measurement':False},'no_scientific_authority_or_actual_arrays':True}
with (H/'WITNESSES01.json').open('x') as f:json.dump(w,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in w.items() if k not in ['CS1','CS2']},sort_keys=True))
