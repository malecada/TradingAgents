"""Current-resident compact terminal handoff and registered representation outputs.

A distinct schema2 marker never impersonates old graph-event journals. Active
owner contracts stay closed. Receipts retain original resident producer objects;
lease verifies current authority/metadata, check also verifies original numeric
and archive content. Neither is a cold reader or empirical admission. All
source/guard/filesystem guarantees are sampled, not atomic external snapshots.
"""
import json
import os
from pathlib import Path
import sys

from .. import lifecycle
from . import compact_publication, compact_owner, compact_policy, compact_features
from . import compact_denominator, compact_mcm, compact_sampler, matching_owner, score_batches as io
from .cache import cache_key
from .provenance import canonical_bytes, durable_mkdir, freeze, thaw

require = io._require
FORMAT = 'compact-representation-v1'


def directory(published):
    owner = compact_publication._owner(published._closure); b = owner.bound.record
    return owner.bound._run.admission.root/'research_artifacts/onchain_compact_terminals'/b['workflow_identity']/b['experiment']


def _original(published,expected_stages):
    """Postseal-safe original receipt checks; no live producer lease or bypass."""
    closure = published._closure;closure._integrity()
    dictionary = closure._dictionary;owner = dictionary._proof.owner
    training = compact_mcm._training(dictionary)
    require(closure._denominator._training is training,'terminal denominator ancestry differs')
    required = tuple(training.descriptor['required_graphs'])
    graphs = closure._graphs
    require(sorted(p.record['graph_hash'] for p in graphs) == list(required)
        and all(p._features._mcm._dictionary is dictionary for p in graphs),'terminal graph population differs')
    require(tuple(closure._denominator.record['denominator']['required_graphs']) == required,
        'terminal calendar graph union differs')
    dictionary._proof._final();dictionary._numeric();dictionary._evidence()
    compact_denominator._original(training);closure._denominator._integrity()
    require(owner._verified_stages() == expected_stages,'terminal stage content differs')
    for p in graphs:
        f = p._features
        compact_features._original(f._mcm);f._numeric();p._evidence()
        require(f.record['graph_hash'] == f._mcm.record['graph_hash']
            and f.record['mcm_receipt_sha256'] == f._mcm.receipt_sha256
            and f.record['feature_hash'] == f._boundary_module.identity(f._mcm.matrix,f._mcm._graph.edge_index,f._chunk),
            'terminal original feature lineage differs')
    parent = graphs[0].directory.parent
    require(all(p.directory.parent == parent for p in graphs),'terminal graph parent differs')
    compact_owner.entries(parent,set(required),required=set(required))
    published._evidence()


class Receipt:
    __slots__ = ('_record','_live','_verify','_owner')
    def __init__(self,record,live,verify,owner):
        object.__setattr__(self,'_record',freeze(record));object.__setattr__(self,'_live',live)
        object.__setattr__(self,'_verify',verify);object.__setattr__(self,'_owner',owner)
    def __setattr__(self,name,value):raise AttributeError('compact terminal receipt is immutable')
    record = property(lambda self:self._record)
    def lease(self):
        """Authority/metadata only; does not certify numeric/archive content."""
        self._live()
    def check(self):
        require(self._owner._transition.acquire(blocking=False),'concurrent compact terminal check')
        try:self.lease();self._verify(full=True)
        finally:self._owner._transition.release()


def finish(published,*,input_name):
    require(type(published) is compact_publication.Published,'actual compact publication required')
    closure = published._closure;owner = compact_publication._owner(closure)
    require(owner._transition.acquire(blocking=False),'concurrent compact terminal handoff')
    claimed = False;root = None;inode = None;fd = None
    try:
        published._check();bound = owner.bound;run = bound._run;ad = run.admission
        selected = json.loads(run.read_input('execution_job'))['payload']['representation_jobs'][bound.record['representation']]
        item = json.loads(run.read_input(selected['plan_input']))['producers'][bound.record['producer']]
        require(type(input_name) is str and input_name in ad.inputs
            and item.get('compact_terminal_input') == selected.get('compact_terminal_input') == input_name,
            'selected compact terminal policy differs')
        policy = json.loads(run.read_input(input_name))
        require(type(policy) is dict and set(policy) == {'schema_version','max_metadata_bytes','max_attempt_bytes'}
            and type(policy['schema_version']) is int and policy['schema_version'] == 1
            and all(type(policy[k]) is int and 0 < policy[k] < 2**63 for k in ('max_metadata_bytes','max_attempt_bytes'))
            and policy['max_metadata_bytes'] <= 2*1024**2,'compact terminal policy differs')
        cap = policy['max_metadata_bytes'];reserve = 6*cap+io.META_LIMIT
        require(reserve <= policy['max_attempt_bytes'],'compact terminal output allowance exceeded')
        names = tuple(item.get(k) for k in ('binding_output','journal_output'))
        require(all(type(n) is str and n and Path(n).name == n and n in ad.experiment['outputs'] for n in names)
            and len(set(names)) == 2 and names == tuple(selected.get(k) for k in ('binding_output','journal_output')),
            'compact terminal registered output routes differ')
        root = directory(published);journal = owner.root.parent
        require(root.resolve() == root and not compact_owner.present(root),'compact terminal attempt already claimed or redirected')
        for name in names:
            require(not compact_owner.present(run.directory/'outputs'/name),'compact terminal output already claimed')
        journal_names = {'owner.json','start.json','claim.json','compact'}
        from . import archive_owner_seal
        archive_names,archive_pin=archive_owner_seal._journal_members(owner)
        archive_ledger=getattr(owner,'_archive_operations',None)
        journal_names |= archive_names
        compact_owner.entries(journal,journal_names,required=journal_names)
        jinfo = journal.lstat();journal_inode = (jinfo.st_dev,jinfo.st_ino)
        stages = owner._verified_stages();required = tuple(owner.required)
        stage_pins = {n:(s,s.reference,cache_key(thaw(s.contract)),s.reservation,s.inode) for n,s in owner.stages.items()}
        owner_done = {'schema_version':1,'owner':owner.identity,**stages,
            'reserved_logical_bytes':owner.reserved,'representation_admitted':False}
        owner_raw = compact_owner.body(owner_done);owner_sha = io._hash(owner_raw)
        publication_sha = io._hash(published._bodies['complete.json'])
        marker = {'schema_version':2,'format':FORMAT,'status':'complete','backend':compact_policy.BACKEND,
            'owner':thaw(bound.record),'compact_owner':{'path':str(owner.root/'complete.json'),'sha256':owner_sha},
            'publication':{'path':str(published.directory/'complete.json'),'sha256':publication_sha},
            'binding_sha256':published.record['binding_sha256'],'closure_sha256':published.record['closure_sha256'],
            'required_graphs':list(closure.record['binding']['feature_hashes'])}
        marker_raw = canonical_bytes(marker);marker_sha = io._hash(marker_raw)
        reference = {'schema_version':2,'format':FORMAT,'backend':compact_policy.BACKEND,
            'path':str((journal/'complete.json').relative_to(ad.root)),'sha256':marker_sha,
            'owner':thaw(bound.record),'workflow_identity':bound.record['workflow_identity']}
        outputs = {names[0]:thaw(closure.record['binding']),names[1]:reference}
        output_raw = {n:lifecycle._encode(v) for n,v in outputs.items()}
        start = {'schema_version':2,'format':FORMAT,'owner':owner.identity,'resumable':False,
            'input':input_name,'policy_sha256':ad.inputs[input_name]['sha256'],'reserved_encoded_bytes':reserve,
            'owner_terminal_sha256':owner_sha,'representation_sha256':marker_sha,
            'outputs':{n:io._hash(v) for n,v in output_raw.items()}}
        record = start | {'status':'complete','representation':reference,'publication':marker['publication'],
            'owner_terminal':marker['compact_owner'],'metadata_lease_content_verified':False,
            'resident_originals_retained':True,'empirical_admission_verified':False}
        start_raw = canonical_bytes(start);proof_raw = canonical_bytes(record)
        fail_raw = canonical_bytes({'schema_version':2,'status':'failed','owner':owner.identity,'resumable':False})
        require(max(map(len,(start_raw,proof_raw,fail_raw,marker_raw,*output_raw.values()))) <= cap,
            'compact terminal metadata allowance exceeded before claim')
        phase = {'owner':False,'representation':False,'outputs':set(),'proof':False}
        observed = dict(run._published_outputs)
        def sources():
            run._active();run._check_source();run._check_inputs()
            matching_owner._source(run,bound.record['numerical_source'])
            require(cache_key(matching_owner.inventory(ad.root,include_torch=True)) == bound.context['runtime_hash'],
                'terminal runtime differs')
            compact_features._sources(closure._graphs[0]._features._mcm)
            compact_sampler._sources(closure._denominator._training)
            compact_denominator._sources(closure._denominator._training)
        def verify(*,full=False):
            # No live owner/Binding/guard callback follows this verification.
            sources();owner.check_binding();run._active()
            require(getattr(owner,'_archive_operations',None) is archive_ledger
                and archive_owner_seal._journal_members(owner)==(archive_names,archive_pin)
                and (archive_ledger is None or archive_ledger._closed==phase['owner']),
                'terminal archive phase or original operations differ')
            require(owner.bound is bound and bound._run is run and not owner.poisoned
                and owner.closed == phase['owner'] and owner.closing == phase['owner']
                and owner.active is None and tuple(owner.required) == required
                and set(owner.stages) == set(stage_pins),'terminal owner state differs')
            require(cache_key(owner.configuration()) == owner.configuration_sha256
                and owner.reserved == owner._reserved == owner_done['reserved_logical_bytes'],
                'terminal owner configuration/reservation differs')
            for n,(s,ref,contract,reservation,identity) in stage_pins.items():
                require(owner.stages[n] is s and s.owner is owner and s.closed and s.reference == ref
                    and cache_key(thaw(s.contract)) == contract and s.reservation == reservation and s.inode == identity,
                    'terminal stage authority differs')
                s.integrity();compact_owner.exact(s.root,'intent.json',s.intent)
            require(not any(compact_owner.present(run.directory/n) for n in ('complete.json','failed.json')),
                'terminal run no longer active')
            compact_owner.entries(journal.parent,{journal.name},required={journal.name})
            info = journal.lstat();require(journal.resolve() == journal and (info.st_dev,info.st_ino) == journal_inode,
                'terminal representation directory differs')
            compact_owner.entries(journal,journal_names|({'complete.json'} if phase['representation'] else set()),
                required=journal_names|({'complete.json'} if phase['representation'] else set()))
            for path,sha in bound._snapshots.items():
                require(matching_owner.metadata(path,ad.root)[1] == sha,'terminal binding metadata changed')
            info = owner.root.lstat();require((info.st_dev,info.st_ino) == owner.inode,'terminal compact owner directory differs')
            expected = {'owner.json',*required}|({'complete.json'} if phase['owner'] else set())
            compact_owner.entries(owner.root,expected,required=expected);compact_owner.exact(owner.root,'owner.json',owner.start)
            if phase['owner']:compact_owner.exact(owner.root,'complete.json',owner_raw)
            if phase['representation']:_exact(journal,'complete.json',marker_raw,cap)
            published._evidence()
            if claimed:
                info = root.lstat();require((info.st_dev,info.st_ino) == inode,'terminal attempt directory differs')
                expected = {'start.json'}|({'complete.json'} if phase['proof'] else set())
                compact_owner.entries(root,expected,required=expected);_exact(root,'start.json',start_raw,cap)
                if phase['proof']:_exact(root,'complete.json',proof_raw,cap)
            with lifecycle._lock(ad.root):
                run._active();registry = dict(run._published_outputs)
                require(set(registry) <= set(ad.experiment['outputs']) and all(registry.get(n) == sha for n,sha in observed.items()),
                    'terminal registered outputs changed or disappeared')
                for n in names:
                    require((n in registry) == (n in phase['outputs']),'terminal output phase differs')
                    if n in registry:require(registry[n] == io._hash(output_raw[n]),'terminal original output registry changed')
                compact_owner.entries(run.directory/'outputs',set(registry),required=set(registry))
                for n,sha in registry.items():
                    require(type(n) is str and Path(n).name == n,'terminal output name differs')
                    require(_hash_file(run.directory/'outputs',n,cap) == sha,'terminal output bytes changed')
                observed.update(registry)
            if full:_original(published,stages)
        def live():
            run._active();bound._guard();verify()
        published.lease();compact_publication._final(closure);published._evidence()
        durable_mkdir(root.parent);require(root.resolve() == root,'terminal attempt parent redirected')
        published.lease();compact_publication._final(closure);published._evidence()
        root.mkdir();claimed = True;info = root.lstat();inode = (info.st_dev,info.st_ino)
        parent,pfd = io._open(root.parent)
        try:os.fsync(pfd);io._root(parent,pfd)
        finally:io._cleanup((lambda:os.close(pfd),))
        root,fd = io._open(root);require(os.fstat(fd).st_dev == ad.root.stat().st_dev,'terminal attempt device differs')
        io._write(fd,'start.json',start_raw)
        # Final active contract; subsequent checks use the separate phase contract.
        published.lease();compact_publication._final(closure);verify(full=True)
        actual = owner._finish();phase['owner'] = True
        require(actual == owner_sha,'compact owner seal differs');live();verify(full=True)
        _write(journal,'complete.json',marker_raw);phase['representation'] = True;live()
        for n,v in outputs.items():
            live();run.write_json(n,v);phase['outputs'].add(n);live()
        io._write(fd,'complete.json',proof_raw);phase['proof'] = True
        result = Receipt(record,live,verify,owner)
        result.lease();verify(full=True);return result
    except BaseException as primary:
        if claimed:
            try:_failed(owner,root,inode)
            except BaseException as failure:
                primary.add_note('Compact terminal failure marker: '+repr(failure))
                if isinstance(failure,io.CleanupFailure):raise failure from primary
        raise
    finally:
        primary = sys.exception()
        try:
            if fd is not None:
                try:io._cleanup((lambda:os.close(fd),))
                except BaseException as cleanup:
                    owner.poisoned = True
                    try:_failed(owner,root,inode)
                    except BaseException as error:cleanup.add_note('Compact terminal failure marker: '+repr(error))
                    if primary is not None:raise cleanup from primary
                    raise
        finally:owner._transition.release()


def _exact(root,name,expected,cap):
    path,fd = io._open(root)
    try:require(io._read(fd,name,cap) == expected,'terminal saved metadata changed');io._root(path,fd)
    finally:io._cleanup((lambda:os.close(fd),))


def _hash_file(root,name,cap):
    path,fd = io._open(root)
    try:result = io._hash(io._read(fd,name,cap));io._root(path,fd);return result
    finally:io._cleanup((lambda:os.close(fd),))


def _write(root,name,raw):
    path,fd = io._open(root)
    try:io._write(fd,name,raw);io._root(path,fd)
    finally:io._cleanup((lambda:os.close(fd),))


def _failed(owner,root,inode):
    owner.poisoned = True
    path,fd = io._open(root)
    try:
        info = os.fstat(fd);require((info.st_dev,info.st_ino) == inode,'terminal failed attempt directory differs')
        if not compact_owner.present(path/'failed.json'):
            io._write(fd,'failed.json',canonical_bytes({'schema_version':2,'status':'failed',
                'owner':owner.identity,'resumable':False}))
        io._root(path,fd)
    finally:io._cleanup((lambda:os.close(fd),))
