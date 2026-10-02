"""Full/partial compact chunks replayed through verified archive consumption."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import struct

import pytest
from tradingagents.research.onchain_replication import compact_pair_log as events


def sha(value): return hashlib.sha256(value).hexdigest()


def fixture(tmp_path):
    from tradingagents.research.onchain_replication import archived_pair_log as reader
    root=tmp_path/'log';owner=sha(b'owner')
    scope={name:sha(name.encode()) for name in events.FIELDS}
    writer=events.PairLog(root,owner=owner,scope=scope,limits={'chunk_events':3,
        'max_events':12,'max_pairs':4,'max_logical_bytes':12*events.RECORD_BYTES+2*events.io.META_LIMIT},
        max_iterations=10,lease=lambda:None)
    writer.begin(sha(b'purpose0'),sha(b'pair0'))
    writer.progress(sha(b'checkpoint'))
    writer.complete(.25,'temperature_complete',1)
    writer.begin(sha(b'purpose1'),sha(b'pair1'))
    writer.complete(.75,'iteration_cap',2)
    terminal=writer.finish()
    chunks=[(root/events._name(i)).read_bytes() for i in range(2)]
    kwargs=dict(start_bytes=(root/'start.json').read_bytes(),terminal_bytes=(root/'terminal.json').read_bytes(),
        terminal_sha256=terminal,owner=owner,scope=scope,
        read_chunk=lambda index,extent:chunks[index],lease=lambda:None)
    return reader,root,chunks,kwargs


def test_actual_archive_consumer_replays_full_and_partial_chunks(tmp_path):
    from tradingagents.research.onchain_replication import archive_chunks,archive_consume
    spec=importlib.util.spec_from_file_location('archive_fixture',Path(__file__).with_name('test_archive_chunks.py'))
    base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
    reader,root,chunks,kwargs=fixture(tmp_path)
    original=events.verify(root,owner=kwargs['owner'],scope=kwargs['scope'],
        terminal_sha256=kwargs['terminal_sha256'],lease=lambda:None)
    transport=base.Transport(tmp_path/'remote');receipts=[]
    for index,raw in enumerate(chunks):
        binding=sha(kwargs['start_bytes']+str(index).encode())
        attempt=tmp_path/f'copy-{index}'
        reference=archive_chunks.preserve(source=root/events._name(index),attempt=attempt,
            expected_sha256=sha(raw),expected_bytes=len(raw),scope=binding,remote=f'event-{index}',
            transport=transport,lease=lambda:None,free_floor_bytes=0)
        receipts.append(((attempt/'complete.json').read_bytes(),reference,binding))
        # Only disposable synthetic originals; production eviction is not implemented.
        shutil.rmtree(attempt);(root/events._name(index)).unlink()
    def read(index,extent):
        raw,reference,binding=receipts[index]
        result=archive_consume.consume(receipt_bytes=raw,receipt_sha256=reference,
            expected_scope=binding,attempt=tmp_path/f'consume-{index}',transport=transport,
            lease=lambda:None,free_floor_bytes=0)
        assert len(result)==extent
        return result
    kwargs['read_chunk']=read
    result=reader.verify(**kwargs)
    assert all(result[k]==v for k,v in original.items())
    scores=b''.join(struct.pack('<Qd32s',i,score,bytes.fromhex(sha(f'purpose{i}'.encode())))
        for i,score in enumerate((.25,.75)))
    assert result['matching_scores_sha256']==sha(scores)
    assert result['checkpoint_references_sha256']==sha(struct.pack('<Q32s',1,bytes.fromhex(sha(b'checkpoint'))))
    assert all(not (tmp_path/f'consume-{i}'/'payload.bin').exists() for i in range(2))


@pytest.mark.parametrize('failure',['corrupt','swapped','short','mutable','missing','lease'])
def test_bad_or_revoked_chunk_never_returns_success(tmp_path,failure):
    reader,root,chunks,kwargs=fixture(tmp_path)
    def lease():
        if getattr(lease,'revoked',False):raise RuntimeError('revoked')
    def read(index,extent):
        raw=chunks[index]
        if failure=='corrupt':raw=bytes([raw[0]^1])+raw[1:]
        if failure=='swapped':raw=chunks[1-index]
        if failure=='short':raw=raw[:-1]
        if failure=='mutable':raw=bytearray(raw)
        if failure=='missing':raise FileNotFoundError('chunk unavailable')
        if failure=='lease':lease.revoked=True
        return raw
    kwargs.update(read_chunk=read,lease=lease)
    with pytest.raises((ValueError,OSError,RuntimeError)):reader.verify(**kwargs)


@pytest.mark.parametrize('failure',['owner','scope','terminal_hash','failed','chunks','state','extra'])
def test_invalid_header_or_denominator_refused(tmp_path,failure):
    reader,root,chunks,kwargs=fixture(tmp_path)
    if failure=='owner':kwargs['owner']='0'*64
    elif failure=='scope':kwargs['scope']={name:'0'*64 for name in events.FIELDS}
    elif failure=='terminal_hash':kwargs['terminal_sha256']='0'*64
    else:
        terminal=json.loads(kwargs['terminal_bytes'])
        if failure=='failed':terminal['status']='failed'
        if failure=='chunks':terminal['chunks']+=1
        if failure=='state':terminal['state']['completed_pairs']+=1
        if failure=='extra':terminal['ignored']='unbound'
        kwargs['terminal_bytes']=events.io._json(terminal);kwargs['terminal_sha256']=sha(kwargs['terminal_bytes'])
    with pytest.raises(ValueError):reader.verify(**kwargs)


def test_previous_chunk_reference_released_before_next_fetch(tmp_path):
    import sys
    reader,root,chunks,kwargs=fixture(tmp_path)
    expected=sys.getrefcount(chunks[0])
    def read(index,extent):
        if index==1:assert sys.getrefcount(chunks[0])==expected
        return chunks[index]
    kwargs['read_chunk']=read
    reader.verify(**kwargs)
