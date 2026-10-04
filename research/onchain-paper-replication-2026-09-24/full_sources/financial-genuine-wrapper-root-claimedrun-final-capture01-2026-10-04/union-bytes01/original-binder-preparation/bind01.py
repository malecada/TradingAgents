"""Strict finite binder; does not execute the outcome verifier or launch a job."""
import argparse,ast,json,re,os
from pathlib import Path
import recovery04 as R
H=Path(__file__).resolve().parent
SOURCE='649fb8a11089524aaef7843dffeeb90a3a55ca17'
CAP='/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-native-20261004-01/source'
PARENT='/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-root-launch-20261004-01'
IDENTITY='financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01'
PARENT_HASH='82d79e1a99cff7be02fcd402661034f18eda749de870b6aa3a51f4994df4f578'
VERIFIER_HASH='f6626d0a66dba46e6b4a314c4806a0452844fda886375f5e99e99186b2ceaa56'
OLD_QHASH='dc80a4dff93fbf3261bdf151076c1420630ed38926ab7094d60eb1902bde25bc'
OLD_SOURCE='d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0'
PINS={'original-verifier03.py':VERIFIER_HASH,'accepted_parent01.py':PARENT_HASH,'SOURCE_ADOPTION01.json':'c08c065d3366441e94ae237cceab3fc35a1e83981f87e63a2e7085eab8523dc6','verifier-review/MANIFEST03.json':'434c9a4fa7f0e38d329b9ed4dc77a3e4fe9dade8c528dd21bb4f00f26d11e779','verifier-review/REVIEW03.json':'2c072bb513fbe1f07a38af0208fe134dad4fc1b383d603ab846123a5b39eca35','parent-review/MANIFEST01.json':'9b82e1c0b5acfdeae8ef5432159396dd911731a7a721be5bcc6cdbfdebc8e1dd','parent-review/REVIEW01.json':'742787d225173a699a9309fe8a4c9ccea964079ba0b36c7592c5b9342772e41c'}

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
 ad=json.loads(R.read(H,'SOURCE_ADOPTION01.json'))
 R.require(q['source_files']==ad['source_files'] and len(q['source_files'])==324 and q['registration']==ad['registration'] and q['registration_sha256']==ad['registration_sha256'],'actual Source325 selected324/gate binding')
 R.require(type(q['input_hashes'])is dict and q['input_hashes']=={Path(n).stem:pin for n,pin in ad['role_hashes'].items()} and len(q['input_hashes'])==8,'eight actual input pins')


def rewrite(original,request_hash,request_name):
 """Pure source transformation only; by itself grants no authenticated binding."""
 R.require(R.digest(original)==VERIFIER_HASH,'unchanged verifier03')
 h(request_hash);R.require(request_hash!=OLD_QHASH,'old request permanently refused')
 R.require(type(request_name)is str and re.fullmatch(r'REQUEST_FINAL[0-9]{2}\.json',request_name) is not None,'actual final request basename')
 text=original.decode();edits=[]
 for old,new in [("QHASH='"+OLD_QHASH+"'","QHASH='"+request_hash+"'"),("par.value('REQUEST_FINAL03.json',QHASH)","par.value("+repr(request_name)+",QHASH)"),("source==q['design_source']=='"+OLD_SOURCE+"'","source==q['design_source']=='"+SOURCE+"'")]:
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
 out=H/'generated-recordfix01';R.require(not os.path.lexists(out),'one-use binding output');out.mkdir(mode=0o700)
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
