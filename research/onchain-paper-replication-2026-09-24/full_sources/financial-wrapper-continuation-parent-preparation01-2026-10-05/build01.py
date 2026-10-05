"""Read-only deterministic Root binding builder; emits a draft bundle, never installs/adopts."""
import argparse, copy, hashlib, json, os, re, shutil, time
from pathlib import Path
import recovery04 as R
from bounded_git01 import git
H=Path(__file__).resolve().parent
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
ID='financial-wrapper-classification-eager-continue100-compatibility-20261004-01'
PRED='financial-wrapper-classification-eager-predict-compatibility-20261004-01'
REFERENCE='financial-wrapper-classification-eager-complete100-compatibility-20261004-01'
OLD_SOURCE='32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41'
OLD_GATE='fixture_inputs/financial_wrapper_compatibility01/gates.json'
OLD_GATE_SHA='e1846c9fbd5d1964c867c9c7027e3e9a6009520c07841ed720c035374dbeb806'
REG='fixture_inputs/financial_wrapper_continuation01/gates.json'
PREPARATION_PINS={'GATE4_DRAFT01.json': 'c4f33416f952ee5e9a2177fc4455bff51662e9fe6639016a92373ca16ba1d693', 'REQUEST_DRAFT01.json': '6cecfa63bbfdba46e3dcd782efeb4879bbee7802bfb8f540fc4396b6d58e3fb2', 'parent01.py': '763b31b21a03a531d1dfa49a26d5744a5ba5ff9f5a44f3ec8b8bef2377bd7027', 'PROTOCOL_PINS01.json': 'b55959d7fef0bf04b6eea80e4e83d1c262a2f0f9e778791814e52f2fe0325434', 'bounded_git01.py': 'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f', 'descendants01.py': '7ce3c0b4aa5a89c8f74238e810a19b659e3aaf89fe67b86801127a2246d12ee9', 'owned_io.py': '09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb', 'preclaim01.py': '079df4afd2ad9cc0c303c400df48aca05f22fceba66fe363f0d0147bfe94800c', 'proof_reuse_contract01.json': '8fe5a1ace0b863dc90b59bd5e6754deb9054695192168dd1af6d36e37419549d', 'recovery04.py': 'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a', 'supervisor01.py': '551850d2af69baf48bc582f8fc7da7e7eba931c2b58abec4987a09e9ec270db0'}
sha=lambda b:hashlib.sha256(b).hexdigest()
enc=lambda v:(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def need(ok,text):
 if not ok:raise ValueError(text)
def digest(v,n):need(type(v)is str and re.fullmatch('[0-9a-f]{'+str(n)+'}',v)is not None,'exact digest')
def relative(n):
 need(type(n)is str and n and not n.startswith('/') and all(x not in ('','.','..') for x in n.split('/')) and '\\' not in n and '\n' not in n and '\0' not in n,'canonical source path')
class Reads:
 """Preparation-only64MiB total reads including finish; original runtime Reader stays8MiB."""
 def __init__(self):self.start=time.monotonic();self.charged=0;self.cache={}
 def tick(self):need(time.monotonic()-self.start<120,'preparation120s deadline');need(shutil.disk_usage(H).free>=10*1024**3,'10GiB floor')
 def read(self,p):
  self.tick();p=Path(p);need(p.is_absolute() and p.resolve()==p,'canonical input path')
  b=R.read(p.parent,p.name);self.charged+=len(b);need(self.charged<=64*1024**2,'preparation64MiB reads')
  previous=self.cache.get(str(p));need(previous is None or previous==b,'input changed across preparation');self.cache[str(p)]=b;self.tick();return b
 def ref(self,r):
  need(type(r)is dict and set(r)=={'path','sha256'},'exact reference');digest(r['sha256'],64);b=self.read(Path(r['path']));need(sha(b)==r['sha256'],'reference hash');return b
 def finish(self):
  for p in tuple(self.cache):self.read(Path(p))
  self.tick()
def validate_manifest(m):
 need(type(m)is dict and set(m)=={'schema_version','source','registration','registration_sha256','source_files','tracked_count'} and m['schema_version']==1,'closed source manifest schema')
 digest(m['source'],40);need(m['source']!=OLD_SOURCE,'future adopted source required');need(m['registration']==REG,'fixed new registration');digest(m['registration_sha256'],64)
 files=m['source_files'];need(type(files)is dict and files and REG not in files,'source map excluding only selected gate')
 for n,pin in files.items():relative(n);digest(pin,64)
 need(type(m['tracked_count'])is int and m['tracked_count']==len(files)+1,'actual source cardinality')
 need(files.get(OLD_GATE)==OLD_GATE_SHA,'original13 gate retained')
def validate_gate(g,base,source_map):
 expected=copy.deepcopy(base)
 for identity in (ID,PRED):expected['experiments'][identity]['source_files']=source_map
 need(g==expected,'only new selected source maps may differ from exact four-definition draft')
 need(len(g['experiments'][ID]['inputs'])==29,'29 continuation roles')
def validate_reuse(c,original,source,reader):
 need(type(c)is dict and set(c)==set(original),'reuse contract fields')
 for k,v in original.items():
  if k not in ('current_source','outcome_recovery'):need(c[k]==v,'immutable trusted proof-root contract')
 need(c['current_source']==source,'contract current source')
 recovery=json.loads(reader.ref(c['outcome_recovery']))
 need(set(recovery)=={'schema_version','kind','decision','source','identity','outcome_review_sha256','claim_sha256','terminal_sha256','checkpoint_sha256','review'},'actual100 recovery exact schema')
 expected={'schema_version':1,'kind':'complete100_outcome_recovery','decision':'accepted-actual-complete100-byte-recovery','source':OLD_SOURCE,'identity':REFERENCE,'outcome_review_sha256':'27e29cab0b784748bdd0fef2ca484215b39b2b025784a469de443f619ae9b124','claim_sha256':'c6c1106de459a89f9633ae51501959ecabd47c204534d85e9ebcf15671bcd19f','terminal_sha256':'bd54cb0052645e77fa7b0a4f943ab864798a4e05224ee530d4117b47f8f032c1','checkpoint_sha256':'2b127b8c08218783d8d20828c032e7443576465a64e07cf1415ed40e50916595'}
 need(all(recovery[k]==v for k,v in expected.items()),'genuine fixed complete100 ancestry')
 review=json.loads(reader.ref(recovery['review']))
 need(review['decision']=='ACCEPTED_ACTUAL_COMPATIBILITY_COMPLETE100_BYTE_RECOVERY' and review['source']==OLD_SOURCE and review['identity']==REFERENCE and review['outcome_review_sha256']==expected['outcome_review_sha256'],'genuine complete100 recovery review')
def build(manifest_ref,contract_ref):
 reader=Reads()
 for name,pin in PREPARATION_PINS.items():need(sha(reader.read(H/name))==pin,'frozen preparation dependency')
 m=json.loads(reader.ref(manifest_ref));validate_manifest(m)
 need(git(CAP,['rev-parse','HEAD'],cap=128).decode().strip()==m['source'],'actual adopted current/design source')
 tracked=git(CAP,['ls-tree','-r','--name-only',m['source']]).decode().splitlines()
 need(len(tracked)==m['tracked_count'] and set(tracked)==set(m['source_files'])|{REG},'whole actual source membership')
 base=json.loads(reader.read(H/'GATE4_DRAFT01.json'))
 oldgate=json.loads(reader.read(CAP/OLD_GATE));need(sha(reader.cache[str(CAP/OLD_GATE)])==OLD_GATE_SHA,'immutable original gate')
 oldmap=oldgate['experiments'][REFERENCE]['source_files']
 need(all(m['source_files'].get(n)==pin for n,pin in oldmap.items()),'every old source/input body remains exact')
 for n,pin in m['source_files'].items():need(sha(reader.read(CAP/n))==pin,'actual current source bytes')
 names=sorted(m['source_files'])
 for start in range(0,len(names),64):
  batch=names[start:start+64];raw=git(CAP,['cat-file','--batch'],''.join(m['source']+':'+n+'\n' for n in batch).encode());offset=0
  for name in batch:
   end=raw.index(b'\n',offset);oid,kind,size=raw[offset:end].decode().split();size=int(size);body=raw[end+1:end+1+size]
   need(kind=='blob' and 0<=size<=R.FILE and sha(body)==m['source_files'][name] and raw[end+1+size:end+2+size]==b'\n','actual committed source framing');offset=end+2+size
  need(offset==len(raw),'source Git tail')
 regraw=reader.read(CAP/REG);need(sha(regraw)==m['registration_sha256'] and git(CAP,['show',m['source']+':'+REG])==regraw,'committed selected registration');reg=json.loads(regraw);validate_gate(reg,base,m['source_files'])
 exp=reg['experiments'][ID]
 for ref in exp['inputs'].values():relative(ref['path']);need(sha(reader.read(CAP/ref['path']))==ref['sha256'],'every continuation input actual bytes')
 q=json.loads(reader.read(H/'REQUEST_DRAFT01.json'));target=Path(q['parent_root']);need(target.is_absolute() and target.resolve()==target and not os.path.lexists(target) and not target.is_relative_to(CAP) and not CAP.is_relative_to(target),'fresh fixed external Parent')
 need(not os.path.lexists(CAP/'research_runs'/ID) and not os.path.lexists(CAP/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/ID),'unspent unreserved continuation')
 template=reader.read(H/'parent01.py');need(sha(template)==q['caller_sha256'],'exact prepared Parent template')
 for n,pin in q['helper_hashes'].items():need(sha(reader.read(H/n))==pin,'exact prepared helper closure')
 original=json.loads(reader.cache[str(H/'proof_reuse_contract01.json')]);craw=reader.ref(contract_ref);c=json.loads(craw);validate_reuse(c,original,m['source'],reader)
 binding={'source':m['source'],'registration_sha256':m['registration_sha256'],'source_map_sha256':sha(R.encode(m['source_files'])),'source_count':len(m['source_files']),'tracked_count':m['tracked_count']}
 needle=b'SOURCE_BINDING=None';need(template.count(needle)==1,'one exact binding substitution');parent=template.replace(needle,('SOURCE_BINDING='+repr(binding)).encode())
 q.update(source=m['source'],design_source=m['source'],registration_sha256=m['registration_sha256'],source_files=m['source_files'],input_hashes={k:v['sha256'] for k,v in exp['inputs'].items()},caller_sha256=sha(parent))
 q['helper_hashes']['proof_reuse_contract01.json']=sha(craw)
 need(json.loads(reader.read(CAP/exp['inputs']['runtime_mapping']['path']))==q['runtime_mapping'],'same251 runtime mapping')
 reader.finish();need(git(CAP,['rev-parse','HEAD'],cap=128).decode().strip()==m['source'],'final actual source currentness');reader.tick()
 return {'status':'DRAFT_NOT_RELEASED','parent_source':parent.decode(),'request':q,'proof_reuse_contract_raw':craw.decode(),'binding':binding,'actual_reads_including_finish':reader.charged,'required_metadata_proof_field':{'continuation_trusted_proof_contract':{'path':str(target/'proof_reuse_contract01.json'),'sha256':sha(craw)}},'remaining_authority':{'independent_source_input_runtime':None,'full_recovery':None,'cumulative':None,'final_review':None,'full_public_preclaim':None,'native_release':None}}
def main():
 p=argparse.ArgumentParser();p.add_argument('--source-manifest',type=Path,required=True);p.add_argument('--source-manifest-sha256',required=True);p.add_argument('--reuse-contract',type=Path,required=True);p.add_argument('--reuse-contract-sha256',required=True);a=p.parse_args()
 result=build({'path':str(a.source_manifest),'sha256':a.source_manifest_sha256},{'path':str(a.reuse_contract),'sha256':a.reuse_contract_sha256})
 # Emission is a draft only. No directory creation, installation, admission or launch.
 raw=enc(result);offset=0
 while offset<len(raw):
  n=os.write(1,raw[offset:]);need(n>0,'stdout progress');offset+=n
if __name__=='__main__':main()
