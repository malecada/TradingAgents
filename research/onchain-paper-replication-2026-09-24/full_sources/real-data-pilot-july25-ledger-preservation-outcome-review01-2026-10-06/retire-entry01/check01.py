"""Exact dependent RETIRE metadata/stat/eligibility review; never calls retire or reads payload."""
from pathlib import Path
import ast,datetime,hashlib,importlib.util,json,os,shutil,stat
H=Path(__file__).resolve().parent;F=H.parent.parent;R=F.parents[2];D=F/'real-data-pilot-july25-ledger-relocation01-2026-10-06';ev={}
def sig(s):return [s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,stat.S_IMODE(s.st_mode)]
def raw(p,pin=None):
 p=Path(p);s=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<4*1024**2;b=p.read_bytes();assert sig(s)==sig(p.lstat());v=hashlib.sha256(b).hexdigest();assert pin is None or v==pin;ev[str(p.relative_to(R))]=v;return b
def read(p,pin=None):return json.loads(raw(p,pin))
e=read(D/'retire-envelope01.json','c727c6bea2be8194a907713d4326697b103e02e925bc661b2aea0412631b2667');draft=read(D/'retire-RELEASE_DRAFT01.json','4eec70100bb65cd59fcde7f318aab62988a42490d6d42071d8c67d89eb5d938b')
assert draft['decision']=='DRAFT_NOT_RELEASED' and draft['phase']==e['phase']=='retire' and draft['identity']==e['identity']=='real-pilot-july25-ledger-relocation-20261006-01'
assert draft['envelope_sha256']==ev[str((D/'retire-envelope01.json').relative_to(R))]
for path,pin in draft['evidence'].items():raw(R/path,pin)
for path,pin in e['source_files'].items():assert draft['evidence'][path]==pin
for ref in e['evidence']+[e['helper'],e['selection'],e['environment']]:assert draft['evidence'][ref['path']]==ref['sha256']
c=read(R/e['selection']['path'],e['selection']['sha256']);parts={}
for name in ('copy_receipt','copy_review','copy_native','copy_outer','copy_root'):
 ref=draft[name];assert draft['evidence'][ref['path']]==ref['sha256'];parts[name]=read(R/ref['path'],ref['sha256'])
rec=parts['copy_receipt'];review=parts['copy_review'];native=parts['copy_native'];outer=parts['copy_outer'];root=parts['copy_root']
assert review['decision']=='accepted' and review['full_destination_readback_verified'] is True and review['copy_receipt_sha256']==draft['copy_receipt']['sha256'] and review['identity']==e['identity']
assert rec['original']==c['recovery_selection']['rows'][0]['original'] and rec['original_retired'] is False and rec['source_retired'] is False and rec['copy_readback_verified'] is True
assert native['phase']=='complete' and native['child_exit_code']==0 and native['cleanup_verified'] is True and outer['entry_selected_exit_code']==0 and root['actual_root_tool_exit_code']==0
assert not Path(native['cgroup']).exists() and all(not Path('/proc',str(p)).exists() for p in root['selected_recorded_pids'])
p=R/e['helper']['path'];source=raw(p,e['helper']['sha256']);spec=importlib.util.spec_from_file_location('accepted_retire_metadata',p);m=importlib.util.module_from_spec(spec);exec(compile(source,str(p),'exec'),vars(m))
base,row=m.validate(c);m.room(c);base.inactive() # read-only metadata/current-stat/floor and consumer checks
assert {k:rec['target'][k] for k in ('path','device','bytes','sha256')}==c['target']
target=Path(rec['target']['path']);assert target.resolve(strict=True)==target and sig(target.lstat())==rec['target']['stat_identity'] and set(q.name for q in target.parent.iterdir())=={'events.sqlite'}
for name in ('retire-preflight01.json','retire-launch-attempt01.json','retire-attempt01.json','retire-complete01.json','retire-failed01.json','retire-outer-exit01.json','relocation-receipt01.json'):assert not os.path.lexists(D/name)
# Source unchanged; one unlink targets only ROOT/row[path], recording success before fsync.
node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='retire')
unlinks=[n for n in ast.walk(node) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='unlink'];assert len(unlinks)==1 and ast.unparse(unlinks[0])=="(ROOT / row['path']).unlink()"
assert "(ROOT/row['path']).unlink();removed.append(row['path'])" in source.decode() and "'ambiguous_attempts':[p for p in attempted if p not in removed]" in source.decode()
result={'decision':'pass','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'identity':e['identity'],'phase':'retire','entry_sha256':e['source_files'][str((D/'entry01.py').relative_to(R))],'envelope_sha256':draft['envelope_sha256'],'current_original_stat':sig((R/row['path']).lstat()),'current_get_stat':sig((R/c['recovery_selection']['rows'][0]['recovered']['path']).lstat()),'current_target_stat':sig(target.lstat()),'retire_namespace_unused':True,'only_original_unlink':True,'native_and_consumers_inactive':True,'root_free_bytes':shutil.disk_usage(R).free,'data_free_bytes':shutil.disk_usage(m.DATA).free,'minimum_each_volume_bytes':10*1024**3+64*1024**2,'evidence':ev,'actual_retire_outcome':None,'payload_reads':0}
(H/'CHECK01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='evidence'},sort_keys=True))
