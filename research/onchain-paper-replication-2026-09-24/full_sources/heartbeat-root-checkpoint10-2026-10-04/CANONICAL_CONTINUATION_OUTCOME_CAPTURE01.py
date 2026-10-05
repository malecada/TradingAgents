"""One-use Root capture of actual new refusal bytes, reusing accepted old bytes."""
from pathlib import Path
import sys,os,stat,json,time,hashlib,shutil
ROOT=Path(__file__).resolve().parents[4]
F=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'
C=Path(__file__).resolve().parent
P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-canonical-plan-root-launch-20261005-01')
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
ID='financial-wrapper-classification-eager-continue100-compatibility-20261004-01'
JOB=CAP/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/ID
OUT=F/'financial-wrapper-continuation-refused-outcome-capture01-2026-10-05'
assert hashlib.sha256((P/'recovery04.py').read_bytes()).hexdigest()=='b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a'
sys.path.insert(0,str(P))
import recovery04 as R
from bounded_git01 import git
assert not OUT.exists() and shutil.disk_usage(F).free>=10*1024**3
basis=F/'financial-wrapper-continuation-canonical-plan-review01-2026-10-05/CANONICAL_FULL_RECOVERY_PROOF01.json'
assert R.digest(R.read(basis.parent,basis.name))=='4bb7781345617bf5529e63b0c2d0a630aad726df87c3dc895ab4e02ca323aa79'
old=json.loads(R.read(F/'financial-wrapper-continuation-canonical-delta-root01-2026-10-05/snapshot','COMPOSITION01.json'))['capsule']
def metadata():
    rows=[];deadline=time.monotonic()+10
    for current,dirs,files in os.walk(CAP):
        assert time.monotonic()<deadline and len(rows)<4096
        if Path(current)==CAP:dirs[:]=[n for n in dirs if n!='.git']
        for n in sorted(dirs+files):
            p=Path(current)/n;s=p.lstat();assert p.resolve()==p and stat.S_ISDIR(s.st_mode) or p.resolve()==p and stat.S_ISREG(s.st_mode)
            row={'path':p.relative_to(CAP).as_posix(),'kind':'directory' if stat.S_ISDIR(s.st_mode) else 'file','mode':stat.S_IMODE(s.st_mode)}
            if row['kind']=='file':row['bytes']=s.st_size
            rows.append(row)
    return sorted(rows,key=lambda r:r['path'])
before=metadata();known={r['path']:r for r in old['members']};actual={r['path']:r for r in before}
assert set(known)<=set(actual)
for name,row in known.items():assert all(actual[name][k]==v for k,v in row.items() if k!='sha256')
job=R.scan(JOB);parent=R.scan(P);reviewroot=F/'financial-wrapper-continuation-outcome-review01-2026-10-05';review=R.scan(reviewroot)
prefix=JOB.relative_to(CAP).as_posix()
assert set(actual)-set(known)=={prefix}|{prefix+'/'+r['path'] for r in job['members']}
assert len(job['members'])==10 and sum(r['kind']=='file' for r in job['members'])==9
newrows=[{'path':prefix,'kind':'directory','mode':job['root_mode']}]+[{**r,'path':prefix+'/'+r['path']} for r in job['members']]
current={**old,'members':sorted(old['members']+newrows,key=lambda r:r['path'])}
assert len(current['members'])==1060 and sum(r['kind']=='file' for r in current['members'])==832
assert git(CAP,['rev-parse','HEAD'],cap=128).decode().strip()=='d4c81c0961342bfe4c5771aabbef1d46a14cffb8'
assert not (CAP/'research_runs'/ID).exists() and not (JOB/'guard/release.json').exists()
saved={};sources={}
for label,base,m in [('Parent',P,parent),('job',JOB,job),('outcome-phase',reviewroot,review)]:
    sources[label]={'root':str(base),'manifest':m}
    for r in m['members']:
        if r['kind']=='file':
            raw=R.read(base,r['path']);assert len(raw)==r['bytes'] and R.digest(raw)==r['sha256'];saved[label+'/'+r['path']]=raw
for n in ('CANONICAL_CONTINUATION_ACTUAL_ROOT_EXIT01.json','CANONICAL_CONTINUATION_NUM01.stdout','CANONICAL_CONTINUATION_NUM01.stderr'):
    saved['Root/'+n]=R.read(C,n)
assert sum(map(len,saved.values()))<2*1024**2
OUT.mkdir(mode=0o700);snapshot=OUT/'snapshot';snapshot.mkdir(mode=0o700);mapped={}
for i,(name,raw) in enumerate(sorted(saved.items())):
    leaf='body-%04d'%i
    with R.new_file(snapshot/leaf) as fd:
        with os.fdopen(os.dup(fd),'wb') as stream:stream.write(raw)
    mapped[name]={'flat':leaf,'bytes':len(raw),'sha256':R.digest(raw)}
composition={'schema_version':1,'kind':'complete-new-refusal-bytes-with-accepted-immutable-basis','identity':ID,'source':'d4c81c0961342bfe4c5771aabbef1d46a14cffb8','basis':{'path':str(basis),'sha256':R.digest(R.read(basis.parent,basis.name))},'capsule':current,'Git_logical_objects':422,'scopes':sources,'materialized':mapped,'old823_capsule_bodies_not_reread':True,'old_runtime251_not_reread':True,'numerical_claim':False,'namespace_reserved':True,'POSIX_reconstruction':False,'runtime_bodies_recovered':False,'external_recovery':None}
R.put(snapshot/'COMPOSITION01.json',composition);manifest=R.scan(snapshot);R.put(OUT/'archive-manifest.json',manifest);info=R.pack(snapshot,manifest,OUT/'increment.tar.gz')
for label,scope in sources.items():R.same(Path(scope['root']),scope['manifest'])
assert before==metadata() and not (CAP/'research_runs'/ID).exists()
R.same(snapshot,manifest);assert shutil.disk_usage(OUT).free>=10*1024**3
R.put(OUT/'CAPTURE01.json',{'schema_version':1,'identity':ID,'source':composition['source'],'archive':info,'regular':len(manifest['members']),'new_original_bodies':len(mapped),'new_original_bytes':sum(r['bytes'] for r in mapped.values()),'complete_current_CAP_regular':832,'complete_current_CAP_typed':1060,'Parent_regular':sum(r['kind']=='file' for r in parent['members']),'recovery_basis':composition['basis'],'scope':'complete original new refusal bytes and typed current population, accepted old byte basis reused; no POSIX/runtime/whole-capacity claim','external_recovery':False})
print(json.dumps({'status':'CAPTURED_ONCE','archive_bytes':info['bytes'],'archive_sha256':info['sha256'],'new_original_bodies':len(mapped)}))
