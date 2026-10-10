from pathlib import Path
import datetime,hashlib,json,os,re,resource,shlex,subprocess,time
r=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
out=r/"research/onchain-paper-replication-2026-09-24/full_sources/pilot29-third-group-actual-recovery01-2026-10-10"
off=r/'research_artifacts/onchain_batched_offload/c64f82cdaebfcadd2c0227b40ac26bfdf7c53705c0d8f56903f3183c0ea49cc2/mcm-0114d61904938208c75497bdabe82c5dae32b7d2110a4e460d1942f84dc473ba/preserve/00000002/offload.json'
raw=off.read_bytes(); d=json.loads(raw); receipt=d['receipt']
assert d['first_batch']==32 and d['batches']==16 and d['cells']==65536
assert receipt['transport_identity']=='553a31d3776219f2ef54ba0eef449dba08746d0ea8cc6c68ca120a37fe86ac84'
assert receipt['bytes']==3532800 and re.fullmatch('[a-f0-9]{64}',receipt['source_sha256'])
assert re.fullmatch('ethpilot-20261009-29-[a-f0-9]{64}-p[a-f0-9]{16}-000000000000/payload.bin',receipt['member'])
assert receipt['remote']+'/payload.bin'==receipt['member']
old=json.loads((r/'research/onchain-paper-replication-2026-09-24/full_sources/pilot29-first-group-actual-recovery01-2026-10-10/REQUEST01.json').read_bytes())
argv=old['argv'][:-1]+['cat '+shlex.quote(receipt['member'])]
for name in ('REQUEST01.json','RESULT01.json','returned-third-group.tar','ssh.stderr','MANIFEST01.json'):
 assert not (out/name).exists(),name
request={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':argv,'receipt':receipt,'offload_sha256':hashlib.sha256(raw).hexdigest(),'transport_identity':receipt['transport_identity'],'bounds':old['bounds'],'credential_contents_read':False,'scope':'Root fresh read-only retrieval of actual third-group increment; no claim, numerical execution or deletion'}
(out/'REQUEST01.json').write_text(json.dumps(request,sort_keys=True,indent=2)+'\n')
resource.setrlimit(resource.RLIMIT_FSIZE,(4194304,4194304))
resource.setrlimit(resource.RLIMIT_CPU,(15,15))
os.nice(10)
if 3 in os.sched_getaffinity(0):os.sched_setaffinity(0,{3})
start=time.monotonic(); actual_exit=None; error=None
with (out/'returned-third-group.tar').open('xb') as dst,(out/'ssh.stderr').open('xb') as err:
 try:actual_exit=subprocess.run(argv,stdout=dst,stderr=err,timeout=60,check=False).returncode
 except Exception as exc:error=repr(exc)
returned=(out/'returned-third-group.tar').read_bytes()
result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_exit':actual_exit,'actual_error':error,'elapsed_seconds':time.monotonic()-start,'expected_bytes':receipt['bytes'],'expected_sha256':receipt['source_sha256'],'returned_bytes':len(returned),'returned_sha256':hashlib.sha256(returned).hexdigest(),'no_credentials_inspected':True,'no_deletion':True,'exact_match':actual_exit==0 and len(returned)==receipt['bytes'] and hashlib.sha256(returned).hexdigest()==receipt['source_sha256'],'scope':'Fresh selected external bytes only; semantics and numerical correctness require separate evidence'}
(out/'RESULT01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
manifest={'format':'actual-third-group-recovery-v1','files':[{'path':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(out.iterdir()) if p.is_file()]}
(out/'MANIFEST01.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
print('manifest_sha256',hashlib.sha256((out/'MANIFEST01.json').read_bytes()).hexdigest())
raise SystemExit(0 if result['exact_match'] else 1)
