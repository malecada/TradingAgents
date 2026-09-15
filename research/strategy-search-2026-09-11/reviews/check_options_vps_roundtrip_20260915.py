import hashlib,json,tarfile,time
from pathlib import Path
from tradingagents.research_options_capture import returned
root=Path.cwd();folder=Path('/home/malecada/master_thesis/research-deployment/options-20260915')
archive=folder/'synthetic-return-repacked.tar.gz'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='a3e92b1e0fab0ecddebef6c652729a0e38984a275539aedca589918bd8790922'
dest=folder/'returned-synthetic';dest.mkdir()
with tarfile.open(archive,'r:gz') as tf:
    members=tf.getmembers();names=set();total=0
    assert len(members)<100000
    for m in members:
        path=Path(m.name)
        assert not path.is_absolute() and '..' not in path.parts and path.parts[0] in ('package','data')
        assert m.name not in names and (m.isdir() or m.isfile()) and m.size<=16*1024**2
        names.add(m.name);total+=m.size
        assert total<=2*1024**3
    tf.extractall(dest,members=members,filter='data')
anchor='0986059022f435f8e541e6f0a11d6c419a097376303f5944684bc04e82f7c50e'
started=time.monotonic();prepared=returned.prepare(package=dest/'package',data=dest/'data',expected_assignment_sha256=anchor)
assert prepared['source_report']['source_status']=='complete'
# Exact file bytes (not tar headers/ownership) must agree for every original member.
original=Path('/tmp/options-full-episode-v6ie8rac');count=0;h=hashlib.sha256()
for p in sorted(x for name in ('package','data') for x in (original/name).rglob('*') if x.is_file()):
    rel=p.relative_to(original);q=dest/rel
    digest=hashlib.sha256(p.read_bytes()).hexdigest()
    assert digest==hashlib.sha256(q.read_bytes()).hexdigest(),str(rel)
    h.update(json.dumps([str(rel),p.stat().st_size,digest],separators=(',',':')).encode());count+=1
report={'scope':'Invented raw source package copied to confirmed VPS, extracted and repacked there, downloaded to new local staging, allmembers verified and returned.prepare admitted; no collector or market request',
        'host':'pck-preds-1','remote_directory':'/opt/thesis-research/options-episode-20260911/synthetic-return-proof',
        'upload_archive_sha256':'08d1ceddb4a281adb9ff3a3e15c646971cd1573c25e44ceb0908cf208a5e883c','download_archive_sha256':'a3e92b1e0fab0ecddebef6c652729a0e38984a275539aedca589918bd8790922',
        'assignment_sha256':anchor,'local_returned_directory':str(dest),'all_package_and_data_regular_members_equal':count,'member_comparison_sha256':h.hexdigest(),
        'source_report':prepared['source_report'],'validation_seconds':time.monotonic()-started,'source_original_preserved':True,
        'backup_scope':'Invented complete raw source bytes retained original localtemp, extracted VPS copy, remotearchives and verified returned localstaging. This does not claim nonexistent future observations backed up.'}
with (root/'research/strategy-search-2026-09-11/reviews/options-vps-roundtrip-20260915.json').open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
print(json.dumps({'members_equal':count,'source_slots':prepared['source_report']['intended_slot_count'],'seconds':report['validation_seconds']}))
