"""Exact actual metadata/current-stat entry review; never reads or deletes payloads."""
from pathlib import Path
import datetime,hashlib,json,os,shutil,sys,types
HERE=Path(__file__).resolve().parent;F=HERE.parent.parent;ROOT=F.parents[2]
D=F/'real-data-pilot-july25-get-retirement01-2026-10-06'
ENTRY='05512665226937ca46ab9bdaf5578de9de53e46b5778e859b885854d48ea5f8e'
SELECTION='6245d372684be982a283a87f6bac224d50e9161c2a4e3f55187f207a41907297'
DRAFT='6ded6d3657cc0ca278a1cf67dbf777b0cdf2ddba0df08b97e51f32d696b15cc9'
def audit(event,args):
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0]));assert p.suffix not in ('.bin','.sqlite','.npy','.npz') and p.name!='connection.json','payload/private body access forbidden'
 if event=='subprocess.Popen':assert args[1][:5]==['systemctl','--user','list-units','--state=active,activating','--no-legend'],'only read-only native inactivity query permitted'
 if event in ('os.remove','os.rename','os.rmdir','socket.connect'):raise AssertionError('mutation/network forbidden')
sys.addaudithook(audit)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(D/'retire01.py')==ENTRY and sha(D/'selection01.json')==SELECTION and sha(D/'RELEASE_DRAFT01.json')==DRAFT
r=types.ModuleType('exact_get_entry');r.__file__=str(D/'retire01.py');exec(compile((D/'retire01.py').read_bytes(),r.__file__,'exec'),vars(r))
m,cold=r.sources();c=json.loads((D/'selection01.json').read_bytes());draft=json.loads((D/'RELEASE_DRAFT01.json').read_bytes())
assert draft['decision']=='DRAFT_NOT_RELEASED' and draft['entry_sha256']==ENTRY and draft['retirement_identity']==r.ID and draft['retire_only_exact_backup02_get'] is True
assert draft['selection']=={'path':str((D/'selection01.json').relative_to(ROOT)),'sha256':SELECTION}
for refs in (c['evidence'],draft['evidence']):
 for path,pin in refs.items():m.metadata(ROOT,path,pin)
row,target=r.validate(m,c);r.inactive(m)
for name in ('attempt01.json','complete01.json','failed01.json','ROOT_TERMINAL01.json'):
 assert not os.path.lexists(D/name),'retirement namespace spent: '+name
get=ROOT/row['recovered']['path'];assert get.name=='00-recovered.bin' and get.parent.name=='real-pilot-july25-ledger-preservation-20261006-02'
original_absent=not os.path.lexists(ROOT/m.ORIGINAL);assert original_absent
free={str(p):shutil.disk_usage(p).free for p in (ROOT,Path('/home/malecada/Data'))}
assert all(v>=10*1024**3 for v in free.values()),'unchanged physical floor unavailable'
# Prior metadata-binding failure is historical; it is not a retirement attempt.
failure=D/'ROOT_BINDING_FAILURE01.json';assert failure.is_file()
observation={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'decision':'PASS','entry_sha256':ENTRY,'selection_sha256':SELECTION,'release_draft_sha256':DRAFT,'evidence_count':len(set(c['evidence'])|set(draft['evidence'])),'original_absent':original_absent,'sole_get':row['recovered'],'get_stat_identity':m.identity(get.lstat()),'get_allocated_bytes':get.lstat().st_blocks*512,'retained_data':target,'data_current_stat_identity':r.sig(r.TARGET.lstat()),'native_and_registered_consumers_inactive':True,'unused_retirement_namespace':True,'disk_free_bytes':free,'prior_binding_failure_sha256':sha(failure),'payload_body_reads':False,'retirement_executed':False,'qualification':'Actual sampled stat/metadata/process checks. Existing accepted full-byte recovery and Data readback reused. No global writer exclusion, new payload verification, pilot-capacity admission or execution is inferred.'}
(HERE/'CHECK01.json').write_text(json.dumps(observation,indent=2)+'\n');print(json.dumps({k:observation[k] for k in ('decision','evidence_count','original_absent','get_allocated_bytes','disk_free_bytes','prior_binding_failure_sha256')}))
