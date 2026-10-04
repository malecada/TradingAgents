"""Root-only, exclusive composition of an unreleased financial parent."""
import hashlib,json,os,stat,sys
from pathlib import Path

MAIN=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
BASE=MAIN/'research/onchain-paper-replication-2026-09-24/full_sources'
PREP=BASE/'financial-genuine-wrapper-parent-preparation03-2026-10-04'
OUT=Path(__file__).resolve().parent
PARENT=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-root-launch-20261004-01')
CAP=PARENT.parent/'genuine-financial-wrapper-native-20261003-01/source'
SOURCE='d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0'
IDENTITY='financial-wrapper-classification-eager-interrupt1-20261003-01'
REG='fixture_inputs/financial_wrapper_registration01/gates.json'
sys.path.insert(0,str(PREP))
import recovery04 as R
from bounded_git01 import git

def sha(raw):return hashlib.sha256(raw).hexdigest()
def body(p):return R.read(p.parent,p.name)
def require(ok,msg):R.require(ok,msg)
def ref(p):return {'path':str(p),'sha256':sha(body(p))}
def write(p,raw):
 require(len(raw)<=R.FILE,'bounded output')
 with R.new_file(p) as fd:
  left=memoryview(raw)
  while left:
   n=os.write(fd,left);require(n>0,'short write');left=left[n:]
  os.fsync(fd)
 require(body(p)==raw,'exclusive copied body')

def main():
 require(sys.executable==str(MAIN/'.venv/bin/python'),'pinned interpreter')
 require(sha(body(PREP/'MANIFEST01.json'))=='3c6c8ef58e93de1a314a105b77e0b452267494487c971c73f925f98615ad78de','accepted parent manifest')
 review=BASE/'financial-genuine-wrapper-parent-review03-2026-10-04/MANIFEST01.json'
 require(sha(body(review))=='c5c37ae65524e7033e1b5174d7391bdfd87704ee8576390c44c8236422c59af6','independent parent review')
 manifest=json.loads(body(PREP/'MANIFEST01.json'))
 # Join copied helpers to the accepted complete preparation, not fresh defaults.
 rows={r['path']:r for r in manifest['entries']}
 names=['parent01.py','supervisor01.py','descendants01.py','recovery04.py','owned_io.py','bounded_git01.py','PROTOCOL_PINS01.json']
 for n in names:require(sha(body(PREP/n))==rows[n]['sha256'],'accepted helper '+n)
 require(PARENT.parent.resolve()==PARENT.parent and not os.path.lexists(PARENT),'fresh external parent')
 require(CAP.resolve()==CAP and not PARENT.is_relative_to(CAP) and not CAP.is_relative_to(PARENT),'disjoint owner roots')
 require(git(CAP,['rev-parse','HEAD'],cap=128).decode().strip()==SOURCE,'current source')
 require(git(CAP,['status','--porcelain'],cap=65536)==b'','closed clean source')
 tracked=git(CAP,['ls-files','-z']).decode().rstrip('\0').split('\0');require(len(tracked)==290,'complete source290')
 raw=body(CAP/REG);require(sha(raw)=='6818dfdc48879fde8bf149bd1dae252885c6460a209e31af5a17a66012247691','actual committed gate')
 gate=json.loads(raw);exp=gate['experiments'][IDENTITY]
 require(len(exp['source_files'])==289 and len(exp['inputs'])==8 and len(gate['experiments'])==10,'initial exact scope')
 require(set(exp['source_files'])==set(tracked)-{REG},'no omitted tracked source')
 for n,h in exp['source_files'].items():require(sha(R.read(CAP,n))==h,'actual source '+n)
 for r in exp['inputs'].values():require(sha(R.read(CAP,r['path']))==r['sha256'],'input hash')
 orderpath=BASE/'financial-genuine-wrapper-root-gate-adoption01-2026-10-04/FIXED_ORDER01.json'
 order=json.loads(body(orderpath));require(order['first_initial']==IDENTITY and order['complete18_topological_order'][0]==IDENTITY and order['actual_source']==SOURCE,'fixed first slot')
 PARENT.mkdir(mode=0o700)
 for n in names:write(PARENT/n,body(PREP/n))
 (PARENT/'proofs').mkdir(mode=0o700)
 proof_origins={
  'CUMULATIVE_REVIEW01.json':BASE/'financial-genuine-wrapper-cumulative-admission-review01-2026-10-04/REVIEW01.json',
  'INSTALLED_ADMISSION_REVIEW01.json':BASE/'financial-genuine-wrapper-installed-gate-admission-review01-2026-10-04/READBACK01.json',
  'ACTUAL_ADMISSION02.json':BASE/'financial-genuine-wrapper-root-readonly-admission01-2026-10-04/READBACK02.json',
  'PARENT_REVIEW_MANIFEST01.json':review,
  'ADMISSION_REVIEW_MANIFEST01.json':BASE/'financial-genuine-wrapper-installed-gate-admission-review01-2026-10-04/MANIFEST01.json',
 }
 for n,p in proof_origins.items():write(PARENT/'proofs'/n,body(p))
 write(PARENT/'CASE_ORDER01.json',body(orderpath))
 q=json.loads(body(PREP/'REQUEST_TEMPLATE01.json'))
 q.update(parent_root=str(PARENT),identity=IDENTITY,source=SOURCE,design_source=SOURCE,registration=REG,registration_sha256=sha(raw),source_files=exp['source_files'],input_hashes={k:v['sha256'] for k,v in exp['inputs'].items()},runtime_mapping=json.loads(R.read(CAP,exp['inputs']['runtime_mapping']['path'])),caller_sha256=sha(body(PARENT/'parent01.py')),helper_hashes={n:sha(body(PARENT/n)) for n in names if n!='parent01.py'},expected_phase='interrupt1',proofs={'cumulative':ref(PARENT/'proofs/CUMULATIVE_REVIEW01.json'),'independent_source_input_runtime':ref(PARENT/'proofs/INSTALLED_ADMISSION_REVIEW01.json'),'full_recovery':None})
 require(q['status']=='DRAFT_NOT_RELEASED' and q['final_review'] is None,'no release authority')
 write(PARENT/'REQUEST_DRAFT01.json',R.encode(q))
 source_manifest=R.scan(CAP);parent_manifest=R.scan(PARENT)
 R.put(OUT/'SOURCE_MANIFEST01.json',source_manifest);R.put(OUT/'PARENT_MANIFEST01.json',parent_manifest)
 R.put(OUT/'COMPOSITION01.json',{'status':'ACTUALLY_COMPOSED_UNRELEASED','source':SOURCE,'tracked':290,'source_pins':289,'implementation':194,'package':149,'paper_fit_credit':0,'identity':IDENTITY,'claim_started':False,'caller':ref(PARENT/'parent01.py'),'request':ref(PARENT/'REQUEST_DRAFT01.json'),'fixed_order':ref(PARENT/'CASE_ORDER01.json'),'helper_hashes':q['helper_hashes'],'proof_origins':{n:ref(p) for n,p in proof_origins.items()},'source_manifest':ref(OUT/'SOURCE_MANIFEST01.json'),'parent_manifest':ref(OUT/'PARENT_MANIFEST01.json'),'remaining':['complete current source290 and parent archive capture','actual fresh external and flat complete recovery','independent actual recovery acceptance','exact final caller/release binding and review','fresh native/source/runtime/namespace/resource eligibility before one numerical launcher'],'shared_runtime_bodies_recovered':False})
 require(not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')),'no numerical imports')
 R.same(CAP,source_manifest);R.same(PARENT,parent_manifest)
 print(json.dumps({'status':'unreleased composition complete','tracked':290,'source_pins':289,'parent_members':len(parent_manifest['members']),'source_members':len(source_manifest['members'])}))
if __name__=='__main__':main()
