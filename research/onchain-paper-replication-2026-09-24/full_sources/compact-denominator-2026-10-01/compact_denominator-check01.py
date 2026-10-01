"""Complete registered daily denominator for actual compact Training.

Metadata admission preserves every included/excluded date and required graph
union. It does not independently revalidate prices or price-based exclusions,
materialize graph features, close a representation or admit empirical fitting.
"""
from dataclasses import asdict
import importlib.util
import json

from . import compact_training, calendar, dataset
from .cache import cache_key
from .neighborhoods import graph_hash
from .provenance import canonical_bytes, digest, file_hash, freeze, thaw
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = 'research/onchain-paper-replication-2026-09-24/full_sources/representation-denominator-2026-10-01/denominator.py'
require = compact_training.require


def _validator():
    spec = importlib.util.spec_from_file_location('compact_calendar_denominator',ROOT/VALIDATOR)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def _sources(training):
    ad = training.owner.bound._run.admission; sha = ad.experiment['source_files'].get(VALIDATOR)
    require(sha is not None and file_hash(ROOT/VALIDATOR) == sha and file_hash(ad.root/VALIDATOR) == sha,
        'compact denominator validator source differs')
    return {VALIDATOR:sha}


def _manifest(examples):
    return digest(canonical_bytes({**vars(examples),'train':[asdict(x) for x in examples.train],
        'test':[asdict(x) for x in examples.test]}))


def _original(training):
    training._integrity()
    require(_manifest(training._examples) == training.record['example_manifest_sha256'],
        'compact denominator original examples changed')
    require(canonical_bytes(asdict(training._fold)) == canonical_bytes(thaw(training.descriptor['fold'])),
        'compact denominator original fold changed')
    require(sorted(graph_hash(g) for g in training.graphs) == list(training.descriptor['graph_population']),
        'compact denominator original graphs changed')


class Receipt:
    __slots__ = ('_training','_record','_pin')
    def __init__(self,training,record):
        object.__setattr__(self,'_training',training)
        object.__setattr__(self,'_record',freeze(record))
        object.__setattr__(self,'_pin',cache_key(record))
    def __setattr__(self,name,value): raise AttributeError('compact denominator receipt is immutable')
    record = property(lambda self:self._record)
    def _integrity(self):
        require(cache_key(thaw(self.record)) == self._pin,'compact denominator receipt changed')
        require(self.record['owner'] == self._training.owner.identity
            and self.record['descriptor_sha256'] == cache_key(thaw(self._training.descriptor)),
            'compact denominator owner/descriptor changed')
    def lease(self):
        self._integrity(); self._training.lease(); _original(self._training); self._integrity()
    def _check(self):
        self._training.check(); _sources(self._training); self.lease()
    def check(self):
        owner = self._training.owner
        require(owner._transition.acquire(blocking=False),'concurrent compact denominator check')
        try: self._check()
        finally: owner._transition.release()


def admit(training, *, input_name):
    require(type(training) is compact_training.Training,'actual compact Training required')
    owner = training.owner
    require(owner._transition.acquire(blocking=False),'concurrent compact denominator admission')
    try:
        training.check(); _original(training); sources = _sources(training)
        require(owner.bound._ancestry_arguments is None,'historical denominator requires separate admission')
        run = owner.bound._run; bound = owner.bound.record
        def read(name):
            require(type(name) is str and name in run.admission.inputs,'registered compact denominator input required')
            return json.loads(run.read_input(name))
        selected = read('execution_job')['payload']['representation_jobs'][bound['representation']]
        item = read(selected['plan_input'])['producers'][bound['producer']]
        require(item.get('compact_denominator_input') == selected.get('compact_denominator_input') == input_name,
            'selected compact denominator route differs')
        for value in (item,selected):
            require(canonical_bytes(value['descriptor']) == canonical_bytes(thaw(training.descriptor)),
                'registered compact denominator descriptor differs')
        policy = read(input_name)
        require(type(policy) is dict and set(policy) == {'schema_version','calendar_input','coverage_input','max_calendar_days'}
            and type(policy['schema_version']) is int and policy['schema_version'] == 1
            and type(policy['max_calendar_days']) is int and 0 < policy['max_calendar_days'] < 2**63,
            'compact denominator policy differs')
        config,coverage = read(policy['calendar_input']),read(policy['coverage_input'])
        require(type(config) is dict and type(coverage) is dict
            and type(config.get('lookback_days')) is int and config['lookback_days'] > 0
            and type(config.get('folds')) is list and bool(config['folds']), 'compact calendar configuration differs')
        matches = [fold for fold in calendar.build_folds(config,coverage) if fold.id == training._fold.id]
        require(len(matches) == 1 and canonical_bytes(asdict(matches[0])) == canonical_bytes(asdict(training._fold)),
            'registered compact fold/coverage differs')
        graphs = tuple(dataset.CalendarGraph(g.asset,g.start_utc,g.end_utc,g.available_at,g.source_hashes,graph_hash(g))
            for g in training.graphs)
        result = _validator().validate(graphs,training._examples,training._fold,lookback_days=config['lookback_days'],
            max_calendar_days=policy['max_calendar_days'],expected_manifest_sha256=training.record['example_manifest_sha256'],
            expected_population=thaw(training.descriptor['graph_population']),
            expected_required=thaw(training.descriptor['required_graphs']))
        def reference(name): return {'input':name,'sha256':run.admission.inputs[name]['sha256']}
        record = {'schema_version':1,'owner':owner.identity,'descriptor_sha256':cache_key(thaw(training.descriptor)),
            'policy':reference(input_name),'calendar':reference(policy['calendar_input']),
            'coverage':reference(policy['coverage_input']),'sources':sources,'denominator':result,
            'graph_completion_validated':False,'representation_admitted':False}
        receipt = Receipt(training,record); receipt.lease(); _sources(training)
        return receipt
    finally: owner._transition.release()
