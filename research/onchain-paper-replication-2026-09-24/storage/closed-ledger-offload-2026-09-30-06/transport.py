"""Preservation-local deadlines for one <=4 GiB file; old transport unchanged."""
from pathlib import Path
import importlib.util
import json
import sys
ROOT=Path(__file__).resolve().parents[4]
spec=importlib.util.spec_from_file_location('prior_transfer',ROOT/'research/onchain-paper-replication-2026-09-24/storage/raw-preservation-2026-09-28-09/transfer.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
class Transport(base.Transport):
 def run(self,args):
  try:return base.subprocess.run(args,check=True,capture_output=True,timeout=5400)
  except (base.subprocess.CalledProcessError,base.subprocess.TimeoutExpired) as error:
   print(json.dumps({'transport_error_type':type(error).__name__,'returncode':getattr(error,'returncode',None),'stderr_tail':(error.stderr or b'')[-16384:].decode('utf-8',errors='replace')}),file=sys.stderr,flush=True)
   raise
 def get(self,path,destination):
  if Path(destination).exists():raise FileExistsError(destination)
  size=self.sizes[path];count=size//32768+1;self.reserve(count*32768)
  base.receive_diagnostic([*self.ssh,'dd','if='+self.remote_path(path),'bs=32768','count='+str(count)],destination,expected_bytes=size,max_seconds=5400,bytes_per_second=self.rate_bytes)
