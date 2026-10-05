"""One exact same-family source/gate adoption; no numerical execution or release."""
from pathlib import Path
import ast,copy,hashlib,json,os,subprocess
root=Path.cwd();F=root/'research/onchain-paper-replication-2026-09-24/full_sources';C=F/'heartbeat-root-checkpoint10-2026-10-04';A=F/'financial-wrapper-serialized-storage-binding-source01-2026-10-05';D=F/'financial-wrapper-serialized-storage-root-preparation01-2026-10-05';V=F/'financial-wrapper-serialized-storage-binding-review01-2026-10-05';remote=F/'financial-wrapper-serialized-storage-source-remote02-2026-10-05'
cap=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');parent=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-serialized-storage-root-launch-20261005-01');oldparent=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-resource-successor-root-launch-20261005-01');identity='financial-wrapper-classification-eager-continue100-serialized-storage-successor-20261005-01';oldid='financial-wrapper-classification-eager-continue100-resource-successor-20261005-01';prefix='tradingagents/research/onchain_replication/';relative='fixture_inputs/financial_wrapper_serialized_storage01';directory=cap/relative;registration=directory/'gates.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def compact(v):return (json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
def put(p,b):
 with p.open('xb') as w:w.write(b)
def git(args):return subprocess.run(['git',*args],cwd=cap,capture_output=True,check=True).stdout
assert git(['rev-parse','HEAD']).decode().strip()=='a5bcc943167ad035b45e12ddf9864d46e685b124'
assert git(['status','--short','--untracked-files=no'])==b''
assert not os.path.lexists(parent) and not os.path.lexists(directory) and not os.path.lexists(cap/'research_runs'/identity) and not os.path.lexists(cap/'research_artifacts/financial_wrapper_engineering'/identity)
assert {x.name for x in (cap/'research_runs').iterdir()}=={'.lock','financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01','financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01','financial-wrapper-classification-eager-complete100-20261003-01','financial-wrapper-classification-eager-complete100-compatibility-20261004-01'}
assert sha((A/'MANIFEST01.json').read_bytes())=='e97d4e2b00e73165cf35d29d0fd9669f2be73c8bb0af227b118b449c236660b0'
review=(V/'SOURCE_REVIEW_PROOF01.json').read_bytes();assert sha(review)=='a6e7e6ce57d2b8efb7098a64a9d8bc7a24cb007cb8d1754c3423ea5478398bc3'
recovery=(V/'SOURCE_RECOVERY_PROOF01.json').read_bytes();remote_review=json.loads((V/'SOURCE_REMOTE_CHECK01.json').read_bytes());receipt=json.loads((remote/'REMOTE_RECOVERY01.json').read_bytes());assert remote_review['decision']=='accepted-actual-serialized-storage-source-byte-recovery' and receipt['selected_count']==48 and receipt['selected_logical_bytes']==3839470 and remote_review['receipt_sha256']==sha((remote/'REMOTE_RECOVERY01.json').read_bytes())
edge=json.loads((D/relative/'successor.json').read_bytes());policy=json.loads((cap/'fixture_inputs/financial_wrapper_compatibility01/policy.json').read_bytes())
base={'schema_version':1,'decision':'accepted','policy_sha256':sha((D/relative/'successor.json').read_bytes()),'original_policy_sha256':edge['original_policy_sha256'],'historical_map_sha256':sha(json.dumps(policy['target']['installed'],sort_keys=True,separators=(',',':')).encode()),'target_map_sha256':sha(json.dumps(edge['installed'],sort_keys=True,separators=(',',':')).encode()),'checker_sha256':edge['installed'][prefix+'operational_source_compatibility.py'],'refusal_sha256':'2263ea2cd9f6e6b2fe6100498a917fb971328d9e4ae3478e4f544a07f93d908b'}
assert json.loads(review)==dict(base,kind='continuation_source_successor_review') and json.loads(recovery)==dict(base,kind='continuation_source_successor_recovery')
helper=A/'operational_source_compatibility.py';before=(cap/(prefix+helper.name)).read_bytes();body=helper.read_bytes();assert sha(before)=='d97cd1f62d1958fb2de77eebae42c8e22d4c24e754157335e85936999225ee54' and sha(body)==base['checker_sha256'];ast.parse(body)
for p in (helper,D/relative/'successor.json',D/relative/'source_closure.json',D/relative/'continue-plan.json'):
 recovered=remote/'selected'/p.relative_to(root);assert recovered.read_bytes()==p.read_bytes()
oldraw=(cap/'fixture_inputs/financial_wrapper_continuation_successor01/gates.json').read_bytes();assert sha(oldraw)=='995d56529860ce1ce63191ac17f29e1176525dae3930a74d6011b7092a0b51d7';oldgate=json.loads(oldraw);gate=json.loads((D/'GATES_UNBOUND_DRAFT01.json').read_bytes());assert {k:v for k,v in gate['experiments'].items() if k!=identity}==oldgate['experiments']
put(C/'SERIALIZED_ADOPTION_INTENT01.json',enc({'schema_version':1,'old_source':'a5bcc943167ad035b45e12ddf9864d46e685b124','identity':identity,'source_review_sha256':sha(review),'source_recovery_sha256':sha(recovery),'root_only_integration':True,'claim':False,'numerical_import':False}))
(cap/(prefix+helper.name)).write_bytes(body);directory.mkdir(mode=0o700)
for name in ('successor.json','source_closure.json','continue-plan.json','refusal.json','previous-recovery.json'):put(directory/name,(D/relative/name).read_bytes())
put(directory/'successor-review.json',review);put(directory/'successor-recovery.json',recovery)
exp=gate['experiments'][identity]
for role,name in (('continuation_source_successor_review','successor-review.json'),('continuation_source_successor_recovery','successor-recovery.json')):exp['inputs'][role]['sha256']=sha((directory/name).read_bytes())
names=git(['ls-tree','-r','--name-only','HEAD']).decode().splitlines();assert len(names)==367
names=sorted(set(names)|{x.relative_to(cap).as_posix() for x in directory.iterdir()});assert len(names)==374
exp['source_files']={n:sha((cap/n).read_bytes()) for n in names};assert len(exp['inputs'])==36
for name,pin in edge['installed'].items():assert exp['source_files'][name]==pin
for role,ref in exp['inputs'].items():assert sha((cap/ref['path']).read_bytes())==ref['sha256']
put(registration,compact(gate));git(['add','--',prefix+helper.name,*[x.relative_to(cap).as_posix() for x in sorted(directory.iterdir())]]);git(['diff','--cached','--check']);git(['commit','-q','-m','engineering: register serialized storage continuation successor'])
source=git(['rev-parse','HEAD']).decode().strip();tracked=git(['ls-tree','-r','--name-only','HEAD']).decode().splitlines();assert len(tracked)==375 and set(tracked)==set(exp['source_files'])|{relative+'/gates.json'}
parent.mkdir(mode=0o700)
for name in ('supervisor01.py','descendants01.py','recovery04.py','owned_io.py','bounded_git01.py','PROTOCOL_PINS01.json'):put(parent/name,(oldparent/name).read_bytes())
put(parent/'preclaim01.py',(A/'preclaim01.py').read_bytes())
reuse=json.loads((oldparent/'proof_reuse_contract01.json').read_bytes());reuse['consumer']=identity;reuse['current_source']=source;put(parent/'proof_reuse_contract01.json',compact(reuse))
binding={'source':source,'registration_sha256':sha(registration.read_bytes()),'source_map_sha256':sha(enc(exp['source_files'])),'source_count':374,'tracked_count':375}
s=(D/'parent-unbound01.py').read_text();assert s.count('SOURCE_BINDING=None')==1;s=s.replace('SOURCE_BINDING=None','SOURCE_BINDING='+repr(binding));ast.parse(s);put(parent/'parent01.py',s.encode())
q=json.loads((D/'REQUEST_UNBOUND_DRAFT01.json').read_bytes());q.update(source=source,design_source=source,registration_sha256=binding['registration_sha256'],source_files=exp['source_files'],input_hashes={k:v['sha256'] for k,v in exp['inputs'].items()},caller_sha256=sha(s.encode()),helper_hashes={name:sha((parent/name).read_bytes()) for name in ('supervisor01.py','descendants01.py','recovery04.py','owned_io.py','bounded_git01.py','PROTOCOL_PINS01.json','preclaim01.py','proof_reuse_contract01.json')});put(parent/'REQUEST_SOURCE_BOUND_DRAFT01.json',compact(q))
record={'schema_version':1,'status':'SOURCE_GATE_ADOPTED_DRAFT_NOT_RELEASED','source':source,'design_source':source,'tracked_count':375,'selected_source_count':374,'input_count':36,'installed_count':195,'changed_installed':1,'old_definitions_unchanged':5,'registration':relative+'/gates.json','registration_sha256':binding['registration_sha256'],'source_map_sha256':binding['source_map_sha256'],'caller_sha256':q['caller_sha256'],'recovery_proof_sha256':sha(recovery),'claim':False,'numerical_import':False,'pending':'genuine read-only admission; actual current capsule/Git/caller/released-envelope incremental recovery; exact independent final release and full preflight'};put(C/'SERIALIZED_SOURCE_GATE_ADOPTION01.json',compact(record));print(json.dumps(record,sort_keys=True))
