"""Actual current compact terminal to bounded fixed CPU feature batches.

Uses the existing reviewed native numeric map without invoking its old owner or
seal route. All dynamic sources are explicitly admitted. Resident originals held
by the terminal, aliases/autograd, model state and RSS remain outside its numeric
batch allowance. This does not select an executor or authorize an empirical fit.
"""
from functools import lru_cache
import importlib.util
import json
import os
from pathlib import Path
import threading

from . import compact_terminal, compact_owner, score_batches as io
from .feature_pipeline import PreparedFeatures
from .feature_residency import FixedFeatureMap
from .provenance import file_hash, freeze, thaw

require = io._require
ROOT = Path(__file__).resolve().parents[3]
NATIVE = 'research/onchain-paper-replication-2026-09-24/full_sources/terminal-output-lifetime-2026-10-01/native_map.py'


@lru_cache(maxsize=1)
def _api():
    spec = importlib.util.spec_from_file_location('compact_native_numeric',ROOT/NATIVE)
    module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def required_sources():return set(_api().SOURCES)|{str(Path(__file__).resolve().relative_to(ROOT))}


def _metadata(path,expected,cap):
    root,fd = io._open(path.parent)
    try:
        raw = io._read(fd,path.name,cap);io._root(root,fd)
        require(io._hash(raw) == expected,'compact native metadata hash differs')
        return json.loads(raw)
    finally:io._cleanup((lambda:os.close(fd),))


class _Features(FixedFeatureMap):
    def __init__(self,mapping,terminal,hashes,boundary,chunk):
        self._mapping = mapping;self._terminal = terminal
        self._hashes = freeze(hashes);self._boundary = boundary;self._chunk = chunk;self._lock = threading.Lock()
    def __len__(self):return len(self._mapping)
    def __iter__(self):return iter(self._mapping)
    def __getitem__(self,key):return self.load_batch([key])[key]
    def live_tensor_bytes(self):
        require(self._lock.acquire(blocking=False),'concurrent compact native operation')
        try:return self._mapping.live_tensor_bytes()
        finally:self._lock.release()
    def verified_hashes(self):
        require(self._lock.acquire(blocking=False),'concurrent compact native operation')
        try:
            actual = self._mapping.verified_hashes();self._terminal._verify(full=False)
            require(actual == dict(self._hashes),'compact native feature population differs');return actual
        finally:self._lock.release()
    def load_batch(self,keys):
        require(self._lock.acquire(blocking=False),'concurrent compact native operation')
        loaded = None
        try:
            loaded = self._mapping.load_batch(keys)
            self._terminal._verify(full=False);self._mapping.live_tensor_bytes()
            # Recheck returned values after the numeric map's final live callback.
            for h,f in loaded.items():
                require(self._boundary.identity(f['mcm'].numpy(),f['edge_index'].numpy(),self._chunk) == self._hashes[h],
                    'compact native returned feature bytes changed')
            return loaded
        except BaseException:
            if loaded is not None:loaded.clear()
            loaded = None;f = None
            raise
        finally:self._lock.release()


def prepare(terminal,*,input_name):
    require(type(terminal) is compact_terminal.Receipt,'actual compact terminal Receipt required')
    terminal.check();owner = terminal._owner;bound = owner.bound;run = bound._run;ad = run.admission
    selected = json.loads(run.read_input('execution_job'))['payload']['representation_jobs'][bound.record['representation']]
    item = json.loads(run.read_input(selected['plan_input']))['producers'][bound.record['producer']]
    require(type(input_name) is str and input_name in ad.inputs
        and item.get('compact_native_features_input') == selected.get('compact_native_features_input') == input_name,
        'selected compact native feature policy differs')
    require(item.get('compact_terminal_input') == selected.get('compact_terminal_input') == terminal.record['input'],
        'compact native terminal policy differs')
    m = _api();settings = m.policy(json.loads(run.read_input(input_name)))
    require(max(settings['max_numeric_bytes'],settings['max_live_tensor_bytes']) < 2**63,
        'compact native numeric allowance differs')
    def sources():
        for name in required_sources():
            sha = ad.experiment['source_files'].get(name)
            require(sha is not None and file_hash(ROOT/name) == sha and file_hash(ad.root/name) == sha,
                'compact native dynamic source differs')
    def lease():
        terminal.lease();sources();terminal._verify(full=False)
    lease();cap = json.loads(run.read_input(terminal.record['input']))['max_metadata_bytes']
    reference = terminal.record['publication'];publication = _metadata(Path(reference['path']),reference['sha256'],cap)
    closure = publication['closure'];binding = closure['binding'];hashes = binding['feature_hashes']
    require(set(hashes) == set(closure['graph_receipts']) and hashes,'compact native required graph union differs')
    base = ad.root/'research_artifacts/onchain_compact_graphs'/bound.record['workflow_identity']/bound.record['experiment']
    compact_owner.entries(base,set(hashes),required=set(hashes));refs = {}
    for h in sorted(hashes):
        path = base/h
        record = _metadata(path/'complete.json',closure['graph_receipts'][h],io.META_LIMIT)
        start = _metadata(path/'start.json',record['start_sha256'],io.META_LIMIT)
        require(record['owner'] == terminal.record['owner'] and record['graph_hash'] == h
            and record['feature_hash'] == hashes[h],'compact native saved graph binding differs')
        name = record['policy_input']
        require(item.get('compact_graph_output_input') == selected.get('compact_graph_output_input') == name
            and ad.inputs[name]['sha256'] == record['policy_sha256'],'compact native graph output policy differs')
        output = json.loads(run.read_input(name))
        component = path/'artifact/manifest.json'
        manifest,_,_,_ = m.reader.inspect_component(component,record['artifact_sha256'],start,ad.root,
            output['max_manifest_bytes'],output['max_artifact_bytes'],record['numeric_payload_bytes'])
        require(set(manifest['arrays']) == {'array-000000.npy','array-000001.npy'},'compact native array membership differs')
        a = manifest['arrays']['array-000000.npy'];e = manifest['arrays']['array-000001.npy']
        require(len(a['shape']) == len(e['shape']) == 2 and a['dtype'] == 'float32' and e['dtype'] == 'int64'
            and all(type(v) is int and v > 0 for v in a['shape']) and e['shape'][0] == 2,'compact native array layout differs')
        payload = 4*a['shape'][0]*a['shape'][1]+16*e['shape'][1]
        require(payload == record['numeric_payload_bytes'] and payload <= settings['max_live_tensor_bytes']
            and 2*payload+9*settings['chunk_entries'] <= settings['max_numeric_bytes'],
            'compact native single-graph capacity insufficient')
        refs[h] = {'path':str(component),'sha256':record['artifact_sha256'],'context':start,
            'nodes':a['shape'][0],'motifs':a['shape'][1],'edge_shape':e['shape'],'feature_hash':hashes[h],
            'max_manifest_bytes':output['max_manifest_bytes'],'max_artifact_bytes':output['max_artifact_bytes']}
    mapping = m._NativeMap(ad.root,refs,settings,lease=lease,read_lease=lease)
    features = _Features(mapping,terminal,hashes,m.boundary,settings['chunk_entries'])
    require(features.verified_hashes() == hashes,'compact native saved population changed')
    terminal.check();sources();terminal._verify(full=False)
    return PreparedFeatures(features,binding,None)
