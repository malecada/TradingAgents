from pathlib import Path
import importlib.util,os,json
O=Path(__file__).resolve().parent;T=O.parent/'financial-wrapper-compatibility-operational-delta-flat-tooling01-2026-10-04';spec=importlib.util.spec_from_file_location('limit_flat',T/'restore01.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M);p=O/'cap04';p.mkdir(mode=0o700)
fd=os.open(p/'oversize',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
try:os.ftruncate(fd,M.R.FILE+1)
finally:os.close(fd)
try:M.W.census(p)
except ValueError as e:result={'actual_sparse_extent':(p/'oversize').stat().st_size,'actual_allocated':(p/'oversize').stat().st_blocks*512,'result':'refused','error':str(e)}
else:raise AssertionError('oversize accepted')
(O/'LIMITS04.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS actual per-file cap refusal without allocating payload')
