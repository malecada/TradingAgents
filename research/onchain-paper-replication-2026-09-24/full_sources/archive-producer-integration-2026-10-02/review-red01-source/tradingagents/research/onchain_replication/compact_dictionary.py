"""Current-owner exact dictionary construction and bounded numeric publication.

Consumes a scientific sample Proof, never arbitrary samples or reopened evidence.
Matrices retain the original scalar kernel's ordered-subset reuse. Publication
stores representative sample indices, not another copy of sampled graphs. The
explicit matrix/readback limits bound numeric payload only: SciPy scratch, legacy
identity .tolist()/JSON expansion, parent/sample arrays and Python overhead remain
in the outer workflow/RSS accounting. This does not admit a full representation.
"""
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

import numpy as np
from . import compact_sample_proof, compact_samples, compact_owner, compact_stage
from . import compact_matcher, compact_pair_log, component_store, matching_pair, score_batches as io
from .cache import cache_key
from .dictionary import Dictionary, dictionary_hash
from .provenance import durable_mkdir, file_hash, freeze, thaw

require = io._require
ROOT = Path(__file__).resolve().parents[3]
KERNEL = 'research/onchain-paper-replication-2026-09-24/full_sources/pair-workload-2026-09-30/workload.py'


def directory(proof):
    bound = proof.owner.bound
    return (bound._run.admission.root / 'research_artifacts/onchain_compact_dictionary' /
        bound.record['workflow_identity'] / bound.record['experiment'])


def _sources(proof):
    ad = proof.owner.bound._run.admission; result = {}
    for path in (KERNEL, compact_samples.READER):
        expected = ad.experiment['source_files'].get(path)
        require(expected is not None and file_hash(ROOT / path) == expected
            and file_hash(ad.root / path) == expected, 'compact dictionary numerical source not admitted or changed')
        result[path] = expected
    return result


def _kernel():
    spec = importlib.util.spec_from_file_location('compact_dictionary_kernel', ROOT / KERNEL)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def _prepare(proof, input_name):
    proof.check(); sources = _sources(proof); owner = proof.owner
    run = owner.bound._run; record = owner.bound.record
    selected = json.loads(run.read_input('execution_job'))['payload']['representation_jobs'][record['representation']]
    item = json.loads(run.read_input(selected['plan_input']))['producers'][record['producer']]
    require(type(input_name) is str and input_name in run.admission.inputs
        and selected.get('compact_dictionary_input') == item.get('compact_dictionary_input') == input_name,
        'explicit compact dictionary route differs')
    policy = json.loads(run.read_input(input_name))
    fields = {'schema_version', 'max_matrix_bytes', 'max_identity_array_bytes', 'max_manifest_bytes',
        'max_artifact_bytes', 'max_loaded_array_bytes', 'max_attempt_bytes'}
    require(set(policy) == fields and type(policy['schema_version']) is int and policy['schema_version'] == 1
        and all(type(policy[k]) is int and 0 < policy[k] < 2**63 for k in fields-{'schema_version'})
        and policy['max_manifest_bytes'] <= compact_samples.MANIFEST_LIMIT, 'compact dictionary policy differs')
    count_policy = owner._dictionary_count_policy()
    capacity = count_policy['capacity']; matrix_bytes = 8 * capacity['max_matrix_entries']
    numeric = sum(a.nbytes for g in proof.samples.graphs for a in (g.node_features,g.edge_index,g.edge_features))
    require(matrix_bytes <= policy['max_matrix_bytes'] and matrix_bytes <= policy['max_loaded_array_bytes'],
        'compact dictionary matrix/readback capacity insufficient')
    require(numeric <= policy['max_identity_array_bytes'], 'legacy dictionary identity input capacity insufficient')
    reserved = policy['max_artifact_bytes'] + 3 * io.META_LIMIT
    require(reserved <= policy['max_attempt_bytes'], 'compact dictionary output reservation insufficient')
    start = {'schema_version': 1, 'kind': 'compact-dictionary', 'owner': owner.identity,
        'workload_sha256': proof.scope, 'sample_proof_sha256': cache_key(thaw(proof.record)),
        'sample_publication_sha256': proof.record['publication_sha256'], 'sources': sources,
        'policy_input': input_name, 'policy_sha256': run.admission.inputs[input_name]['sha256'],
        'count_policy': count_policy, 'reserved_output_logical_bytes': reserved,
        'reserved_matrix_bytes': matrix_bytes, 'reserved_readback_bytes': matrix_bytes,
        'legacy_identity_input_bytes_upper_bound': numeric, 'resumable': False,
        'sample_provenance_admitted': True, 'representation_admitted': False}
    io._json(start)
    return policy, start, count_policy


def _payload(proof, dictionary, matrices):
    samples = proof.samples; settings = thaw(proof._published._draws._training.settings)
    require(type(dictionary) is Dictionary and dictionary.sample_hash == samples.identity
        and dictionary.training_graph_hashes == samples.source_hashes
        and thaw(dictionary.config) == settings | {'pair_execution': matching_pair.BACKEND}
        and dictionary.matching_config_hash == cache_key({'config': thaw(proof.owner.matching), 'backend': matching_pair.BACKEND}),
        'compact dictionary sample/configuration differs')
    indices = []
    for graph in dictionary.representatives:
        choices = [i for i, g in enumerate(samples.graphs) if graph is g]
        require(len(choices) == 1, 'dictionary representative must be an actual ordered sample')
        indices.append(choices[0])
    groups = dictionary.memberships
    require(len(indices) == len(groups) == settings['size'] and len(set(indices)) == len(indices)
        and sorted(j for group in groups for j in group) == list(range(len(samples.graphs)))
        and all(type(j) is int for group in groups for j in group)
        and all(i in group for i, group in zip(indices, groups, strict=True)), 'dictionary membership partition differs')
    require(dictionary.identity == dictionary_hash(dictionary), 'compact dictionary identity differs')
    return {'representative_sample_indices': indices, 'memberships': groups,
        'sample_hash': dictionary.sample_hash, 'training_graph_hashes': dictionary.training_graph_hashes,
        'config': thaw(dictionary.config), 'matching_config_hash': dictionary.matching_config_hash,
        'identity': dictionary.identity, 'hierarchy': thaw(dictionary.hierarchy), 'matrices': matrices}


def _fingerprint(payload):
    """Hash numeric byte views without .tolist or a whole-array boolean copy."""
    def visit(value):
        if isinstance(value, np.ndarray):
            require(value.dtype == np.dtype('float64') and value.flags.c_contiguous,
                'dictionary matrix dtype/contiguity differs')
            digest = hashlib.sha256()
            if value.size:
                raw = memoryview(value).cast('B')
                for start in range(0,len(raw),262144): digest.update(raw[start:start+262144])
            return {'array_sha256':digest.hexdigest(),'shape':list(value.shape),'dtype':str(value.dtype)}
        if isinstance(value, dict): return {k:visit(v) for k,v in value.items()}
        if isinstance(value,(list,tuple)): return [visit(x) for x in value]
        return value
    return cache_key(visit(payload))


class Produced:
    def __init__(self, proof, stage, dictionary, matrices, policy, start, context, record, root, inode, reference, reader):
        self._proof = self._authority = proof; self._stage = stage
        self._dictionary = dictionary; self._matrices = matrices; self._policy = freeze(policy)
        self._start = freeze(start); self._context = freeze(context); self._record = freeze(record)
        self._directory = root; self._inode = inode; self._reference = reference; self._reader = reader
        self._pin = cache_key(self._configuration())

    dictionary = property(lambda self:self._dictionary)
    matrices = property(lambda self:self._matrices)
    record = property(lambda self:self._record)
    directory = property(lambda self:self._directory)
    receipt_sha256 = property(lambda self:self._reference)

    def _configuration(self):
        return {'policy':thaw(self._policy),'start':thaw(self._start),'context':thaw(self._context),
            'record':thaw(self._record),'directory':str(self._directory),'inode':self._inode,'reference':self._reference}

    def _integrity(self):
        require(self._proof is self._authority and cache_key(self._configuration()) == self._pin,
            'compact dictionary view changed')

    def lease(self):
        self._integrity(); self._proof.lease(); self._integrity()

    def _numeric(self):
        payload = _payload(self._proof,self.dictionary,self.matrices)
        require(_fingerprint(payload) == self.record['numeric_fingerprint'], 'compact dictionary numeric payload changed')
        return payload

    def _evidence(self):
        self._integrity(); stage = self._stage; owner = self._proof.owner
        require(owner.stages.get('dictionary') is stage and stage.owner is owner and stage.closed
            and stage.reference == self.record['stage_sha256'], 'actual completed dictionary stage differs')
        stage.integrity()
        info = stage.root.lstat()
        require((info.st_dev,info.st_ino) == tuple(self.record['stage_inode']) == stage.inode,
            'completed dictionary stage directory changed')
        names = {'intent.json','matching','checkpoints','stage-complete.json'}
        compact_owner.entries(stage.root,names,required=names)
        compact_owner.exact(stage.root,'intent.json',stage.intent)
        compact_owner._stage_content(stage)
        root,fd = io._open(self.directory)
        try:
            info = os.fstat(fd); require((info.st_dev,info.st_ino) == self._inode,'dictionary publication directory changed')
            names = {'start.json','artifact','complete.json'}; compact_owner.entries(root,names,required=names)
            require(io._read(fd,'start.json',io.META_LIMIT) == io._json(thaw(self._start)), 'dictionary start changed')
            raw = io._read(fd,'complete.json',io.META_LIMIT)
            require(io._hash(raw) == self._reference and raw == io._json(thaw(self.record)), 'dictionary receipt changed')
            args = (root/'artifact/manifest.json',self.record['artifact_sha256'],thaw(self._context))
            manifest,_,_,_ = self._reader.inspect_component(*args,root,self._policy['max_manifest_bytes'],
                self._policy['max_artifact_bytes'],self._policy['max_loaded_array_bytes'])
            size = (root/'artifact/manifest.json').stat().st_size
            require(size == self.record['encoded_manifest_bytes']
                and size + sum(x['bytes'] for x in manifest['arrays'].values()) == self.record['encoded_artifact_bytes'],
                'dictionary encoded size differs')
            io._root(root,fd); return args
        finally: os.close(fd)

    def check(self):
        self.lease(); self._proof.check(); _sources(self._proof)
        payload = self._numeric(); args = self._evidence()
        loaded = self._reader.read_component(*args,root=self.directory,
            max_manifest_bytes=self._policy['max_manifest_bytes'], max_artifact_bytes=self._policy['max_artifact_bytes'],
            max_array_bytes=self._policy['max_loaded_array_bytes'],lease=self.lease)
        compact_samples._equal_numeric(loaded,payload); del loaded
        self.lease(); self._proof._final(); self._numeric(); self._evidence()


def produce(proof, *, input_name):
    require(type(proof) is compact_sample_proof.Proof, 'actual scientific sample Proof required')
    owner = proof.owner
    with compact_owner._held(owner) as held:
        return _produce_locked(proof, input_name=input_name, held=held)


def _produce_locked(proof, *, input_name, held):
    owner = proof.owner; held.check(owner)
    fd = None; log = None; claimed = False
    try:
        policy,start,count_policy = _prepare(proof,input_name)
        require(not owner.stages and owner.active is None,'dictionary stage already claimed')
        root = directory(proof)
        require(root.is_absolute() and root.resolve() == root and not compact_owner.present(root),
            'dictionary output namespace already claimed or redirected')
        kernel = _kernel(); reader = compact_samples._reader()
        proof.lease(); proof._final(); durable_mkdir(root.parent)
        require(root.resolve() == root,'dictionary output parent redirected')
        proof.lease()  # Refresh after potentially long evidence hashing/parent setup.
        root.mkdir(); claimed = True
        parent,parent_fd = io._open(root.parent)
        try: os.fsync(parent_fd); io._root(parent,parent_fd)
        finally: os.close(parent_fd)
        root,fd = io._open(root); info = os.fstat(fd); inode = (info.st_dev,info.st_ino)
        require(info.st_dev == owner.root.stat().st_dev,'dictionary output device differs')
        start_sha = io._write(fd,'start.json',io._json(start))
        # The outer lock owns all transitions, including the internal stage calls.
        stage = owner._begin('dictionary',proof.scope,count_policy['capacity']['max_pairs'],count_policy)
        def lease():
            stage.lease(); proof.lease(); io._root(root,fd)
            require(io._read(fd,'start.json',io.META_LIMIT) == io._json(start),'dictionary start changed')
        p = thaw(owner.policy)
        def compute(event_log, live):
            nonlocal log
            log = event_log
            matcher = compact_matcher.CompactMatcher(log,config=thaw(owner.matching),context=thaw(owner.bound.context),
                policy=p['pair'],workload_sha256=proof.scope,schedule=p['schedule'],lease=live)
            live(); proof._final()
            actual = kernel.fit(proof.samples,thaw(owner.matching),thaw(proof._published._draws._training.settings),
                workflow=owner.bound.record['workflow_identity'],backend=matching_pair.BACKEND,
                max_entries=count_policy['capacity']['max_matrix_entries'],score_pair=matcher)
            pin = _fingerprint(_payload(proof,actual['dictionary'],actual['matrices']))
            return actual,pin
        ledger = getattr(owner, '_archive_operations', None)
        if ledger is None:
            log = compact_pair_log.PairLog(stage.root/'matching',owner=owner.identity,scope=thaw(stage.scope),
                limits=p['log'],max_iterations=owner.matching['max_iterations'],lease=lease)
            actual,numeric_pin = compute(log,lease)
        else:
            from . import archive_owner_writer
            (actual,numeric_pin), writer_receipt = archive_owner_writer._run_locked(ledger,stage,compute,
                held=held,science_lease=lease)
        require(actual['workload_sha256'] == proof.scope,'dictionary workload scope differs')
        d = actual['dictionary']; matrices = actual['matrices']; payload = _payload(proof,d,matrices)
        fingerprint = _fingerprint(payload)  # Pin before seal/live callbacks.
        require(fingerprint==numeric_pin,'dictionary payload changed during writer completion')
        context = start | {'dictionary_identity':d.identity,'numeric_fingerprint':fingerprint,
            'stage_inode':list(stage.inode)}
        manifest,artifact,numeric = compact_samples._encoded_size(payload,context,policy['max_manifest_bytes'])
        require(artifact <= policy['max_artifact_bytes'] and numeric <= policy['max_matrix_bytes']
            and numeric <= policy['max_loaded_array_bytes'],'dictionary numeric publication capacity exceeded')
        count = log.state['completed_pairs']
        if ledger is None:
            terminal = log.finish()
            stage_ref = owner._finish_stage(stage,log_terminal_sha256=terminal,stream_terminal_sha256=None,completed_pairs=count)
        else:
            from . import archive_owner_stage
            stage_ref = archive_owner_stage._execute_locked(ledger,stage,stream_terminal_sha256=None,
                publish=True,held=held,science_lease=lease)
        proof.check(); _sources(proof); proof.lease(); proof._final()
        require(_fingerprint(_payload(proof,d,matrices)) == fingerprint,'dictionary payload changed before publication')
        io._root(root,fd)
        require(io._read(fd,'start.json',io.META_LIMIT) == io._json(start),'dictionary start changed before publication')
        path = component_store.save_component(root/'artifact',payload,context)
        record = context | {'start_sha256':start_sha,'stage_sha256':stage_ref,'completed_pairs':count,
            'encoded_manifest_bytes':manifest,'encoded_artifact_bytes':artifact,'matrix_payload_bytes':numeric,
            'artifact_sha256':file_hash(path),'numeric_artifact_published':True}
        reference = io._write(fd,'complete.json',io._json(record))
        result = Produced(proof,stage,d,matrices,policy,start,context,record,root,inode,reference,reader)
        result.check(); return result
    except BaseException as primary:
        cleanup = None
        if claimed:
            try:
                if log is not None and not log.closed:
                    try: log.fail('dictionary producer failed')
                    except BaseException as failure:
                        primary.add_note('Failed log terminal: ' + repr(failure))
                        try: log.close()
                        except BaseException as failure: cleanup = failure
            finally:
                # Failed log publication needs its live stage lease; the held
                # transition lock prevents reuse meanwhile. Cleanup must never
                # skip irrevocable poisoning or the attempt failure marker.
                owner.poisoned = True
                if fd is not None:
                    try: io._write(fd,'failed.json',io._json({'schema_version':1,'status':'failed','owner':owner.identity}))
                    except (OSError,ValueError) as failure:
                        primary.add_note('Failed attempt marker: ' + repr(failure))
            if cleanup is not None:
                fatal = compact_matcher.CleanupFailure('dictionary log cleanup unresolved; worker must stop')
                fatal.add_note('Cleanup failure: ' + repr(cleanup))
                raise fatal from primary
        raise
    finally:
        if fd is not None: io._release(lambda: os.close(fd))
