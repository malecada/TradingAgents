import copy,hashlib,io,json,os,sys
from pathlib import Path
H=Path(__file__).resolve().parent
old=sys.argv[1]=='old';A=H.parent/'financial-batch-output-chunk-storage-preparation01-2026-10-04' if old else H
sys.path.insert(0,str(A));import codec01 as C;import local_store01 as L
label='old' if old else 'new';checks=0;results={}
def check(v):
 global checks
 assert v;checks+=1
D=dict(schema_version=1,kind='mcm-batch-output-bytes',role='mcm-output',dtype='<f4',shape=[1,32],order='C',scope={k:'a'*64 for k in C.SCOPE},motifs=32,spent_samples=512)
f={};raw=bytes(range(128));pin=C.encode_stream(io.BytesIO(raw),D,lambda n,b:f.setdefault(n,b),chunk_bytes=32)
expected=copy.deepcopy(D);expected['scope']['graph']='b'*64
calls=[]
def reader(n):calls.append(n);expected['scope']['graph']='a'*64;return f[n]
try:result=C.verify_stream(reader,pin,expected);refused=False
except ValueError as e:result={'error':str(e)};refused=True
check(refused is (not old));results['CS1']={'refused':refused,'actual_result':result,'calls':calls}
# Both methods are real actual source, bound to a real private owned directory.
r=H/(label+'-verify-fatal');r.mkdir(mode=0o700);failure=KeyboardInterrupt('owned opaque provisional interruption');seen=[]
with L.LocalStore(r) as s:
 terminal=C.encode_stream(io.BytesIO(raw),D,s.put,chunk_bytes=32)
 def provisional(b):seen.append(b);raise failure
 try:s.verify(terminal,D,provisional)
 except KeyboardInterrupt as e:check(e is failure)
 else:raise AssertionError('missing original fatal')
 check(s.poisoned is (not old));poisoned=s.poisoned
 try:s.verify(terminal,D);retry=True
 except ValueError:retry=False
 check(retry is old);results['CS2']={'primary_identity_preserved':True,'poisoned':poisoned,'retry_succeeded':retry,'prefix_bytes':sum(map(len,seen))}
# Reviewer exact threshold scale is preserved; only LIMIT differs, no cap claim.
r=H/(label+'-allocated-scaled');r.mkdir(mode=0o700);production=L.LIMIT;L.LIMIT=max(8192,r.stat().st_blocks*512+4096);scaled=L.LIMIT
try:
 try:
  with L.LocalStore(r) as s:
   s.put('start.json',b'x');s.put('terminal.json',b'y')
 except ValueError as e:error=str(e)
 else:raise AssertionError('no bound refusal')
 allocated=r.stat().st_blocks*512+sum(p.stat().st_blocks*512 for p in r.iterdir())
 check((allocated>scaled) is old)
 if not old:check(not list(r.iterdir()))
 results['CS3']={'scaled_only':True,'production_limit':production,'scaled_limit':scaled,'actual_allocated':allocated,'error':error,'retained':sorted(p.name for p in r.iterdir()),'actual_64MiB_capacity_measured':False}
finally:L.LIMIT=production
results['checks']=checks;results['codec_sha256']=hashlib.sha256((A/'codec01.py').read_bytes()).hexdigest();results['sink_sha256']=hashlib.sha256((A/'local_store01.py').read_bytes()).hexdigest()
(H/('WITNESS_'+label.upper()+'02.json')).write_text(json.dumps(results,sort_keys=True,indent=2)+'\n');print(json.dumps(results,sort_keys=True))
