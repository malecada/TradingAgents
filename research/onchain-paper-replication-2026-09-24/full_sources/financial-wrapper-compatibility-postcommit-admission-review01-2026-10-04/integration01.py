"""Read-only genuine Admission/job integration, never lifecycle entry."""
import json,os,sys,types,hashlib
from pathlib import Path
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');SOURCE='32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41';IDENT='financial-wrapper-classification-eager-complete100-compatibility-20261004-01'
class BlockNumerics:
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0] in {'numpy','torch','scipy','pandas','pyarrow','sklearn'}:raise RuntimeError('forbidden numerical import '+fullname)
sys.meta_path.insert(0,BlockNumerics());sys.path.insert(0,str(CAP));os.environ['GIT_NO_LAZY_FETCH']='1';os.environ['GIT_ALLOW_PROTOCOL']=''
def audit(event,args):
 if event=='open':
  path,mode,flags=args
  if flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):raise RuntimeError('read-only integration open denied')
 if event in {'os.mkdir','os.rename','os.remove','os.rmdir','os.chmod','os.link','os.symlink','os.truncate'}:raise RuntimeError('read-only integration mutation denied')
sys.addaudithook(audit)
from tradingagents.research.admission import Admission
from tradingagents.research.onchain_replication import job,financial_wrapper_fixture
args=types.SimpleNamespace(root=str(CAP),registration='fixture_inputs/financial_wrapper_compatibility01/gates.json',experiment=IDENT,source=SOURCE)
ad,j=job._admitted(args);assert type(ad) is Admission and ad.ready and ad.source==SOURCE
origins={}
for n,m in sorted(sys.modules.items()):
 if n=='tradingagents' or n.startswith('tradingagents.'):
  p=Path(m.__file__).resolve();assert p.is_relative_to(CAP);origins[n]={'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
assert not (CAP/'research_runs'/IDENT).exists();assert not ({'numpy','torch','scipy','pandas','pyarrow','sklearn'}&set(sys.modules))
rt=json.loads((CAP/'fixture_inputs/financial_wrapper_compatibility01/runtime_mapping.json').read_bytes());rows=[financial_wrapper_fixture._runtime_record(x) for x in rt['distribution_records']]
print(json.dumps({'status':'GENUINE_READ_ONLY_JOB_ADMITTED','type':type(ad).__module__+'.'+type(ad).__name__,'ready':ad.ready,'source':ad.source,'experiment':ad.experiment_id,'inputs':len(ad.inputs),'source_pins':len(ad.experiment['source_files']),'required_sources':len(job.required_sources()),'package_bodies':len(list((CAP/'tradingagents/research/onchain_replication').glob('*.py'))),'module_origins':origins,'runtime_records':rows,'runtime_mapping':rt,'job':j,'run_started':False,'claim_absent':True,'numerical_imports':[],'runtime_qualification':'Exact interpreter/lock/distribution RECORD and METADATA origins only; dependency bodies not fully rehashed.'},indent=2))
