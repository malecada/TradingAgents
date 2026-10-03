"""Explicit fresh compact producer and current-run native training handoff.

Resident parents are retained. No cold reuse, numerical fallback, empirical
admission or whole-workflow resource sufficiency follows from this adapter.
"""
import json
import hashlib
from pathlib import Path

from . import matching_owner, compact_policy, compact_owner, compact_training
from . import compact_sampler, compact_samples, compact_sample_proof, compact_dictionary
from . import compact_mcm, compact_features, compact_graph_artifacts, compact_denominator
from . import compact_closure, compact_publication, compact_terminal, compact_native_features
from . import compact_cold_features
from .cache import cache_key
from .contracts import Fold, GraphSnapshot
from .neighborhoods import graph_hash
from .registered_features import representation_descriptor
from .provenance import canonical_bytes, file_hash, thaw
from ..lifecycle import ResearchRun, _immutable, _encode

BACKEND = compact_policy.BACKEND
ROOT = Path(__file__).resolve().parents[3]
ROUTES = ('pair_checkpoint_input','compact_policy_input','compact_training_input',
    'compact_sampler_input','compact_samples_input','compact_dictionary_input',
    'compact_mcm_input','compact_mcm_output_input','compact_feature_input',
    'compact_graph_output_input','compact_denominator_input','compact_closure_input',
    'compact_publication_input','compact_terminal_input','compact_native_features_input')
UNSUPPORTED = ('continuation_input','death_input','pair_journal_parent_input',
    'graph_residency_input','residency_input','sampling_input','matching_input','neighborhood_input')
NAMESPACES = ('onchain_representations','onchain_pair_workflows','onchain_compact_sampler',
    'onchain_compact_samples','onchain_compact_dictionary','onchain_compact_mcm','onchain_compact_outputs',
    'onchain_compact_graphs','onchain_compact_publications','onchain_compact_terminals')


class CompactProducerError(RuntimeError):
    """A claimed attempt failed; the enclosing job must stop without fallback."""


def require(value,message):
    if not value:raise ValueError(message)


def required_sources():
    return compact_native_features.required_sources() | compact_cold_features.required_sources() | {compact_sampler.CORE,
        compact_samples.READER,compact_dictionary.KERNEL,compact_mcm.KERNEL,
        compact_features.BOUNDARY,compact_denominator.VALIDATOR,
        str(Path(__file__).resolve().relative_to(ROOT))}


def selected(run,representation,job):
    """Check explicit selection, policy routes and fresh namespaces before loading."""
    require(isinstance(run,ResearchRun),'actual compact producer run required');run._active()
    require(type(job) is dict,'compact producer job must be an object')
    plan = json.loads(run.read_input(job['plan_input'])) if job.get('plan_input') else None
    item = plan.get('producers',{}).get(job.get('producer')) if isinstance(plan,dict) else None
    a = job.get('native_backend');b = item.get('native_backend') if isinstance(item,dict) else None
    if a != BACKEND and b != BACKEND:return False
    require(a == b == BACKEND and job.get('operation') == 'produce',
        'compact producer selection differs or operation unsupported')
    require(type(plan.get('schema_version')) is int and plan['schema_version'] == 2,
        'compact producer requires version2 plan')
    execution = json.loads(run.read_input('execution_job'))
    require(execution['kind'] == 'fit' and canonical_bytes(execution['payload']['representation_jobs'].get(representation))
        == canonical_bytes(job),'compact selected execution job differs')
    require(all(item.get(k) is None and job.get(k) is None for k in UNSUPPORTED),
        'compact producer requires fresh resident inputs')
    require('pair_journal_parent_input' in item and 'pair_journal_parent_input' in job,
        'explicit fresh pair journal parent required')
    for key in ROUTES:
        name = job.get(key)
        require(type(name) is str and item.get(key) == name and name in run.admission.inputs,
            'compact required policy route differs: '+key)
        json.loads(run.read_input(name))
    compact_training._archive_extension(run, job, item)
    compact_training._retention_extension(run, job, item)
    for key in ('descriptor','binding_output','journal_output','graphs','compact_dictionary_count_policy'):
        require(key in job and canonical_bytes(item.get(key)) == canonical_bytes(job[key]),
            'compact producer '+key+' differs')
    require(job['compact_dictionary_count_policy'] == 'capacity-with-exact-completion-v1',
        'compact dictionary count policy differs')
    outputs = (job['binding_output'],job['journal_output'])
    require(all(type(n) is str and Path(n).name == n for n in outputs) and len(set(outputs)) == 2
        and set(outputs) <= set(run.admission.experiment['outputs']),'compact output names differ')
    require(job['descriptor']['arm'] == 'proposed','compact producer requires motif representation')
    identity = cache_key(job['descriptor'])
    for kind in NAMESPACES:
        namespace = run.admission.root/'research_artifacts'/kind/identity
        require(namespace.resolve() == namespace and not namespace.exists() and not namespace.is_symlink(),
            'compact fresh namespace already reserved or redirected: '+str(namespace))
    require(type(job.get('max_graph_payload_bytes')) is int and job['max_graph_payload_bytes'] > 0,
        'compact parent graph capacity required')
    for name in required_sources():
        expected = run.admission.experiment['source_files'].get(name)
        require(expected is not None and file_hash(ROOT/name) == expected
            and file_hash(run.admission.root/name) == expected,'compact source closure differs: '+name)
    compact_cold_features.selected(run,representation,job,item)
    return True


def produce(run,representation,job,graphs,examples,*,archive_transport=None):
    require(selected(run,representation,job),'compact production must be explicitly selected')
    graphs = tuple(graphs);d = job['descriptor'];fold = Fold(**d['fold'])
    require(graphs and all(type(g) is GraphSnapshot for g in graphs),'compact resident graph snapshots required')
    actual = representation_descriptor(graphs,examples,fold,'proposed',d['seed'],d['configs'])
    actual.update({k:d[k] for k in ('pair_execution','compact_execution','compact_training')})
    item=json.loads(run.read_input(job['plan_input']))['producers'][job['producer']]
    extension=compact_training._archive_extension(run,job,item)
    actual.update(extension)
    actual.update(compact_training._retention_extension(run,job,item))
    require(bool(extension)==(archive_transport is not None),
        'explicit selected archive transport required; local route cannot accept one')
    require(canonical_bytes(actual) == canonical_bytes(d),'compact actual representation differs before claim')
    m = compact_native_features._api()
    m.minimum_capacity({graph_hash(g):g for g in graphs},d['required_graphs'],d['configs']['dictionary']['size'],
        m.policy(json.loads(run.read_input(job['compact_native_features_input']))))
    cold = compact_cold_features.selected(run,representation,job,item)
    handoff_started = False
    journal = owner = ledger = archive_lock = None
    try:
        journal,bound = matching_owner.open_first(run,representation=representation,plan_input=job['plan_input'],
            producer=job['producer'],policy_input=job['pair_checkpoint_input'])
        owner = compact_owner.attach(bound,policy_input=job['compact_policy_input'])
        if extension:
            from . import archive_owner_policy, archive_owner_operations
            archive_lock = owner._transition
            ledger = archive_owner_operations.attach(archive_owner_policy.select(owner,
                input_name=job['compact_archive_input'],transport=archive_transport))
        training = compact_training.admit(owner,input_name=job['compact_training_input'],graphs=graphs,
            examples=examples,fold=fold,seed=d['seed'],configs=d['configs'])
        denominator = compact_denominator.admit(training,input_name=job['compact_denominator_input'])
        draws = compact_sampler.produce(training,input_name=job['compact_sampler_input'])
        saved = compact_samples.publish(draws,input_name=job['compact_samples_input'])
        proof = compact_sample_proof.admit(saved)
        dictionary = compact_dictionary.produce(proof,input_name=job['compact_dictionary_input'])
        artifacts = []
        for h in d['required_graphs']:
            mcm = compact_mcm.produce(dictionary,graph_hash=h,input_name=job['compact_mcm_input'],
                output_input=job['compact_mcm_output_input'])
            features = compact_features.prepare(mcm,input_name=job['compact_feature_input'])
            artifacts.append(compact_graph_artifacts.publish(features,input_name=job['compact_graph_output_input']))
        closure = compact_closure.admit(dictionary,denominator,artifacts,input_name=job['compact_closure_input'])
        published = compact_publication.publish(closure,input_name=job['compact_publication_input'])
        if cold is not None:
            handoff_started = True
            prepared = compact_cold_features.prepare(published,terminal_input=job['compact_terminal_input'],
                input_name=job['compact_cold_handoff_input'])
            finalize(prepared)
            return prepared,None
        terminal = compact_terminal.finish(published,input_name=job['compact_terminal_input'])
        prepared = compact_native_features.prepare(terminal,input_name=job['compact_native_features_input'])
        finalize(prepared)
        return prepared,terminal
    except BaseException as error:
        if handoff_started:
            owner.poisoned = True
            if compact_cold_features.cold_files.fatal(error):raise
            raise CompactProducerError('claimed cold handoff failed; preserve evidence and stop enclosing job') from error
        cleanup = []
        if owner is not None:owner.poisoned = True
        if ledger is not None and not ledger._closed:
            try:_close_failed_archive(owner,ledger,archive_lock)
            except BaseException as failure:cleanup.append(failure)
        if journal is not None:
            if not journal.sealed:
                try:journal.seal('failed',reason=type(error).__name__+': '+str(error))
                except BaseException as failure:cleanup.append(failure)
            try:_immutable(journal.directory/'attempt-failed.json',{
                'reason':type(error).__name__+': '+str(error),
                'compact_terminal_present':(journal.directory/'complete.json').exists(),
                'cleanup_errors':[str(e) for e in cleanup]})
            except BaseException as failure:cleanup.append(failure)
        for failure in cleanup:error.add_note('compact failure cleanup: '+repr(failure))
        if not isinstance(error,Exception):raise
        for failure in cleanup:
            if not isinstance(failure,Exception):raise failure from error
        raise CompactProducerError('compact producer attempt failed; preserve partial evidence and stop enclosing job'
            + ('; cleanup failed' if cleanup else '')) from error



def _close_failed_archive(owner,ledger,lock):
    """Revoke and close only the original ledger under its captured transition."""
    from . import archive_owner_operations
    require(type(ledger) is archive_owner_operations.Ledger
        and ledger.owner is owner and ledger.selection._owner is owner
        and getattr(owner,'_archive_operations',None) is ledger
        and owner._transition is lock and ledger._transition is lock,
        'failed archive ledger authority changed')
    with compact_owner._held(owner) as held:
        held.check(owner)
        require(held.lock is lock,'failed archive captured transition changed')
        if ledger._closed:return
        # Revocation is safe once identity is established. Replaced evidence
        # cannot authorize a physical write, but must not retain live authority.
        ledger._poisoned = True
        ledger._evidence()
        held.check(owner)
        compact_owner.io._cleanup((ledger._close,))


def finalize(prepared):
    """Full evidence rejoin before outer acceptance, including after all fits."""
    if type(prepared.features) is compact_cold_features._Features:
        try:return compact_cold_features.finalize(prepared)
        except BaseException as error:
            if compact_cold_features.cold_files.fatal(error):raise
            raise CompactProducerError('cold finalization failed; preserve evidence and stop enclosing job') from error
    require(type(prepared.features) is compact_native_features._Features,'actual compact native features required')
    terminal = prepared.features._terminal
    terminal.check()
    bound = terminal._owner.bound;run = bound._run
    selected = json.loads(run.read_input('execution_job'))['payload']['representation_jobs'][bound.record['representation']]
    expected = terminal.record['outputs'][selected['binding_output']]
    require(hashlib.sha256(_encode(thaw(prepared.binding))).hexdigest() == expected,
        'compact final prepared binding differs')
    terminal.check()
