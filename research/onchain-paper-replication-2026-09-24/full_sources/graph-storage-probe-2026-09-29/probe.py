"""Synthetic production aggregation/storage observation; no empirical data.

Fixed 250,000 distinct edges and 500,000 distinct addresses, random-looking fixed
identities, seven source boundaries. Observations are not upper bounds. All own
SQLite open files (including unlinked sort files) are sampled and inode-deduped.
"""
import hashlib
import json
import os
from pathlib import Path
import threading
import time

from tradingagents.research.onchain_replication.aggregation import SourceBoundary
from tradingagents.research.onchain_replication.contracts import Transaction
from tradingagents.research.onchain_replication.weekly import build_weekly
from tradingagents.research.onchain_replication.graph_store import save_graph

ROOT = Path(__file__).resolve().parent
OUT = ROOT/'synthetic01'
OUT.mkdir(exist_ok=False)
N = 250_000
stop = threading.Event()
phase = 'ingestion'
peaks = {}
errors = []


def sample():
    items = {}
    for p in OUT.rglob('*'):
        try:
            if p.is_file():
                s=p.stat();items[(s.st_dev,s.st_ino)]=s.st_blocks*512
        except FileNotFoundError:
            pass
    for fd in Path('/proc/self/fd').iterdir():
        try:
            name=os.readlink(fd)
            if 'etilqs_' in name or str(OUT) in name:
                s=fd.stat();items[(s.st_dev,s.st_ino)]=s.st_blocks*512
        except FileNotFoundError:
            pass
    return sum(items.values())


def monitor():
    while not stop.is_set():
        try:
            label=phase;peaks[label]=max(peaks.get(label,0),sample())
        except Exception as e:
            errors.append(type(e).__name__+': '+str(e));return
        stop.wait(.02)


def events():
    global phase
    for part in range(7):
        first,last=N*part//7,N*(part+1)//7
        source=hashlib.sha256(('source'+str(part)).encode()).hexdigest()
        for i in range(first,last):
            h=hashlib.sha256(str(i).encode()).hexdigest()
            # First two hex digits distinguish address sides; fixed hash suffix
            # exercises unsorted B-tree insertion rather than a sequential key.
            yield Transaction('ETH','0x'+h,'2022-07-25T12:00:00Z',
                              '0x00'+h[:38],'0x01'+h[:38],1.23456789,1,source,'synthetic')
        yield SourceBoundary(source,last-first)
    phase='index_sort_graph_construction'


thread=threading.Thread(target=monitor,daemon=True);thread.start()
begin=time.monotonic()
config=json.loads(Path('research/onchain-paper-replication-2026-09-24/config/graph.json').read_bytes())
try:
    iterator=build_weekly(events(),config,coverage=[('2022-07-25T00:00:00Z','2022-08-01T00:00:00Z')],
                          scratch=OUT/'scratch',workspace=OUT/'aggregation')
    graph=next(iterator)
    assert graph.raw_count==graph.admitted_count==N
    assert len(graph.node_ids)==2*N and graph.edge_index.shape==(2,N)
    phase='graph_save_with_live_database'
    manifest=save_graph(OUT/'graph',graph)
    peaks[phase]=max(peaks.get(phase,0),sample())
    try:
        next(iterator)
    except StopIteration:
        pass
    else:
        raise AssertionError('unexpected second graph')
finally:
    stop.set();thread.join()
assert not errors,errors
value={'schema_version':1,'rows':N,'nodes':2*N,'edges':N,'source_boundaries':7,
       'elapsed_seconds':time.monotonic()-begin,'sample_seconds':.02,
       'sampled_peak_allocated_bytes_by_phase':peaks,'sampled_peak_allocated_bytes':max(peaks.values()),
       'final_allocated_bytes':sample(),
       'files':{str(p.relative_to(OUT)):{'bytes':p.stat().st_size,'allocated_bytes':p.stat().st_blocks*512}
                for p in OUT.rglob('*') if p.is_file()},
       'qualification':'Synthetic measured scenario only, not an upper bound or empirical admission; no Parquet projection/decoder in this workload; unlinked own SQLite sort files included via fstat.'}
(ROOT/'result.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(value))
