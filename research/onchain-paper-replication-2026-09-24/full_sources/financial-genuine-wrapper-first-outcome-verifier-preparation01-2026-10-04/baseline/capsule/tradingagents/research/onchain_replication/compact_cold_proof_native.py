"""Stdlib pre-claim finite native selection. No scientific completion authority."""
import hashlib,json,resource
from pathlib import Path
GIB=1024**3
FILE=4*1024**2
IDENTITIES={'materialize':'compact-cold-inputs-20261003-01','compare':'compact-cold-comparison-20261003-01'}

def require(value,message):
 if not value:raise ValueError(message)

def selected(job):return job.get('kind')=='fit' and type(job.get('payload')) is dict and job['payload'].get('cold_proof_input') is not None

def schema(job):
 p=job['payload'];r=job['resources']
 require(set(p)=={'cold_proof_input','representation_jobs'} and type(p['cold_proof_input']) is str and p['cold_proof_input'] and type(p['representation_jobs']) is dict,'native cold payload schema')
 require(r.get('native_unit_limits')=={'file_size_bytes':FILE} and 'physical_policy' not in r,'native cold exact file route required')
 require(r['memory_high_bytes']==r['memory_max_bytes']==3*GIB and r['reserve_bytes']==3*GIB and r['start_reserve_bytes']==6*GIB and r['disk_floor_bytes']==10*GIB and r['wall_seconds']==1800,'native cold exact resource policy differs')

def admitted(ad,job):
 schema(job);name=job['payload']['cold_proof_input'];require(name in ad.inputs,'native cold unregistered selection')
 info=ad.inputs[name];path=ad.root/info['path'];raw=path.read_bytes()
 require(hashlib.sha256(raw).hexdigest()==info['sha256'],'native cold selection hash differs')
 p=json.loads(raw);phase=p.get('phase')
 require(phase in IDENTITIES and p.get('kind')=='genuine-compact-cold-engineering-proof-v1' and p.get('experiment')==ad.experiment_id==IDENTITIES[phase] and ad.spec['program_id']=='compact-cold-engineering-20261003','native cold finite phase identity differs')
 require(job['resources']['storage_budget']['root']==str(ad.root) and job['resources']['disk_paths']==[str(ad.root)],'native cold complete capsule watch required')
 require((ad.root/'.git').is_dir() and (ad.root/'.git').resolve()==ad.root/'.git','native cold genuine isolated Git required')
 require(p.get('watch')==job['resources']['storage_budget'],'native cold selected storage differs')
 require(type(p.get('source_files')) is dict and bool(p['source_files']),'native cold source pins missing')
 for rel,sha in p['source_files'].items():
  require(ad.experiment['source_files'].get(rel)==sha and hashlib.sha256((ad.root/rel).read_bytes()).hexdigest()==sha,'native cold frozen source differs')

def worker_limits():
 resource.setrlimit(resource.RLIMIT_FSIZE,(FILE,FILE))
 require(resource.getrlimit(resource.RLIMIT_FSIZE)==(FILE,FILE),'native cold actual process file cap differs')
 return {'rlimit_fsize':FILE}
