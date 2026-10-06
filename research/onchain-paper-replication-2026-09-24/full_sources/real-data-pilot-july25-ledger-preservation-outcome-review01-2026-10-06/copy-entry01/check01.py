"""Fixed COPY metadata validation, current stat and physical observations. No payload opens."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,os,shutil,stat
H=Path(__file__).resolve().parent;F=H.parent.parent;R=F.parents[2]
D=F/'real-data-pilot-july25-ledger-relocation01-2026-10-06';ev={}
def raw(p,pin=None):
    p=Path(p);s=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<4*1024**2
    b=p.read_bytes();assert s==p.lstat();digest=hashlib.sha256(b).hexdigest();assert pin is None or digest==pin;ev[str(p.relative_to(R))]=digest;return b
def read(p,pin=None):return json.loads(raw(p,pin))
e=read(D/'copy-envelope01.json');assert ev[str((D/'copy-envelope01.json').relative_to(R))].startswith('725af097')
c=read(R/e['selection']['path'],e['selection']['sha256']);assert e['selection']['sha256']=='a050d2188a68583b39f886e621684b2920c6d4e566068191334289c96d79075d'
assert e['identity']==c['identity']=='real-pilot-july25-ledger-relocation-20261006-01' and e['phase']=='copy' and c['status']=='FROZEN_FOR_REVIEW'
for path,pin in e['source_files'].items():raw(R/path,pin)
for ref in e['evidence']+[e['environment'],e['helper']]:raw(R/ref['path'],ref['sha256'])
for path,pin in c['recovery_selection']['evidence'].items():raw(R/path,pin)
assert e['source_files'][str((D/'entry01.py').relative_to(R))]=='93f720a2d5d122933bb97ea31cf1ac13bc8662603b8799cab1d3d6fd25d4004c'
assert e['source_files'][e['helper']['path']]==e['helper']['sha256']=='6307e8165f203118ad9a46758656e808e8ad87d600e45de8bdcc3a58c6d2a8a3'
p=R/e['helper']['path'];spec=importlib.util.spec_from_file_location('reviewed_metadata_only',p);m=importlib.util.module_from_spec(spec);exec(compile(raw(p),str(p),'exec'),vars(m))
# Genuine source predicates only: validate/recovery/current are metadata/stat-only.
base,row=m.validate(c);m.room(c,m.BYTES);base.inactive()
assert not os.path.lexists(m.TARGET.parent) and not os.path.lexists(m.TARGET)
assert m.TARGET.parent.parent.parent.resolve(strict=True)==m.TARGET.parent.parent.parent
for phase in ('copy','retire'):
 for suffix in ('preflight01.json','launch-attempt01.json','attempt01.json','complete01.json','failed01.json','outer-exit01.json','guard01'):
  assert not os.path.lexists(D/(phase+'-'+suffix))
assert not (D/'relocation-receipt01.json').exists()
mem=dict(line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines());available=int(mem['MemAvailable'].split()[0])*1024
assert available>=int(3.5*1024**3)
rootfree=shutil.disk_usage(R).free;datafree=shutil.disk_usage(m.DATA).free
assert R.stat().st_dev==66310 and m.DATA.stat().st_dev==66307
obs={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_files_checked':len(e['source_files']),'metadata_refs_checked':len(ev),'root_free_bytes':rootfree,'data_free_bytes':datafree,'root_minimum_required_bytes':10*1024**3+64*1024**2,'data_minimum_required_bytes':10*1024**3+3755212800+64*1024**2,'mem_available_bytes':available,'startup_mem_required_bytes':int(3.5*1024**3),'target_absent':True,'copy_and_retire_namespaces_unused':True,'genuine_recovery_predicates_passed':True,'native_active_unit_and_registered_consumer_refusal_checks_passed':True,'no_payload_read':True,'no_native_launch_or_network':True,'evidence':ev}
(H/'CHECK01.json').write_text(json.dumps(obs,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in obs.items() if k!='evidence'},sort_keys=True))
