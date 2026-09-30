"""One fresh analytical synthetic profile; no empirical graph or prices."""
from pathlib import Path
import hashlib,importlib.util,json,sys,time
import numpy as np
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from tradingagents.research.onchain_replication.resources import assert_guarded_worker,GIB
from tradingagents.research.onchain_replication.environment import inventory

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def publish(name,data):
 with (HERE/name).open('x') as f:json.dump(data,f,indent=2);f.write('\n')

def main():
 for name,h in json.loads((HERE/'bindings.json').read_bytes()).items():
  if sha(ROOT/name)!=h:raise ValueError('source changed: '+name)
 if inventory(ROOT)!=json.loads((HERE/'environment.json').read_bytes()):raise ValueError('runtime changed')
 assert_guarded_worker(HERE/'guard01',sys.orig_argv,required_paths=[ROOT],wall_seconds=300,memory_max_bytes=GIB,memory_high_bytes=3*GIB//4,disk_floor_bytes=10*GIB)
 spec=importlib.util.spec_from_file_location('ranked',HERE.with_name('ranked-hardening-2026-09-30')/'ranked.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 publish('started.json',{'fixtures':['flat','diagonal_distance'],'shape':[2000,2000],'max_pair_entries':4_000_000,'no_automatic_retry':True})
 results=[]
 for kind in ('flat','diagonal_distance'):
  x=np.zeros((2000,2000),dtype=np.float64)
  if kind=='diagonal_distance':
   axis=np.arange(2000,dtype=np.float64);np.subtract(axis[:,None],axis[None,:],out=x);np.abs(x,out=x);np.negative(x,out=x);del axis
  identity=hashlib.sha256(memoryview(x).cast('B')).hexdigest()
  started=time.monotonic();pairs=m.harden_pairs(x,max_pair_entries=4_000_000,max_explicit_bytes=68_036_000);elapsed=time.monotonic()-started
  expected=np.arange(2000,dtype=np.int64)
  if pairs.shape!=(2000,2) or not np.array_equal(pairs[:,0],expected) or not np.array_equal(pairs[:,1],expected):raise AssertionError('analytical greedy oracle differs')
  if hashlib.sha256(memoryview(x).cast('B')).hexdigest()!=identity:raise AssertionError('input mutated')
  results.append({'fixture':kind,'shape':[2000,2000],'input_sha256':identity,'elapsed_seconds':elapsed,'selected_pairs':2000,'pair_sha256':hashlib.sha256(memoryview(pairs).cast('B')).hexdigest(),'analytical_diagonal_exact':True,'input_unchanged':True,'explicit_bytes':m.explicit_bytes(2000,2000)})
  del x,pairs,expected
 result={'fixtures':results,'qualification':'Fresh isolated ranking fixtures only, no annealing/scoring, checkpoint/resume, production integration or real-graph feasibility. Timing includes native stable sort and Python selection. Actual guard peak includes runtime/input/native workspace; explicit allowance excludes those costs.'}
 publish('result.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
