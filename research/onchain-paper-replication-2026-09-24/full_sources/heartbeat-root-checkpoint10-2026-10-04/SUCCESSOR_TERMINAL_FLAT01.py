"""One-use flat byte recovery through the accepted unchanged PAX primitive."""
from pathlib import Path
import sys,json,hashlib,os,shutil
ROOT=Path(__file__).resolve().parents[4]
F=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'
P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-resource-successor-root-launch-20261005-01')
REMOTE=F/'financial-wrapper-continuation-successor-terminal-remote01-2026-10-05'
PREFIX='research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-continuation-successor-terminal-capture01-2026-10-05'
OUT=F/'financial-wrapper-continuation-successor-terminal-flat01-2026-10-05'
assert hashlib.sha256((P/'recovery04.py').read_bytes()).hexdigest()=='b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a'
sys.path.insert(0,str(P))
import recovery04 as R
archive=REMOTE/'selected'/PREFIX/'increment.tar.gz'
manifest=REMOTE/'selected'/PREFIX/'archive-manifest.json'
capture=REMOTE/'selected'/PREFIX/'CAPTURE01.json'
receipt=json.loads(R.read(REMOTE,'REMOTE_RECOVERY01.json'))
assert receipt['remote_commit']=='34e8da6656fc0cf7ac28cfe511ec99451f09cadc' and receipt['selected_count']==8 and len(receipt['operations'])==34
assert all(r['actual_reaped_exit']==0 and r['cleanup_failures']==[] for r in receipt['operations'])
refs={r['path']:r for r in receipt['selected_blobs']}
for p in (archive,manifest,capture):
    name=p.relative_to(REMOTE/'selected').as_posix();raw=R.read(p.parent,p.name)
    assert len(raw)==refs[name]['bytes'] and R.digest(raw)==refs[name]['sha256']
assert R.digest(R.read(archive.parent,archive.name))=='d26c3af64a99e21162df9effacd9249f749555da059cc19a4e882125810cde17'
record=json.loads(R.read(capture.parent,capture.name));m=json.loads(R.read(manifest.parent,manifest.name))
assert record['new_original_bodies']==87 and len(m['members'])==88 and record['CAP_regular']==848 and record['CAP_typed']==1079 and record['Git_logical_objects']==438 and record['Parent_regular']==29
assert not OUT.exists() and shutil.disk_usage(F).free>=10*1024**3
OUT.mkdir(mode=0o700)
(OUT/'flat').mkdir(mode=0o700)
result=R.restore(archive,record['archive'],m,OUT/'flat')
assert result['regular_bodies']==88
R.put(OUT/'RECOVERY01.json',{'status':'actual-terminal-successor-flat-byte-recovery','receiver_receipt_sha256':R.digest(R.read(REMOTE,'REMOTE_RECOVERY01.json')),'capture_sha256':R.digest(R.read(capture.parent,capture.name)),'archive_sha256':record['archive']['sha256'],'manifest_sha256':R.digest(R.read(manifest.parent,manifest.name)),'primitive':result,'new_original_bodies':87,'accepted_old_basis_reused':True,'POSIX_reconstruction':False,'runtime_bodies_recovered':False,'paper_fit_or_namespace_reuse_authority':False})
assert shutil.disk_usage(OUT).free>=10*1024**3
print(json.dumps({'status':'actual-terminal-successor-flat-byte-recovery','regular_bodies':88,'new_original_bodies':87,'recovery_sha256':R.digest(R.read(OUT,'RECOVERY01.json'))}))
