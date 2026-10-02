"""Registered resident training population for the fresh compact producer.

This admits graph/example/configuration joins, not sampled neighborhoods or a
fitted dictionary. No sampling, pair allocation, output publication or empirical
release occurs here. The bounded sampler must subsequently preserve each draw
and prove its publication. Mapped graph populations need a separate admission.

Full checks rehash immutable resident inputs at boundaries. Inner leases check
the actual current owner and pinned route views under that frozen-input contract;
they deliberately do not hash every graph on each draw/comparison. Memory, disk
and runtime enforcement remain the outer registered guard's responsibility.
"""
from dataclasses import asdict
from datetime import timedelta

from . import compact_owner, compact_policy, matching_pair, matching_owner, score_batches as io
from .cache import cache_key
from .calendar import expected_week, stamp
from .contracts import GraphSnapshot, Fold
from .dataset import ExampleManifest
from .neighborhoods import graph_hash
from .provenance import canonical_bytes, digest, freeze, thaw, utc
from .registered_features import representation_descriptor

require = io._require


def _archive_extension(run, selected, item):
    """Reconstruct optional storage identity from its exact registered input."""
    from . import archive_owner_policy
    name=selected.get('compact_archive_input')
    extensions=[value['descriptor'].get('compact_archive_execution') for value in (selected,item)]
    if name is None and item.get('compact_archive_input') is None and extensions==[None,None]:
        return {}
    require(type(name) is str and item.get('compact_archive_input')==name and name in run.admission.inputs,
        'explicit archive producer policy route differs')
    expected={'backend':archive_owner_policy.BACKEND,'policy_sha256':run.admission.inputs[name]['sha256']}
    require(all(canonical_bytes(value)==canonical_bytes(expected) for value in extensions),
        'archive producer descriptor policy hash differs')
    run.read_input(name)
    return {'compact_archive_execution':expected}


def _metadata(owner, input_name):
    owner.boundary(); run = owner.bound._run; record = owner.bound.record
    snapshots = {}
    def read(name):
        # Full source/input checks bracket the boundary. Do not repeat the full
        # source checkout scan separately for every small graph manifest.
        require(type(name) is str and name in run.admission.inputs, 'registered training input required')
        owner.lease(); info = run.admission.inputs[name]
        return matching_owner.ancestry._read(run.admission.root, run.admission.root / info['path'],
            snapshots, expected=info['sha256'])[0]
    selected = read('execution_job')['payload']['representation_jobs'][record['representation']]
    plan = read(selected['plan_input'])
    require(type(plan.get('schema_version')) is int and plan['schema_version'] == 2,
            'compact training requires version2 producer plan')
    item = plan['producers'][record['producer']]
    require(type(input_name) is str and input_name in run.admission.inputs
        and selected.get('compact_training_input') == item.get('compact_training_input') == input_name
        and selected.get('native_backend') == item.get('native_backend') == compact_policy.BACKEND,
        'explicit compact training selection differs')
    descriptor = selected['descriptor']
    require(canonical_bytes(descriptor) == canonical_bytes(item['descriptor'])
        and cache_key(descriptor) == record['workflow_identity'], 'compact training descriptor differs')
    reference = {'input': input_name, 'sha256': run.admission.inputs[input_name]['sha256']}
    require(descriptor.get('compact_training') == reference, 'training policy descriptor differs')
    control = read(input_name)
    require(set(control) == {'schema_version', 'example_manifest_sha256'}
        and type(control['schema_version']) is int and control['schema_version'] == 1,
        'compact training control schema')
    io._identity(control['example_manifest_sha256'])
    refs = item.get('graphs')
    require(type(refs) is dict and canonical_bytes(refs) == canonical_bytes(selected.get('graphs'))
        and set(refs) == set(descriptor['graph_population']), 'training graph manifest population differs')
    for h, ref in refs.items():
        require(type(ref) is dict and set(ref) == {'input'} and type(ref['input']) is str
            and ref['input'] in run.admission.inputs, 'exact registered graph input required')
        require(read(ref['input']).get('graph_hash') == h,
                'training registered graph manifest differs')
    expected_extensions = {
        'pair_execution': {'backend': matching_pair.BACKEND, 'policy_sha256': record['policy_sha256']},
        'compact_execution': {'backend': compact_policy.BACKEND,
            'policy_sha256': run.admission.inputs[selected['compact_policy_input']]['sha256']},
        'compact_training': reference}
    expected_extensions.update(_archive_extension(run, selected, item))
    return descriptor, control, expected_extensions


def _science(graphs, examples, fold, seed, configs, descriptor, control, extensions):
    require(type(seed) is int and seed >= 0 and type(fold) is Fold
        and type(examples) is ExampleManifest and examples.fold_hash == fold.member_hash,
        'actual training seed/example/fold contract required')
    require(utc(fold.train_start) < utc(fold.train_end) <= utc(fold.test_start) < utc(fold.test_end),
            'training/test fold intervals overlap or differ')
    actual_examples = {**vars(examples), 'train': [asdict(x) for x in examples.train],
        'test': [asdict(x) for x in examples.test]}
    require(digest(canonical_bytes(actual_examples)) == control['example_manifest_sha256'],
            'actual training example population differs')
    require(examples.train_hash == digest(canonical_bytes([asdict(x) for x in examples.train]))
        and examples.test_mask_hash == digest(canonical_bytes([x.decision_at for x in examples.test])),
        'actual example membership hashes differ')
    graphs = tuple(graphs)
    require(graphs and all(type(g) is GraphSnapshot for g in graphs),
            'resident graph snapshots required; mapped admission is separate')
    actual = representation_descriptor(graphs, examples, fold, 'proposed', seed, configs) | extensions
    require(canonical_bytes(actual) == canonical_bytes(descriptor), 'actual compact training descriptor differs')
    by_hash = {graph_hash(g): g for g in graphs}
    require(len({g.asset for g in graphs}) == 1 and len({utc(g.start_utc) for g in graphs}) == len(graphs),
            'mixed training asset or duplicate weekly graph')
    require(all(set(g.source_hashes) <= set(examples.source_hashes) for g in graphs),
            'unbound actual graph source')
    for partition, rows in (('train', examples.train), ('test', examples.test)):
        require(bool(rows), 'empty declared example partition')
        previous = None
        for row in rows:
            decision = utc(row.decision_at)
            require(previous is None or previous < decision, 'example decision order/uniqueness differs')
            previous = decision
            require(utc(row.max_input_available_at) <= decision, 'future example input')
            require(utc(row.label_start) == decision < utc(row.label_end), 'example label clocks differ')
            if partition == 'train':
                require(utc(fold.train_start) <= decision < utc(fold.train_end)
                    and utc(row.label_end) < utc(fold.test_start), 'training fold clocks differ')
            else:
                require(utc(fold.test_start) <= decision < utc(fold.test_end)
                    and utc(row.label_end) <= utc(fold.test_end), 'test fold clocks differ')
            require(len(row.graph_hashes) == len(row.graph_available_at) == len(row.input_dates)
                == len(row.input_prices) and bool(row.graph_hashes), 'example input dimensions differ')
            previous_step = None
            for h, timestamp, day in zip(row.graph_hashes, row.graph_available_at, row.input_dates, strict=True):
                step = utc(day + 'T00:00:00Z') + timedelta(days=1)
                require((previous_step is None or previous_step < step) and step <= decision,
                        'future or unordered price input')
                previous_step = step
                require(h in by_hash and utc(by_hash[h].available_at) == utc(timestamp)
                    and utc(timestamp) <= step
                    and utc(by_hash[h].start_utc) == utc(expected_week(stamp(step))),
                    'actual graph step clock lineage differs')
    training = tuple(sorted((g for g in graphs if utc(g.start_utc) >= utc(fold.train_start)
        and utc(g.available_at) < utc(fold.train_end)), key=lambda g: (g.start_utc, g.asset, graph_hash(g))))
    require(training, 'empty admitted training graph population')
    settings = dict(configs['dictionary']) | {'train_start': fold.train_start, 'train_end': fold.train_end}
    compact_policy.dictionary_capacity(**{k: settings[k] for k in
        ('sample_count', 'size', 'partition_threshold', 'partition_size')})
    require(settings['sample_count'] <= sum(len(g.node_ids) for g in training),
            'insufficient admitted training centers')
    return graphs, training, settings


class Training:
    def __init__(self, owner, input_name, graphs, training, examples, fold, seed, configs, descriptor, control, settings):
        self._owner = self._authority = owner
        self._graphs = graphs; self._training = training
        self._graph_objects = graphs; self._training_objects = training
        self._examples = examples; self._fold = fold; self._configs = freeze(configs)
        self._input = input_name; self._seed = seed; self._settings = freeze(settings)
        self._descriptor = freeze(descriptor); self._control = freeze(control)
        self._record = freeze({'schema_version': 1, 'owner': owner.identity,
            'binding_sha256': cache_key(thaw(owner.bound.record)), 'workflow': owner.bound.record['workflow_identity'],
            'training_input': input_name, 'training_input_sha256': descriptor['compact_training']['sha256'],
            'example_manifest_sha256': control['example_manifest_sha256'],
            'training_hashes': tuple(graph_hash(g) for g in training), 'settings_sha256': cache_key(settings),
            'seed': seed, 'sample_provenance_admitted': False})
        self._configuration_sha = cache_key(self._configuration())
        self.lease()

    owner = property(lambda self: self._owner)
    graphs = property(lambda self: self._graphs)
    training_graphs = property(lambda self: self._training)
    training_hashes = property(lambda self: tuple(self._record['training_hashes']))
    settings = property(lambda self: self._settings)
    seed = property(lambda self: self._seed)
    descriptor = property(lambda self: self._descriptor)
    record = property(lambda self: self._record)

    def _configuration(self):
        return {'input': self._input, 'seed': self._seed, 'configs': thaw(self._configs),
            'settings': thaw(self._settings), 'descriptor': thaw(self._descriptor),
            'control': thaw(self._control), 'record': thaw(self._record), 'fold': asdict(self._fold)}

    def _integrity(self):
        require(self._owner is self._authority and self._graphs is self._graph_objects
            and self._training is self._training_objects
            and cache_key(self._configuration()) == self._configuration_sha, 'compact training route changed')

    def lease(self):
        self._integrity()
        self._owner.lease()
        self._integrity()
        require(self._record['owner'] == self._owner.identity
            and self._record['binding_sha256'] == cache_key(thaw(self._owner.bound.record)),
            'compact training owner authority differs')

    def check(self):
        self.lease()
        descriptor, control, extensions = _metadata(self._owner, self._input)
        graphs, training, settings = _science(self._graphs, self._examples, self._fold, self._seed,
            thaw(self._configs), descriptor, control, extensions)
        require(tuple(map(graph_hash, training)) == self.training_hashes
            and canonical_bytes(settings) == canonical_bytes(thaw(self._settings)),
            'compact training inputs changed')
        self._owner.boundary(); self.lease()


def admit(owner, *, input_name, graphs, examples, fold, seed, configs):
    require(type(owner) is compact_owner.Owner, 'actual compact owner required')
    require(owner._transition.acquire(blocking=False), 'concurrent compact training admission')
    try:
        descriptor, control, extensions = _metadata(owner, input_name)
        require(not owner.stages and owner.active is None, 'training admission must precede matching stages')
        graphs, training, settings = _science(graphs, examples, fold, seed, configs, descriptor, control, extensions)
        route = Training(owner, input_name, graphs, training, examples, fold, seed, configs, descriptor, control, settings)
        owner.boundary(); route.lease()
        return route
    finally: owner._transition.release()
