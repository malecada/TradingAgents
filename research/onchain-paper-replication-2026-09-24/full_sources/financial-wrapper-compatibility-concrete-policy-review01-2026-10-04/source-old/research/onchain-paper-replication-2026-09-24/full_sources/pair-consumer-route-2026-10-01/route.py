"""Construct a dictionary pair consumer only from actual admitted owner settings.

This does not publish/admit sampler or dictionary artifacts, run the complete
workload, or authorize empirical allocation. Those outer joins remain required.
"""
import importlib.util
from pathlib import Path

from tradingagents.research.onchain_replication.provenance import file_hash,thaw

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
ownership=load('consumer_actual_ownership',HERE.parent/'pair-owner-route-2026-09-30/ownership.py')
serial=load('consumer_serial_engine',HERE.parent/'pair-serial-composition-2026-09-30/serial.py')
SOURCES=tuple(str(Path(p).relative_to(ROOT)) for p in (__file__,serial.__file__,serial.extent.__file__))

def require(value,message):
    if not value:raise ValueError(message)

def sources(owned):
    ad=owned.workload.bound._run.admission
    for name in SOURCES:
        expected=ad.experiment['source_files'].get(name)
        require(expected is not None and file_hash(ROOT/name)==expected
            and file_hash(ad.root/name)==expected,'consumer implementation is not admitted or changed')

def dictionary_consumer(owned,samples):
    require(type(owned) is ownership.OwnedJournal,'actual admitted pair owner required')
    owned.workload.bound.check();owned.lease();sources(owned)
    route=owned.workload
    scope=route.sample_scope(samples)
    def lease():
        owned.lease();sources(owned);route.lease()
    lease()
    return serial.Serial(owned.journal,context=thaw(route.bound.context),
        policy=thaw(route.bound.limits),config=thaw(route.descriptor['configs']['matching']),
        workload_sha256=scope,lease=lease,
        operations_per_checkpoint=route.control['operations_per_checkpoint'],
        max_checkpoints=route.control['max_checkpoints'])
