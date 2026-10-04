"""Finite source-copy recipe only. Never creates a Run, root, gate or authority."""
import argparse,hashlib,json,os,re,stat,subprocess
from pathlib import Path
from owned_io import _opened
HERE=Path(__file__).resolve().parent
BASELINE_SHA='d963e3b33e2199206bee953d8646c55725559db5c2c17ac305f239e967314bac'
CLOSURE_SHA='833b30f52f9365fd681bfaeea8031909fe938db7bb46e33ab9082f8a8d8961b1'
MAIN=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
PARENT=Path('/home/malecada/master_thesis/onchain-treatment-isolation')
ROLE_NAMES=('execution_job','environment','treatment_plan','financial_batch_plan','population_plan','source_admission','historical_cohort','historical_cohort_policy','registration','charter','cumulative_allowance','resource_controls','independent_review','external_recovery')
PROTECTED=('keys','apis','.env','.ssh','hf_token.txt')

def require(value,message):
 if not value:raise ValueError(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def blob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def bounded(path):
 require(path.resolve()==path and not path.is_symlink(),'redirected source')
 before=path.lstat();require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<=4*1024**2,'source type/extent')
 with _opened(path,'rb') as stream:
  sig=lambda v:(v.st_dev,v.st_ino,v.st_mode,v.st_nlink,v.st_size,v.st_mtime_ns,v.st_ctime_ns)
  require(sig(os.fstat(stream.fileno()))==sig(before),'opened source changed')
  raw=stream.read(4*1024**2+1)
  require(sig(path.lstat())==sig(before)==sig(os.fstat(stream.fileno())) and len(raw)==before.st_size,'source changed during read')
 return raw

def document(name,pin):
 raw=bounded(HERE/name);require(sha(raw)==pin,'frozen recipe metadata changed');return json.loads(raw)
def source_paths(root):
 p=root/'tradingagents/research/onchain_replication'
 return sorted({x.relative_to(root).as_posix() for x in p.glob('*.py')}|{x.relative_to(root).as_posix() for x in p.parent.glob('*.py')}|{'tradingagents/__init__.py'})
def verify_source(root,expected):
 require(root.resolve()==root and set(source_paths(root))==set(expected),'exact source closure membership differs')
 require(len(expected) in (135,138),'finite closure cardinality differs')
 for rel,pin in expected.items():
  path=Path(rel);require(not path.is_absolute() and str(path)==rel and '..' not in path.parts and all(p not in PROTECTED for p in path.parts),'unsafe source role')
  raw=bounded(root/rel);s=(root/rel).stat()
  require(sha(raw)==pin['sha256'] and len(raw)==pin['bytes'] and stat.S_IMODE(s.st_mode)==pin['mode'] and blob(raw)==pin['git_blob_oid'],'source body/mode/OID differs')
  require(pin['git_mode']==('100755' if s.st_mode&0o111 else '100644'),'Git mode differs')

def target_path(value):
 require(type(value)is str and value,'target path required');p=Path(value)
 require(p.is_absolute() and str(p)==value and p.resolve()==p and '..' not in p.parts,'target must be canonical absolute')
 require(p.parent.parent==PARENT and p.name=='source' and re.fullmatch('[a-z][a-z0-9-]{3,79}',p.parent.name) is not None,'fresh dedicated treatment unit required')
 require(not os.path.lexists(p.parent),'fresh unit identity already exists/reserved')
 require(PARENT.resolve()==PARENT and not PARENT.is_symlink() and (not PARENT.exists() or PARENT.is_dir()),'authorized treatment parent redirected')
 require(not(p==MAIN or p.is_relative_to(MAIN) or MAIN.is_relative_to(p)),'protected Main overlap')
 return p

def role_map(value):
 require(type(value)is dict and set(value)==set(ROLE_NAMES),'exact role denominator required')
 require(all(v is None for v in value.values()),'draft source-copy recipe cannot impersonate admitted input/gate/review roles')
 return value

def prepare(target,roles):
 require(sha(bounded(HERE/'owned_io.py'))=='09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','accepted IO helper changed')
 target=target_path(target);role_map(roles);base=document('BASELINE01.json',BASELINE_SHA);candidate=document('CLOSURE01.json',CLOSURE_SHA)
 require(base['root']==str(MAIN) and base['source_count']==135 and candidate['source_count']==138 and candidate['onchain_module_count']==130,'declared source closure count differs')
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=MAIN,text=True,timeout=10).strip();require(head==base['head'],'current Main commit differs; require a fresh explicit source recipe')
 verify_source(MAIN,base['sources']);verify_source(HERE/'candidate',candidate['sources'])
 selfpath=candidate['producer_dynamic_self_path'];pins=candidate['producer_static_pins'];require(set(pins)==set(candidate['sources'])-{selfpath} and len(pins)==137 and all(pin==candidate['sources'][rel]['sha256'] for rel,pin in pins.items()),'exact producer SourceSource map differs')
 guards=document('SCIENTIFIC_GUARDS01.json','2a41ca2a003667553b870954df603e367285c198da6c5a13f1e465a744ebf21e')
 for rel,pin in guards.items():
  raw=bounded(MAIN/rel);require(sha(raw)==pin['sha256'] and len(raw)==pin['bytes'] and stat.S_IMODE((MAIN/rel).stat().st_mode)==pin['mode'],'original scientific configuration/protocol changed')
 copy=[{'from':str(HERE/'candidate'/rel),'to':str(target/rel),'relative':rel,**row} for rel,row in candidate['sources'].items()]
 require(len(copy)==138 and [r['relative'] for r in copy]==sorted(candidate['sources']),'complete copy order differs')
 require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=MAIN,text=True,timeout=10).strip()==head,'Main changed during preparation')
 return {'status':'DRAFT_SOURCE_COPY_ONLY','target':str(target),'original_main':{'root':str(MAIN),'commit':head,'source_count':135},'candidate_source_count':138,'scientific_guard_pins':guards,'copy':copy,'roles':roles,'future_source_commit':None,'future_design_source':None,'future_registration_commit':None,'fund_complete':'REFUSED: historical65 cohort/address/vintage and known_at policy unadmitted','financial_credit':0,'authority':None}

def release(*args,**kwargs):
 raise ValueError('NOT RELEASED: source preparation grants no charter/gate/cumulative/native/recovery authority')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--target',required=True);p.add_argument('--release',action='store_true');a=p.parse_args()
 if a.release:release()
 print(json.dumps(prepare(a.target,{k:None for k in ROLE_NAMES}),indent=2,sort_keys=True))
