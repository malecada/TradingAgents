"""Storage preservation tests use tiny synthetic bytes; no external calls."""
import hashlib
import io
from pathlib import Path
import tarfile

import pytest

from tradingagents.research.onchain_replication.preservation import (
    plan_batches, build_bundle, verify_bundle,
)


def record(path, data):
    path.write_bytes(data)
    return {'source_path': str(path), 'resolved_path': str(path.resolve()),
            'bytes': len(data), 'expected_sha256': hashlib.sha256(data).hexdigest(),
            'mtime_ns': path.stat().st_mtime_ns}


def test_batch_partition_preserves_every_source_once(tmp_path):
    rows=[record(tmp_path/str(i), b'x'*n) for i,n in enumerate([3,4,2,5])]
    batches=plan_batches(rows, max_raw_bytes=7, max_members=2)
    assert [(b['start'],b['stop'],b['raw_bytes']) for b in batches]==[(0,2,7),(2,4,7)]


def test_duplicate_or_oversize_source_refused(tmp_path):
    row=record(tmp_path/'a',b'1234')
    with pytest.raises(ValueError,match='duplicate'):
        plan_batches([row,row],max_raw_bytes=8,max_members=4)
    with pytest.raises(ValueError,match='exceeds'):
        plan_batches([row],max_raw_bytes=3,max_members=4)


def test_bundle_recovery_hashes_each_original_without_extraction(tmp_path):
    rows=[record(tmp_path/'a',b'first'),record(tmp_path/'b',b'\x00second')]
    archive=tmp_path/'bundle.tar'
    manifest=build_bundle(rows,archive,allowed_roots=[tmp_path],start_index=11)
    assert verify_bundle(archive,manifest)=={'files':2,'raw_bytes':12}
    assert [m['member'] for m in manifest['members']]==['files/00000011','files/00000012']
    assert (tmp_path/'a').read_bytes()==b'first'
    assert (tmp_path/'b').read_bytes()==b'\x00second'
    with pytest.raises(FileExistsError):
        build_bundle(rows,archive,allowed_roots=[tmp_path])


@pytest.mark.parametrize('change',['hash','mtime','path'])
def test_bad_source_never_accepted(tmp_path,change):
    row=record(tmp_path/'a',b'first')
    if change=='hash': row['expected_sha256']='0'*64
    if change=='mtime': row['mtime_ns']-=1
    if change=='path': row['resolved_path']=str(tmp_path/'missing')
    with pytest.raises((ValueError,FileNotFoundError)):
        build_bundle([row],tmp_path/'bundle.tar',allowed_roots=[tmp_path])


def test_source_outside_allowed_root_refused(tmp_path):
    row=record(tmp_path/'a',b'first')
    allowed=tmp_path/'allowed';allowed.mkdir()
    with pytest.raises(ValueError,match='root'):
        build_bundle([row],tmp_path/'bundle.tar',allowed_roots=[allowed])


def test_recovered_member_corruption_detected_even_when_archive_hash_replaced(tmp_path):
    rows=[record(tmp_path/'a',b'first')]
    archive=tmp_path/'bundle.tar'
    manifest=build_bundle(rows,archive,allowed_roots=[tmp_path])
    with tarfile.open(archive,'w',format=tarfile.USTAR_FORMAT) as tar:
        info=tarfile.TarInfo('files/00000000');info.size=5
        tar.addfile(info,io.BytesIO(b'wrong'))
    manifest['archive_sha256']=hashlib.sha256(archive.read_bytes()).hexdigest()
    manifest['archive_bytes']=archive.stat().st_size
    with pytest.raises(ValueError,match='member hash'):
        verify_bundle(archive,manifest)


def test_malicious_member_rejected_without_writing_path(tmp_path):
    rows=[record(tmp_path/'a',b'first')]
    archive=tmp_path/'bundle.tar'
    manifest=build_bundle(rows,archive,allowed_roots=[tmp_path])
    with tarfile.open(archive,'w',format=tarfile.USTAR_FORMAT) as tar:
        info=tarfile.TarInfo('../escape');info.size=5
        tar.addfile(info,io.BytesIO(b'first'))
    manifest['archive_sha256']=hashlib.sha256(archive.read_bytes()).hexdigest()
    manifest['archive_bytes']=archive.stat().st_size
    with pytest.raises(ValueError,match='member'):
        verify_bundle(archive,manifest)
    assert not (tmp_path.parent/'escape').exists()


class LocalTransport:
    """Filesystem transport exercises publication ordering without SSH/network."""
    def __init__(self, root, fail=False):
        self.root=root
        self.fail=fail
    def mkdir(self,path): (self.root/path).mkdir(parents=True,exist_ok=False)
    def put(self,source,path):
        (self.root/path).write_bytes(Path(source).read_bytes())
    def get(self,path,destination):
        if self.fail: raise OSError('simulated interrupted retrieval')
        Path(destination).write_bytes((self.root/path).read_bytes())


def test_bundle_publication_preserves_original_and_refuses_relaunch(tmp_path):
    from tradingagents.research.onchain_replication.preservation import transfer_bundle
    row=record(tmp_path/'source',b'preserve me')
    transport=LocalTransport(tmp_path/'remote')
    work=tmp_path/'attempt'
    result=transfer_bundle([row],work,remote='batch-0',transport=transport,
                           allowed_roots=[tmp_path],start_index=0)
    assert result['files']==1 and result['raw_bytes']==11
    assert (work/'complete.json').exists() and not (work/'failed.json').exists()
    assert not (work/'bundle.tar').exists() and not (work/'recovered.tar').exists()
    assert (tmp_path/'source').read_bytes()==b'preserve me'
    with pytest.raises(FileExistsError):
        transfer_bundle([row],work,remote='batch-0',transport=transport,
                        allowed_roots=[tmp_path],start_index=0)


def test_interrupted_transfer_retains_attempt_and_never_publishes_completion(tmp_path):
    from tradingagents.research.onchain_replication.preservation import transfer_bundle
    row=record(tmp_path/'source',b'preserve me')
    work=tmp_path/'attempt'
    with pytest.raises(OSError,match='interrupted'):
        transfer_bundle([row],work,remote='batch-0',transport=LocalTransport(tmp_path/'remote',True),
                        allowed_roots=[tmp_path],start_index=0)
    assert (work/'failed.json').exists() and not (work/'complete.json').exists()
    assert (work/'bundle.tar').exists()
    assert (tmp_path/'source').read_bytes()==b'preserve me'


@pytest.mark.parametrize('emitted,expected,success', [(b'abc',3,True),(b'abcd',3,False),(b'ab',3,False)])
def test_bounded_receiver_refuses_size_mismatch_without_excess_disk_write(tmp_path,emitted,expected,success):
    import sys
    from tradingagents.research.onchain_replication.preservation import receive_bounded
    target=tmp_path/'download'
    command=[sys.executable,'-c','import sys;sys.stdout.buffer.write('+repr(emitted)+')']
    if success:
        receive_bounded(command,target,expected_bytes=expected,max_seconds=5,bytes_per_second=1024**2)
        assert target.read_bytes()==emitted
    else:
        with pytest.raises(ValueError,match='size'):
            receive_bounded(command,target,expected_bytes=expected,max_seconds=5,bytes_per_second=1024**2)
        assert target.stat().st_size<=expected


def test_bounded_receiver_kills_stalled_child(tmp_path):
    import sys
    from tradingagents.research.onchain_replication.preservation import receive_bounded
    with pytest.raises(TimeoutError):
        receive_bounded([sys.executable,'-c','import time;time.sleep(10)'],tmp_path/'download',
                        expected_bytes=1,max_seconds=.05,bytes_per_second=1024**2)
