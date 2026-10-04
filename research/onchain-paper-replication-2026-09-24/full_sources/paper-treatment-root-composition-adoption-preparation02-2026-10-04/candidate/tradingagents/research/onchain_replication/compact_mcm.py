"""Required-graph MCM production from an actual current compact dictionary.

Runs the unchanged resident array-neighborhood kernel, preserves row-major
purpose acknowledgement through MCMScoreStream, and publishes the completed
scores with the existing strict float32 output route. All transitions share one
owner lock. Numeric allowances exclude parents/samples/dictionary matrices,
matching/stream scratch, Python overhead and mapped-page RSS. No native producer,
complete representation, cold reuse or empirical release is admitted here.
"""
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

import numpy as np
from . import compact_dictionary, compact_owner, compact_stage, compact_policy
from . import compact_matcher, compact_pair_log, compact_mcm_publication as publication, score_batches as io
from .mcm_score_stream import MCMScoreStream
from .cache import cache_key
from .matching_pair import BACKEND
from .matching_identity import graph_identity
from .neighborhoods import graph_hash as hash_graph, node_order_hash
from .provenance import durable_mkdir, file_hash, freeze, thaw

require = io._require
ROOT = Path(__file__).resolve().parents[3]
KERNEL = 'research/onchain-paper-replication-2026-09-24/full_sources/mcm-array-kernel-2026-10-01/kernel.py'


def _training(dictionary): return dictionary._proof._published._draws._training


def directory(dictionary, graph_hash):
    bound = dictionary._proof.owner.bound
    return (bound._run.admission.root/'research_artifacts/onchain_compact_mcm'/
        bound.record['workflow_identity']/bound.record['experiment']/('mcm-'+graph_hash))


def _sources(dictionary):
    result = compact_dictionary._sources(dictionary._proof); ad = dictionary._proof.owner.bound._run.admission
    sha = ad.experiment['source_files'].get(KERNEL)
    require(sha is not None and file_hash(ROOT/KERNEL) == sha and file_hash(ad.root/KERNEL) == sha,
        'compact MCM kernel source not admitted or changed')
    return result | {KERNEL:sha}


def _kernel():
    spec = importlib.util.spec_from_file_location('compact_mcm_kernel',ROOT/KERNEL)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def _graph(dictionary, key):
    training = _training(dictionary); training._integrity()
    require(type(key) is str and key in training.descriptor['required_graphs'], 'exact required MCM graph needed')
    matches = [g for g in training.graphs if hash_graph(g) == key]
    require(len(matches) == 1,'actual required MCM graph differs'); return matches[0]


def _original(dictionary, graph, key):
    """Callback-free original ancestry/graph checks after the last live callback."""
    dictionary._proof._final(); dictionary._numeric(); dictionary._evidence()
    training = _training(dictionary); training._integrity()
    require(key in training.descriptor['required_graphs'] and any(g is graph for g in training.graphs)
        and hash_graph(graph) == key,'original required MCM graph changed')


def _matrix(matrix, rows, motifs):
    require(type(matrix) is np.ndarray and matrix.dtype == np.dtype('<f4')
        and matrix.flags.c_contiguous and matrix.shape == (rows,motifs),'MCM matrix dimensions/dtype differ')
    digest = hashlib.sha256(); raw = memoryview(matrix).cast('B')
    for offset in range(0,len(raw),262144): digest.update(raw[offset:offset+262144])
    return digest.hexdigest()


def _prepare(dictionary, key, input_name, output_input):
    dictionary.check(); sources = _sources(dictionary); owner = dictionary._proof.owner
    graph = _graph(dictionary,key); d = dictionary.dictionary
    rows = len(graph.node_ids); motifs = len(d.representatives); pairs = rows*motifs
    matching = thaw(owner.matching); ordered = [graph_identity(g) for g in d.representatives]
    order = node_order_hash(graph.node_ids)
    scope = cache_key({'schema_version':1,'kind':'mcm','workflow':owner.bound.record['workflow_identity'],
        'backend':BACKEND,'graph':key,'node_order':order,'dictionary':d.identity,
        'ordered_motifs':ordered,'matching':matching,'dtype':'float32'})
    expected = {'graph':key,'node_order':order,'dictionary':d.identity,
        'ordered_motifs':cache_key(ordered),'matching':d.matching_config_hash,'workflow':scope}
    run = owner.bound._run; bound = owner.bound.record
    selected = json.loads(run.read_input('execution_job'))['payload']['representation_jobs'][bound['representation']]
    item = json.loads(run.read_input(selected['plan_input']))['producers'][bound['producer']]
    require(type(input_name) is str and input_name in run.admission.inputs
        and selected.get('compact_mcm_input') == item.get('compact_mcm_input') == input_name,
        'explicit compact MCM route differs')
    policy = json.loads(run.read_input(input_name))
    require(set(policy) == {'schema_version','max_entries','max_workflow_metadata_bytes','numeric'}
        and type(policy['schema_version']) is int and policy['schema_version'] == 1
        and type(policy['max_entries']) is int and 0 < pairs <= policy['max_entries'] < 2**63
        and type(policy['max_workflow_metadata_bytes']) is int
        and 3*io.META_LIMIT*(len(owner.required)-1) <= policy['max_workflow_metadata_bytes'] < 2**63,
        'compact MCM policy/cell/metadata allowance differs')
    kernel = _kernel(); kernel.validate_policy(policy['numeric'],pairs)
    output_policy, output_reserved = publication._output_policy(owner,output_input,pairs)
    pair_reserved = compact_policy.validate(thaw(owner.policy),kind='mcm',pairs=pairs)['logical_reservation_bytes']+compact_owner.STAGE_BYTES
    require(owner.reserved+pair_reserved <= owner.maximum,'compact MCM workflow pair reservation insufficient')
    name = 'mcm-'+key
    require(owner.active is None and name in owner.required and name not in owner.stages
        and not compact_owner.present(owner.root/name),'MCM stage already claimed or active')
    output_path = (run.admission.root/'research_artifacts/onchain_compact_outputs'/
        bound['workflow_identity']/bound['experiment']/name)
    require(output_path.resolve() == output_path and not compact_owner.present(output_path),
        'MCM output already claimed or redirected')
    start = {'schema_version':1,'kind':'compact-required-graph-mcm','owner':owner.identity,
        'dictionary_receipt_sha256':dictionary.receipt_sha256,'dictionary_identity':d.identity,
        'graph_hash':key,'scope':expected,'rows':rows,'motifs':motifs,'cells':pairs,
        'policy_input':input_name,'policy_sha256':run.admission.inputs[input_name]['sha256'],
        'output_input':output_input,'output_policy_sha256':run.admission.inputs[output_input]['sha256'],
        'reserved_workflow_metadata_bytes':3*io.META_LIMIT*(len(owner.required)-1),
        'reserved_workflow_output_bytes':output_reserved,'sources':sources,'representation_admitted':False,'resumable':False}
    io._json(start); return graph,kernel,policy,start


class Produced:
    def __init__(self,dictionary,graph,stage,matrix,policy,start,record,root,inode,reference):
        self._dictionary = self._authority = dictionary; self._graph = self._graph_authority = graph
        self._stage = stage; self._matrix = matrix; self._policy = freeze(policy)
        self._start = freeze(start); self._record = freeze(record); self._directory = root
        self._inode = inode; self._reference = reference; self._pin = cache_key(self._configuration())

    matrix = property(lambda self:self._matrix)
    record = property(lambda self:self._record)
    directory = property(lambda self:self._directory)
    receipt_sha256 = property(lambda self:self._reference)

    def _configuration(self):
        return {'policy':thaw(self._policy),'start':thaw(self._start),'record':thaw(self.record),
            'directory':str(self.directory),'inode':self._inode,'reference':self._reference}

    def _integrity(self):
        require(self._dictionary is self._authority and self._graph is self._graph_authority
            and cache_key(self._configuration()) == self._pin,'compact MCM view changed')

    def lease(self):
        self._integrity(); self._dictionary.lease(); self._integrity()

    def _numeric(self):
        require(_matrix(self.matrix,self.record['rows'],self.record['motifs']) == self.record['matrix_sha256'],
            'compact MCM matrix changed')

    def _evidence(self):
        self._integrity(); owner = self._dictionary._proof.owner; stage = self._stage
        require(stage.owner is owner and owner.stages.get('mcm-'+self.record['graph_hash']) is stage
            and stage.closed and stage.reference == self.record['stage_sha256'], 'completed MCM stage differs')
        stage.integrity(); info = stage.root.lstat()
        require((info.st_dev,info.st_ino) == tuple(self.record['stage_inode']) == stage.inode,'MCM stage inode changed')
        names = {'intent.json','matching','checkpoints','stream','stage-complete.json'}
        compact_owner.entries(stage.root,names,required=names); compact_owner.exact(stage.root,'intent.json',stage.intent)
        compact_owner._stage_content(stage)
        root,fd = io._open(self.directory)
        try:
            info = os.fstat(fd); require((info.st_dev,info.st_ino) == self._inode,'MCM producer directory changed')
            names = {'start.json','complete.json'}; compact_owner.entries(root,names,required=names)
            require(io._read(fd,'start.json',io.META_LIMIT) == io._json(thaw(self._start)), 'MCM producer start changed')
            raw = io._read(fd,'complete.json',io.META_LIMIT)
            require(io._hash(raw) == self._reference and raw == io._json(thaw(self.record)), 'MCM producer receipt changed')
            io._root(root,fd)
        finally: io._cleanup((lambda: os.close(fd),))

    def _check(self):
        self.lease(); self._dictionary.check(); _sources(self._dictionary); self._numeric(); self._evidence()
        owner = self._dictionary._proof.owner; ticket = self.record['output']
        with publication._open_verified(owner,self._stage,output_input=self.record['output_input'],
                expected_scope=thaw(self.record['scope']),receipt_sha256=ticket['receipt_sha256']) as saved:
            require(saved.shape == self.matrix.shape and saved.dtype == self.matrix.dtype, 'saved MCM matrix dimensions differ')
            a = memoryview(saved).cast('B'); b = memoryview(self.matrix).cast('B')
            for offset in range(0,len(a),262144):
                require(a[offset:offset+262144] == b[offset:offset+262144],'saved MCM matrix bytes differ')
            del a,b
        self.lease(); _original(self._dictionary,self._graph,self.record['graph_hash']); self._numeric(); self._evidence()
        # Rejoin wrapper/output after the last external lease as well.
        args = self.record['output_args']; expected = self.record['output_proof']
        publication._verify(Path(ticket['directory']),thaw(args)|{'stage_root':self._stage.root},
            thaw(expected),lambda:None,ticket['receipt_sha256'])

    def check(self):
        owner = self._dictionary._proof.owner
        require(owner._transition.acquire(blocking=False),'concurrent MCM check')
        try: self._check()
        finally: owner._transition.release()


def produce(dictionary, *, graph_hash, input_name, output_input):
    require(type(dictionary) is compact_dictionary.Produced,'actual compact Produced dictionary required')
    owner = dictionary._proof.owner
    with compact_owner._held(owner) as held:
        return _produce_locked(dictionary,graph_hash=graph_hash,input_name=input_name,output_input=output_input,held=held)


def _produce_locked(dictionary, *, graph_hash, input_name, output_input, held):
    owner = dictionary._proof.owner; held.check(owner)
    fd = None; stream = log = None; claimed = False; inode = None
    try:
        graph,kernel,policy,start = _prepare(dictionary,graph_hash,input_name,output_input)
        root = directory(dictionary,graph_hash)
        require(root.is_absolute() and root.resolve() == root and not compact_owner.present(root),
            'MCM producer namespace already claimed or redirected')
        dictionary.lease(); _original(dictionary,graph,graph_hash); durable_mkdir(root.parent)
        require(root.resolve() == root,'MCM producer parent redirected'); dictionary.lease()
        root.mkdir(); claimed = True
        parent,parent_fd = io._open(root.parent)
        try: os.fsync(parent_fd); io._root(parent,parent_fd)
        finally: io._cleanup((lambda: os.close(parent_fd),))
        root,fd = io._open(root); info = os.fstat(fd); inode = (info.st_dev,info.st_ino)
        require(info.st_dev == owner.root.stat().st_dev,'MCM producer device differs')
        start_sha = io._write(fd,'start.json',io._json(start))
        from . import stage_retention
        selection=(stage_retention.mcm_selection(graph,dictionary.dictionary) if 'restart_retention' in owner.policy else None)
        scope = start['scope']; stage = owner._begin('mcm-'+graph_hash,scope['workflow'],start['cells'],None,
            retention_selection=selection)
        stage_inode = list(stage.inode)
        def lease():
            stage.lease(); dictionary.lease(); io._root(root,fd)
            require(io._read(fd,'start.json',io.META_LIMIT) == io._json(start),'MCM producer start changed')
        p = thaw(owner.policy)
        def compute(event_log, live):
            nonlocal log,stream
            log=event_log
            matcher = compact_matcher.CompactMatcher(log,config=thaw(owner.matching),context=thaw(owner.bound.context),
                policy=p['pair'],workload_sha256=scope['workflow'],schedule=p['schedule'],lease=live,
                retention=stage_retention.options(stage))
            stream = MCMScoreStream(stage.root/'stream',graph=graph,dictionary=dictionary.dictionary,
                matching_config=thaw(owner.matching),workflow=owner.bound.record['workflow_identity'],backend=BACKEND,
                owner=owner.identity,chunk_cells=p['score_chunk_cells'],compute=matcher,lease=live)
            require(stream.scope == scope,'MCM stream scientific scope differs')
            live(); _original(dictionary,graph,graph_hash)
            actual = kernel.mcm(graph,dictionary.dictionary,thaw(owner.matching),workflow=owner.bound.record['workflow_identity'],
                backend=BACKEND,max_entries=policy['max_entries'],score_pair=stream,policy=policy['numeric'],lease=live)
            numeric_pin=_matrix(actual['mcm'],start['rows'],start['motifs'])
            if matcher.retention is not None:stage_retention._bind(stage,matcher.retention,held)
            return actual,stream.finish()['terminal_sha256'],numeric_pin
        ledger=getattr(owner,'_archive_operations',None)
        if ledger is None:
            log = compact_pair_log.PairLog(stage.root/'matching',owner=owner.identity,scope=thaw(stage.scope),
                limits=p['log'],max_iterations=owner.matching['max_iterations'],lease=lease)
            actual,stream_terminal,numeric_pin=compute(log,lease)
        else:
            from . import archive_owner_writer
            (actual,stream_terminal,numeric_pin),writer_receipt=archive_owner_writer._run_locked(ledger,stage,compute,
                held=held,science_lease=lease)
        matrix = actual['mcm']; pin = _matrix(matrix,start['rows'],start['motifs'])
        require(pin==numeric_pin,'MCM matrix changed during stream/writer completion')
        require(actual['workload_sha256'] == scope['workflow'] and actual['completed_rows'] == start['rows']
            and actual['completed_cells'] == stream.cells == log.state['completed_pairs'] == start['cells']
            and actual['output_bytes'] == 4*start['cells'],'MCM completed denominator differs')
        if ledger is None:
            log_terminal = log.finish()
            stage_ref = owner._finish_stage(stage,log_terminal_sha256=log_terminal,stream_terminal_sha256=stream_terminal)
        else:
            from . import archive_owner_stage
            stage_ref=archive_owner_stage._execute_locked(ledger,stage,stream_terminal_sha256=stream_terminal,
                publish=True,held=held,science_lease=lease)
        dictionary.check(); dictionary.lease(); _original(dictionary,graph,graph_hash)
        require(_matrix(matrix,start['rows'],start['motifs']) == pin,'MCM matrix changed before publication')
        ticket = publication._publish(owner,stage,output_input=output_input,expected_scope=scope)
        attempt,args,output_proof,output_lease = publication._prepare(owner,stage,output_input,scope)
        require(str(attempt) == ticket['directory'],'MCM output directory differs')
        record = start | {'start_sha256':start_sha,'stage_sha256':stage_ref,'stage_inode':stage_inode,
            'matrix_sha256':pin,'completed_cells':start['cells'],'completed_rows':start['rows'],
            'output':ticket,'output_args':args|{'stage_root':str(args['stage_root'])},'output_proof':output_proof}
        reference = io._write(fd,'complete.json',io._json(record))
        result = Produced(dictionary,graph,stage,matrix,policy,start,record,root,inode,reference)
        result._check(); return result
    except BaseException as primary:
        cleanup = []
        if claimed:
            try:
                if stream is not None and not stream.closed:
                    try: stream.close()
                    except BaseException as failure: cleanup.append(failure)
                if log is not None and not log.closed:
                    try: log.fail('MCM producer failed')
                    except BaseException as failure:
                        if isinstance(failure, io.CleanupFailure): cleanup.append(failure)
                        primary.add_note('Failed MCM log terminal: '+repr(failure))
                        try: log.close()
                        except BaseException as failure: cleanup.append(failure)
            finally:
                owner.poisoned = True
                if fd is not None:
                    try: io._write(fd,'failed.json',io._json({'schema_version':1,'status':'failed','owner':owner.identity}))
                    except (OSError,ValueError) as failure: primary.add_note('Failed MCM marker: '+repr(failure))
            if cleanup:
                fatal = compact_matcher.CleanupFailure('MCM producer cleanup unresolved; worker must stop')
                for failure in cleanup: fatal.add_note(repr(failure))
                raise fatal from primary
        raise
    finally:
        primary = sys.exception()
        if fd is not None:
            try: io._cleanup((lambda: os.close(fd),))
            except BaseException as cleanup:
                owner.poisoned = True
                # Never retry the ambiguous fd. A fresh descriptor may mark
                # only the original pinned attempt, retaining successful
                # outputs if cleanup failed after the return was prepared.
                try:
                    path, fresh = io._open(root)
                    try:
                        info = os.fstat(fresh)
                        require(inode == (info.st_dev,info.st_ino),'MCM failed attempt inode changed')
                        if not compact_owner.present(root/'failed.json'):
                            io._write(fresh,'failed.json',io._json({'schema_version':1,'status':'failed','owner':owner.identity}))
                        io._root(path,fresh)
                    finally: io._cleanup((lambda: os.close(fresh),))
                except BaseException as marker_error: cleanup.add_note('Failure marker: '+repr(marker_error))
                if primary is not None: raise cleanup from primary
                raise
