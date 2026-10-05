"""Finite final population binder. Missing actual dependencies never release."""
import ast,hashlib,json,os,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
sys.path.insert(0,str(HERE/'utilities'))
import recovery_pax01 as R
SOURCE='32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41'
PREFIX='research/onchain-paper-replication-2026-09-24/full_sources/'
COMMON=('accepted_basis_byte_review','coalesced_actual_review','source_runtime_bridge','postinstall_review','independent_population_review')
FINAL=('baseline_envelope','baseline_recovery_review','complete_final_request','complete_final_release','complete_three_proofs')
ROUNDS={'BASELINE':'baseline02','FINAL_SUPPLEMENT':'final-supplement02'}
def evidence(q):
 R.require(type(q)is dict and q.get('round') in ROUNDS,'two fixed rounds only')
 if q['round']=='BASELINE':R.require(all(q.get(k)is None for k in FINAL),'baseline excludes genuinely future proofs and final caller')
 fields=COMMON+(FINAL if q['round']=='FINAL_SUPPLEMENT' else ())
 needed=[]
 for field in fields:
  v=q.get(field)
  if field=='complete_three_proofs':R.require(type(v)is list and len(v)==3 and len({ref(x)['path'] for x in v})==3,'three distinct actual proofs');needed.extend(v)
  else:needed.append(ref(v))
 return fields,needed

def envelope(q,fields):
 r=ref(q.get('envelope'));e=json.loads(body(r))
 R.require(e=={'schema_version':1,'round':q['round'],'source':SOURCE,'bundles':q['bundles'],'evidence':{k:q[k] for k in fields}},'exact nonrecursive envelope')
 R.require(q['exact_required'].get(r['path'])=={k:r[k] for k in ('bytes','sha256')},'envelope selected')
 if q['round']=='BASELINE':R.require(r['path']==PREFIX+'financial-wrapper-compatibility-preclaim-baseline-envelope01-2026-10-05/ENVELOPE01.json','fixed baseline envelope')
 return e
def hexpin(v,n=64):
 R.require(type(v)is str and len(v)==n and all(c in '0123456789abcdef' for c in v),'exact nonnull pin');return v
def ref(row):
 R.require(type(row)is dict and set(row)=={'path','bytes','sha256'},'exact body ref')
 R.require(type(row['path'])is str and row['path'].startswith(PREFIX) and R.path_name(row['path'])==row['path'] and type(row['bytes'])is int and 0<=row['bytes']<=R.FILE,'bounded declared study body')
 hexpin(row['sha256']);return row
def body(row):
 ref(row);b=R.read(ROOT,row['path']);R.require(len(b)==row['bytes'] and R.digest(b)==row['sha256'],'genuine exact body');return b
def validate(q):
 R.require(type(q)is dict and q['schema_version']==1 and q['status']=='ROOT_FROZEN_TWO_ROUND_POPULATION_REQUIRES_CALLER_REVIEW','unreleased draft')
 R.require((q['source'],q['source_tracked'],q['source_pins'],q['input_roles'],q['whole_source_typed'],q['whole_source_regular'],q['whole_git_objects'],q['basis_git_objects'],q['additional_git_objects'],q['basis_source_typed'],q['additional_files'],q['additional_directories'])==(SOURCE,355,354,11,605,491,407,394,13,589,15,1),'fixed actual population composition')
 hexpin(q['actual_main_commit'],40);required=q['exact_required'];R.require(type(required)is dict and 1<=len(required)<=506,'finite exact required set')
 total=0
 for p,r in required.items():ref(dict(path=p,**r));total+=r['bytes']
 R.require(total<=64*1024**2,'selected total bound');known=json.loads(R.read(HERE,'KNOWN_REQUIRED01.json'));R.require(q['round']=='FINAL_SUPPLEMENT' or all(required.get(k)==v for k,v in known.items()),'baseline retains all current and failed capture bodies')
 fields,needed=evidence(q);envelope(q,fields)
 for r in needed:
  ref(r);R.require(required.get(r['path'])=={k:r[k] for k in ('bytes','sha256')},'required genuine final proof/support body');body(r)
 bundles=q['bundles'];R.require(type(bundles)is list and 1<=len(bundles)<=8,'finite explicit archive population');seen=set();members=[];logical=0
 for b in bundles:
  R.require(type(b)is dict and set(b)=={'name','archive','manifest','capture'},'exact archive descriptor');name=b['name'];R.require(type(name)is str and name.isascii() and name.replace('-','').isalnum() and name not in seen,'fresh unique archive name');seen.add(name)
  for key in ('archive','manifest','capture'):
   r=ref(b[key]);R.require(required.get(r['path'])=={k:r[k] for k in ('bytes','sha256')},'archive capture membership')
  m=json.loads(body(b['manifest']));R.validate(m);R.require(R.encode(m)==body(b['manifest']),'canonical manifest');logical+=sum(x.get('bytes',0) for x in m['members']);members.extend(x for x in m['members'] if x['kind']=='file');body(b['archive']);body(b['capture'])
 R.require(logical<=64*1024**2,'complete recovered raw bound')
 # Final callers/proofs must also be archived, not just individually selected reports.
 R.require(all(any(x['sha256']==r['sha256'] and x['bytes']==r['bytes'] for x in members) for r in needed),'complete final envelope/proof archive closure')
 R.require(q['round']=='FINAL_SUPPLEMENT' or any(b['archive']['sha256']=='d90353cb0d72df5fca6ed2479f2ea6b28400a9dcdc6bc1143a8973665ca1d8b1' and b['capture']['sha256']=='5a44a5f98f70c23fa059054c24014d7921f86a992671700801ea857a95813b66' for b in bundles),'genuine source/Parent04 archive preserved')
 return required
def remote_source(q):
 required=validate(q);s=R.read(HERE,'recover.template01.py').decode();changes=[('REQUIRED = None','REQUIRED = '+repr(required)),('FINAL_POPULATION_COUNT = None','FINAL_POPULATION_COUNT = '+str(len(required)))]
 for a,b in changes:R.require(s.count(a)==1,'exact source population seam');s=s.replace(a,b)
 suffix=ROUNDS[q['round']];a='compatibility-final-bundle01';b='compatibility-'+suffix;R.require(s.count(a)==2,'two exact receiver namespace literals');s=s.replace(a,b);changes.append((a,b));ast.parse(s);return s.encode(),changes
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--request',required=True);p.add_argument('--sha256',required=True);a=p.parse_args();raw=R.read(HERE,a.request);R.require(R.digest(raw)==hexpin(a.sha256),'actual request pin');q=json.loads(raw);source,changes=remote_source(q);target=HERE/'GENERATED_REMOTE01.py'
 with R.new_file(target) as fd:
  off=0
  while off<len(source):
   written=os.write(fd,source[off:]);R.require(written>0,'complete source write');off+=written
  os.fsync(fd)
 R.put(HERE/'GENERATED_BINDING01.json',{'source_sha256':R.digest(source),'request_sha256':a.sha256,'changes':changes,'actual_network':False,'actual_release':None})
