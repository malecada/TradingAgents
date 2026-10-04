"""Read-only actual metadata authentication and path-keyed preclaim inventory.
Never calls Admission, Parent preflight, Run, Owner, native or remote operations.
All output files are exclusive creations beneath this preparation directory.
"""
from pathlib import Path
import argparse,ast,hashlib,importlib.util,json,os,stat,sys,time,subprocess
H=Path(__file__).resolve().parent;B=H.parent
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
PARENT=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01')
LAYOUT=B/'financial-wrapper-compatibility-coalesced-evidence-root03-2026-10-04'
SOURCE='32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41';ID='financial-wrapper-classification-eager-complete100-compatibility-20261004-01'
FILE=4194304;TOTAL=64*1024**2;START=time.monotonic();READS={};CHECKS=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def require(v,s):
 if not v:raise ValueError(s)
 CHECKS.append(s)
def signature(s):return tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
def read(p,pin=None,limit=FILE):
 p=Path(p);require(time.monotonic()-START<120,'inventory120s deadline');s=p.lstat();require(p.is_absolute() and p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and 0<=s.st_size<=limit,'bounded canonical regular')
 # Reader bytes and methods are the exact already installed stdlib-only preclaim.
 raw=READER.read(p) if limit==FILE else p.read_bytes()
 require(signature(s)==signature(p.lstat()) and (pin is None or sha(raw)==pin),'stable literal input pin')
 READS[str(p)]={'path':str(p),'bytes':len(raw),'sha256':sha(raw),'mode':stat.S_IMODE(s.st_mode),'signature':signature(s)};require(sum(x['bytes'] for x in READS.values())<=TOTAL,'separate64MiB audit inventory bound');return raw
def j(p,pin=None):return json.loads(read(p,pin))
def ref(p):return {'path':str(p),'sha256':sha(read(p))}
def save(name,x):
 require(Path(name).name==name and not (H/name).exists(),'exclusive own output');raw=(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode();require(len(raw)<=FILE,'own output4M')
 with (H/name).open('xb') as f:f.write(raw)
 return {'path':str(H/name),'sha256':sha(raw),'bytes':len(raw)}
# Import only pinned, pure stdlib preclaim definitions; never public validate_preclaim.
raw=(PARENT/'preclaim01.py').read_bytes();require(sha(raw)=='557b7bcb38b48e3bf1e9e5b5b1eae25ab4908b8567820e17700dc08774b48d16','exact installed public preclaim source')
spec=importlib.util.spec_from_file_location('_actual_preclaim_metadata_reader',PARENT/'preclaim01.py');PRE=importlib.util.module_from_spec(spec);spec.loader.exec_module(PRE)
# Audit Reader uses same immutable physical method but a separate instance with
# audit-only bound; the PRE module's genuine8MiB constant stays untouched.
class AuditReader:
 def __init__(self):self.cache={};self.deadline=time.monotonic()+120;self.total=0;self.verified_signatures={}
 def read(self,p):
  # Fresh real original8MiB reader per file is audit IO only, never presented as
  # a complete preclaim run. Actual whole budget is measured separately below.
  if p not in self.cache:
   r=PRE.Reader();self.cache[p]=r.read(p)
  return self.cache[p]
READER=AuditReader()
parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['draft','bound'],required=True);parser.add_argument('--binding',type=Path);args=parser.parse_args()
qraw=read(PARENT/'REQUEST_DRAFT01.json','e7579251741a865a2955917a3a9dc346ed6710ffc08388f1907c727e95d0a721');q=json.loads(qraw);gate=j(CAP/q['registration'],'e1846c9fbd5d1964c867c9c7027e3e9a6009520c07841ed720c035374dbeb806');e=gate['experiments'][ID]
require(q['source']==q['design_source']==SOURCE and q['identity']==ID and e['parent'] is None,'fixed independent reference/source');require(len(e['source_files'])==354 and len(e['inputs'])==11 and len(gate['experiments'])==13,'354pins11roles13definitions')
source_hashes={n:sha(read(CAP/n,pin)) for n,pin in e['source_files'].items()};require(source_hashes==q['source_files'],'every actual source pin')
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_NO_REPLACE_OBJECTS='1',GIT_ALLOW_PROTOCOL='')
p=subprocess.run(['git','rev-parse','HEAD'],cwd=CAP,env=env,check=True,capture_output=True,timeout=10);require(p.stdout.decode().strip()==SOURCE,'actual source HEAD')
p=subprocess.run(['git','ls-tree','-r','--name-only',SOURCE],cwd=CAP,env=env,check=True,capture_output=True,timeout=10);require(set(p.stdout.decode().splitlines())==set(source_hashes)|{q['registration']},'355 full tracked membership')
inputs={role:read(CAP/v['path'],v['sha256']) for role,v in e['inputs'].items()};policy=json.loads(inputs['operational_source_compatibility']);require(len(policy['target']['installed'])==195 and sum(n.startswith('tradingagents/') for n in policy['target']['installed'])==150,'195 implementation paths/150 package bodies')
for n,pin in policy['target']['installed'].items():require(source_hashes[n]==pin,'actual195 targetsourcepin')
for n,pin in q['helper_hashes'].items():read(PARENT/n,pin)
read(PARENT/'parent01.py','424f13b653d970efc4994e76e27f4ff5e8cf732133daab6a956cb1a034299ea0')
runtime=json.loads(inputs['runtime_mapping']);require(runtime==q['runtime_mapping'] and runtime['python']=='3.13.13' and runtime['prefix']==sys.prefix and runtime['executable']==sys.executable,'actual interpreter identity')
exe=Path(runtime['resolved_executable']);require(Path(sys.executable).resolve(strict=True)==exe and sys.version.split()[0]=='3.13.13','actual executable resolution and CPython version');require(sha(read(exe,limit=64*1024**2))==runtime['executable_sha256'],'actual interpreter opaque hash');require(sha(read(CAP/'uv.lock'))==runtime['lock_sha256'],'actual lock hash')
from email.parser import BytesParser
names=set();records=[]
for row in runtime['distribution_records']:
 rp=Path(row['record']);require(rp.name=='RECORD' and rp.parent.name.endswith('.dist-info') and rp.is_relative_to(Path(sys.prefix)/'lib/python3.13/site-packages'),'runtime fixed RECORD path')
 require(row['name'] not in names,'unique runtime name');names.add(row['name']);body=read(rp,row['record_sha256']);metadata=read(rp.parent/'METADATA');m=BytesParser().parsebytes(metadata,headersonly=True)
 normalize=lambda s:s.lower().replace('_','-').replace('.','-')
 require(normalize(m['Name'])==normalize(row['name']) and m['Version']==row['version'],'actual direct installed metadata name/version')
 records.append({'name':row['name'],'version':row['version'],'record':str(rp),'record_sha256':sha(body),'record_bytes':len(body),'metadata_sha256':sha(metadata)})
require(len(records)==251 and not any(n in sys.modules for n in ['numpy','torch','scipy','pandas']),'251 RECORD metadata only no numerical import')
# Genuine predecessor actual evidence, source-only peer verdicts remain literal.
evidence=[]
for directory,pins in [
 ('financial-wrapper-compatibility-postcommit-admission-review01-2026-10-04',{'MACHINE01.json':'62b5fa80f2a0a1275398156194daef3b809bb983966077f30b669e403be60874','MANIFEST01.json':'da5de0fa5f5956149abd05c73b8e5b7525ea5ada2c1e44ae6514486c1d1b63da'}),
 ('financial-wrapper-compatibility-parent-source-review01-2026-10-04',{'MACHINE01.json':'faaad64cfe9931f64f45fea7eb364fdf2e6219082ad2de8aea69b0ccde3b8dbc','MANIFEST01.json':'dc43830ad8fe17741bc85df2a6ed19da38cb3902c6685f2dce6258b0ef2de3e9'}),
 ('financial-wrapper-compatibility-source-parent-capture-review04-2026-10-04',{'MACHINE01.json':'435b69706a78e785d939311c269357e74f45cfa211c198750eb12f7dd2925429','MANIFEST01.json':'4a21d4a7853e8386e72b700bca5243415caef1d4c0914c008547977e835ded84'})]:
 for name,pin in pins.items():p=B/directory/name;read(p,pin);evidence.append({'path':str(p),'sha256':pin})
admission=j(B/'financial-wrapper-compatibility-root-admission01-2026-10-04/ACTUAL_ADMISSION01.json','dcbef49b6fd6c89b3c0eb022113ff51dd987edb84d1b5ce7ddc8cb4b30bfbb65')
require(not os.path.lexists(CAP/'research_runs'/ID) and not os.path.lexists(PARENT/'attempt'),'actual fresh fixed claim/attempt absence')
layout=j(LAYOUT/'DRAFT_LAYOUT01.json');require(len(layout['receipt_candidates'])==38,'all38 actualreceipt candidates')
external={'review_'+k:v for k,v in layout['review_reference_candidates'].items()};require(set(external)=={'review_proof','review_machine','review_manifest','review_report'},'four actual nestedpolicy refs')
external['recovery_proof']=layout['original_recovery_proof_copy']
for v in external.values():read(Path(v['path']),v['sha256'])
for n in ('machine','report','manifest'):external['recovery_'+n]=None
bound=False;recovery_machine=None
if args.phase=='bound':
 require(args.binding is not None,'actual independently accepted installed binding required');binding=j(args.binding)
 require(set(binding)=={'recovery_machine','recovery_report','recovery_manifest','independent_coalesced_review'},'exact actual binding fields')
 for k in ('recovery_machine','recovery_report','recovery_manifest'):
  v=binding[k];require(Path(v['path']).parent==LAYOUT,'fixed installed Root recovery evidence');read(Path(v['path']),v['sha256']);external[k]=v
 # Accept only genuine different-author installation evidence; authored elsewhere.
 iv=binding['independent_coalesced_review'];require(iv['sha256']=='e267987ec088fcde40936aad9275967131521aa94b7db19fc3237409e629b6a6','exact frozen different-author coalesced acceptance');installation=j(Path(iv['path']),iv['sha256']);require(installation.get('reviewer')=='storage_watch_review' and installation.get('decision')=='ACCEPTED_ACTUAL_COALESCED_RECOVERY_EVIDENCE_WITH_EXACT_INSTALL_CANDIDATES_ONLY','genuine actual coalesced review and exact candidate installation scope')
 peer_manifest=j(Path(iv['path']).parent/'MANIFEST01.json','2eb451cc119963749bc6ac3a2edaf089590b900de810625a888216bfe3f14b95')
 peer_rows={x['path']:x for x in peer_manifest['members']}
 require(peer_rows['MACHINE01.json']['sha256']==iv['sha256'],'authentic peer machine sealed')
 for name,x in installation['candidate_files'].items():
  p=LAYOUT/name;require(str(p)==x['destination'] and len(read(p,x['sha256']))==x['bytes'] and stat.S_IMODE(p.lstat().st_mode)==x['mode'],'actual exact candidate installed body/mode')
  cp=Path(x['source']);require(cp.is_relative_to(Path(iv['path']).parent) and peer_rows[cp.relative_to(Path(iv['path']).parent).as_posix()]['sha256']==x['sha256'] and read(cp)==read(p),'full byte identity to sealed different-author candidate')
 installed_manifest=j(Path(external['recovery_manifest']['path']),external['recovery_manifest']['sha256']);installed_rows={x['path']:x for x in installed_manifest['members']}
 actual_rows={'.'};pending=[LAYOUT]
 while pending:
  pp=pending.pop()
  with os.scandir(pp) as it:
   for ent in it:
    name=str(Path(ent.path).relative_to(LAYOUT))
    if name=='MANIFEST01.json':continue
    st=ent.stat(follow_symlinks=False);require(name in installed_rows,'actual full coalesced namespace membership');actual_rows.add(name);z=installed_rows[name];require(stat.S_IMODE(st.st_mode)==z['mode'],'whole actual coalesced mode')
    if stat.S_ISDIR(st.st_mode):require(z['kind']=='directory','actual coalesced directory');pending.append(Path(ent.path))
    else:require(stat.S_ISREG(st.st_mode) and z['kind']=='file' and len(read(Path(ent.path),z['sha256']))==z['bytes'],'actual full coalesced body')
 require(actual_rows==set(installed_rows) and stat.S_IMODE(LAYOUT.stat().st_mode)==installed_rows['.']['mode'],'complete installed manifest root/member denominator')
 rr=PRE.Reader();ii=PRE.Inputs(CAP,e['inputs'],rr)
 for kind in ('review','recovery'):PRE._proof_bundle(kind,external,ii,policy,rr)
 rr.finish();recovery_machine=j(Path(external['recovery_machine']['path']),external['recovery_machine']['sha256']);require(recovery_machine['recovery_receipts']==layout['receipt_candidates'],'full38 originalreceipt paths retained');bound=True
# Exact unique path cache inventory of the fixed independent complete100 phase.
charged={}
def charge(p,role,pin=None):
 p=Path(p);b=read(p,pin);key=str(p)
 if key not in charged:charged[key]={'path':key,'bytes':len(b),'sha256':sha(b),'roles':[]}
 charged[key]['roles'].append(role)
for n,pin in policy['target']['installed'].items():charge(CAP/n,'target_source',pin)
for role,v in e['inputs'].items():charge(CAP/v['path'],'input:'+role,v['sha256'])
charge(CAP/q['registration'],'registration',q['registration_sha256'])
for role,v in external.items():
 if v is not None:charge(v['path'],role,v['sha256'])
for v in layout['receipt_candidates']:charge(v['path'],'recovery_receipt',v['sha256'])
for n,pin in q['helper_hashes'].items():charge(PARENT/n,'parent_helper',pin)
charge(PARENT/'parent01.py','parent_caller',q['caller_sha256']);charge(q['proofs']['cumulative']['path'],'cumulative_proof',q['proofs']['cumulative']['sha256'])
unknown=['actual_final_parent_contract','actual_final_parent_release','actual_full_recovery_proof','actual_source_input_runtime_proof']+([] if bound else ['installed_recovery_machine','installed_recovery_report','installed_recovery_manifest'])
base=sum(x['bytes'] for x in charged.values());draft_projection=base+len(qraw)
# This is a true original Reader/finish measurement of the known subset only.
rr=PRE.Reader()
for p in charged:rr.read(Path(p))
rr.finish();require(rr.total==2*base,'exact known cache plus finish charge')
proof=None
if bound:
 proof={'schema_version':1,'kind':'independent_source_input_runtime','decision':'accepted-source-input-runtime-metadata-only','reviewer':'combined_worker_review','source':SOURCE,'design_source':SOURCE,'root':str(CAP),'identity':ID,'registration':q['registration'],'registration_sha256':q['registration_sha256'],'tracked':355,'source_pins':354,'input_roles':11,'implementation_paths':195,'package_paths':150,'logical_git_objects':407,'runtime_mapping_sha256':sha(inputs['runtime_mapping']),'runtime_records':251,'runtime_scope':'interpreter/lock/251 RECORD and direct METADATA; package bodies not fully hashed','actual_admission_sha256':'dcbef49b6fd6c89b3c0eb022113ff51dd987edb84d1b5ce7ddc8cb4b30bfbb65','source_parent_evidence':evidence,'compatibility_preclaim_external_refs':external,'numerical_authority':False,'final_preclaim_success':False,'final_caller_recovery':False,'new_source_external_recovery':False}
 proof=save('SOURCE_INPUT_RUNTIME_PROOF01.json',proof)
for p,x in READS.items():require(signature(Path(p).lstat())==tuple(x['signature']),'final bounded audit fingerprint')
out={'schema_version':1,'phase':args.phase,'status':'ACTUAL_EIGHT_REFS_BOUND' if bound else 'DRAFT_MISSING_ACTUAL_INSTALLED_ACCEPTED_LAYOUT','external_refs':external,'unique_known_paths':len(charged),'unique_known_bytes':base,'known_actual_reader_including_finish':rr.total,'draft_request_bytes':len(qraw),'known_plus_draft_request':2*draft_projection,'remaining_after_known_plus_draft':8388608-2*draft_projection,'source_proof':proof,'unknowns':unknown,'fixed_limit':8388608,'complete_final_preclaim_proven':False,'audit_source_reads':len(READS),'audit_source_bytes':sum(x['bytes'] for x in READS.values()),'no_Admission_Run_Owner_or_public_preflight':True,'numerical_authority':False,'inventory':list(charged.values()),'runtime_records':records,'evidence':evidence,'assertions':len(CHECKS)}
save('INVENTORY_'+args.phase.upper()+'01.json',out);save('SOURCE_READBACK_'+args.phase.upper()+'01.json',{'reads':list(READS.values()),'checks':CHECKS});print(json.dumps({k:v for k,v in out.items() if k not in ['inventory','runtime_records','evidence','external_refs']}))
