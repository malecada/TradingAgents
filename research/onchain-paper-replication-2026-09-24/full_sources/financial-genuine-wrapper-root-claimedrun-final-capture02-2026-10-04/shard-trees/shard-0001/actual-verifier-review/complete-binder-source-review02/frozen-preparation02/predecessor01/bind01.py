"""Strict finite binder; does not execute the outcome verifier or launch a job."""
import argparse,ast,json,re,os
from pathlib import Path
import recovery04 as R
H=Path(__file__).resolve().parent
SOURCE='0a2e7639b42b9423b90743feadcda4078aa21816'
CAP='/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source'
PARENT='/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-root-launch-20261004-01'
IDENTITY='financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01'
PARENT_HASH='5d5cbdae455c62c3e66b53208b0f79e6e5bbc7ce05d3ded77126da5e0692deda'
VERIFIER_HASH='f6626d0a66dba46e6b4a314c4806a0452844fda886375f5e99e99186b2ceaa56'
OLD_QHASH='dc80a4dff93fbf3261bdf151076c1420630ed38926ab7094d60eb1902bde25bc'
OLD_SOURCE='d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0'
PINS={'original-verifier03.py': 'f6626d0a66dba46e6b4a314c4806a0452844fda886375f5e99e99186b2ceaa56', 'accepted_parent01.py': '5d5cbdae455c62c3e66b53208b0f79e6e5bbc7ce05d3ded77126da5e0692deda', 'ACTUAL_PARENT_DRAFT01.json': 'b1087b980a44fcc4cd920cdcbd472f092ba17223d0a329cbc74b52a8e0236c98', 'verifier-review/MANIFEST03.json': '434c9a4fa7f0e38d329b9ed4dc77a3e4fe9dade8c528dd21bb4f00f26d11e779', 'verifier-review/REVIEW03.json': '2c072bb513fbe1f07a38af0208fe134dad4fc1b383d603ab846123a5b39eca35', 'parent-review/MANIFEST01.json': '034d5977ba0327a425fb4d99ebf7deda3fec78ab55ff1fd7a971c2cf9ec34f71', 'parent-review/READBACK01.json': 'a3327cc9125d8f66598b94a30510993de30e69059aed4a9b4acd48895ced520c'}

ACCOUNTING_EDITS=[("claim['effective_attempt_budget']==18", "claim['effective_attempt_budget']==19"), ("require(len(relevant)==1 and relevant[0]['identity']==identity,'first case root claim denominator changed')", "require(len(relevant)==2 and {r['identity'] for r in relevant}=={identity,'financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01'},'original failed and new spent claim denominator changed')"), (" for n,h in q['source_files'].items():cap.raw(n,h)", " old_run='research_runs/financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01'\n cap.raw(old_run+'/claim.json','4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128');cap.raw(old_run+'/failed.json','35158c0ecebfe4dc75203ba87d5372f2f85643c0b5f828a99e17aa28fe79c450');require(cap.absent(old_run+'/complete.json'),'original failed claim cannot become complete')\n for n,h in q['source_files'].items():cap.raw(n,h)")]

def h(v):R.require(type(v)is str and re.fullmatch('[0-9a-f]{64}',v) is not None,'exact sha256');return v

def prepared():
 for n,pin in PINS.items():R.require(R.digest(R.read(H,n))==pin,'accepted preparation pin '+n)
 # Only the accepted pure read-only release validation is invoked later.
 import accepted_parent01 as P
 R.require(Path(P.__file__).resolve()==H/'accepted_parent01.py','accepted parent module origin')
 return P

def fixed(q):
 R.require(q['source']==q['design_source']==SOURCE and q['identity']==IDENTITY and q['expected_phase']=='interrupt1','fixed new source/design/identity/phase')
 R.require(q['capsule_root']==CAP and q['parent_root']==PARENT and q['caller_sha256']==PARENT_HASH,'actual fixed parent binding')
 R.require(q['status']=='RELEASED_ONE_USE_FINANCIAL_PARENT' and q['final_review'] is not None,'actual accepted parent release required')
 ad=json.loads(R.read(H,'ACTUAL_PARENT_DRAFT01.json'))
 R.require(q['source_files']==ad['source_files'] and len(q['source_files'])==338 and q['registration']==ad['registration'] and q['registration_sha256']==ad['registration_sha256'],'actual Source339 selected338/gate binding')
 R.require(type(q['input_hashes'])is dict and q['input_hashes']==ad['input_hashes'] and len(q['input_hashes'])==8,'eight actual input pins')
 R.require(q['runtime_mapping']==ad['runtime_mapping'] and q['helper_hashes']==ad['helper_hashes'],'original runtime and helper closure')
 for role in ('cumulative','independent_source_input_runtime'):R.require(q['proofs'][role]['sha256']==ad['proofs'][role]['sha256'],'actual fixed proof pin')


def rewrite(original,request_hash,request_name):
 """Pure source transformation only; by itself grants no authenticated binding."""
 R.require(R.digest(original)==VERIFIER_HASH,'unchanged verifier03')
 h(request_hash);R.require(request_hash!=OLD_QHASH,'old request permanently refused')
 R.require(type(request_name)is str and re.fullmatch(r'REQUEST_FINAL[0-9]{2}\.json',request_name) is not None,'actual final request basename')
 text=original.decode();edits=[]
 for old,new in [("QHASH='"+OLD_QHASH+"'","QHASH='"+request_hash+"'"),("par.value('REQUEST_FINAL03.json',QHASH)","par.value("+repr(request_name)+",QHASH)"),("source==q['design_source']=='"+OLD_SOURCE+"'","source==q['design_source']=='"+SOURCE+"'"),*ACCOUNTING_EDITS]:
  if old==new:continue
  R.require(text.count(old)==1,'exact sole binding literal');text=text.replace(old,new);edits.append({'old':old,'new':new})
 inverse=text
 for row in reversed(edits):R.require(inverse.count(row['new'])==1,'unique inverse');inverse=inverse.replace(row['new'],row['old'])
 R.require(inverse.encode()==original and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(original)),'complete source inverse')
 return text.encode(),edits

def authenticate(path,pin):
 P=prepared();h(pin);R.require(pin!=OLD_QHASH,'old request forbidden');path=Path(path)
 R.require(path.parent==Path(PARENT) and path.resolve()==path,'actual fixed Parent request path');raw=R.read(path.parent,path.name);R.require(R.digest(raw)==pin,'actual request pin');q=json.loads(raw);fixed(q)
 # Every referenced proof must be genuinely present within the installed Parent.
 for ref in [*q['proofs'].values(),q['final_review']]:
  p=Path(ref['path']);R.require(p.is_relative_to(Path(PARENT)) and p.resolve()==p,'actual Parent-contained proof');R.require(R.digest(R.read(Path(PARENT),p.relative_to(PARENT).as_posix()))==h(ref['sha256']),'actual proof pin')
 P.validate_release(q)
 R.require(R.digest(R.read(Path(PARENT),'parent01.py'))==PARENT_HASH,'actual installed accepted Parent body')
 R.require(set(q['helper_hashes'])=={'supervisor01.py','descendants01.py','recovery04.py','owned_io.py','bounded_git01.py','PROTOCOL_PINS01.json'},'actual six helper denominator')
 for n,pin in q['helper_hashes'].items():R.require(R.digest(R.read(Path(PARENT),n))==pin==R.digest(R.read(H,n)),'actual unchanged helper body')
 return raw,q

def generate(path,pin):
 raw,q=authenticate(path,pin);source,edits=rewrite(R.read(H,'original-verifier03.py'),pin,Path(path).name)
 return {'source':source,'request':raw,'request_name':Path(path).name,'inverse':edits,'binding':{'source':SOURCE,'identity':IDENTITY,'parent_source_sha256':PARENT_HASH,'actual_request_sha256':pin,'final_parent_review':q['final_review'],'verifier_sha256':R.digest(source),'outcome_classified':False,'numerical_authority':False}}

def emit(path,pin):
 value=generate(path,pin)
 out=H/'generated-claimedrun01';R.require(not os.path.lexists(out),'one-use binding output');out.mkdir(mode=0o700)
 # Root alone adopts generated files; never write a live Source or Parent.
 def write(name,raw):
  R.require(len(raw)<=R.FILE,'bounded emitted body')
  with R.new_file(out/name) as fd:
   offset=0
   while offset<len(raw):
    count=os.write(fd,raw[offset:]);R.require(count>0,'short write');offset+=count
   os.fsync(fd)
 write('verifier01.py',value['source']);write(value['request_name'],value['request'])
 R.put(out/'BINDING01.json',value['binding']);R.put(out/'INVERSE01.json',{'edits':value['inverse']})
 for n in ('recovery04.py','owned_io.py','bounded_git01.py'):
  write(n,R.read(H,n))
 return out

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True);p.add_argument('--sha256',required=True);a=p.parse_args();print(emit(a.request,a.sha256))
