"""Current-owner published samples through the actual dictionary workload.

Only this driver derives pair purposes. It reuses exact completed pair results;
dictionary publication, sampler RNG provenance and empirical release are separate.
"""
import importlib.util
from pathlib import Path
from tradingagents.research.onchain_replication import dictionary
from tradingagents.research.onchain_replication.provenance import file_hash,thaw

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
artifacts=load('dictionary_driver_artifacts',HERE.parent/'sample-artifact-route-2026-10-01/route.py')
workload=load('dictionary_driver_workload',HERE.parent/'pair-workload-2026-09-30/workload.py')
SOURCES=tuple(sorted(set(artifacts.SOURCES)|{str(Path(p).relative_to(ROOT)) for p in
    (__file__,workload.__file__,dictionary.__file__)}))

def require(value,message):
    if not value:raise ValueError(message)

def sources(owned):
    ad=owned.workload.bound._run.admission
    for name in SOURCES:
        expected=ad.experiment['source_files'].get(name)
        require(expected is not None and file_hash(ROOT/name)==expected
            and file_hash(ad.root/name)==expected,'dictionary driver source is not admitted or changed')

def fit(owned,journal,*,artifact_input,event_index,event_sha256):
    require(type(owned) is artifacts.consumer.ownership.OwnedJournal,'actual admitted pair owner required')
    owned.workload.bound.check();owned.lease();sources(owned)
    admitted=artifacts.admit_samples(owned,journal,artifact_input=artifact_input,
        event_index=event_index,event_sha256=event_sha256)
    route=owned.workload
    consumer=artifacts.consumer.dictionary_consumer(owned,admitted.samples)
    def lease():
        admitted.lease();sources(owned);owned.lease()
    def score(purpose,left,right):
        lease()
        require(purpose.get('workload_sha256')==admitted.scope,'dictionary workload scope differs')
        value=consumer(purpose,left,right)
        lease()
        return value
    lease()
    result=workload.fit(admitted.samples,thaw(route.descriptor['configs']['matching']),
        thaw(route.settings),workflow=route.bound.record['workflow_identity'],
        backend=artifacts.consumer.serial.pair.BACKEND,
        max_entries=route.control['max_entries'],score_pair=score)
    require(result['workload_sha256']==admitted.scope,'dictionary result scope differs')
    lease()
    return result
