"""Prospective registered resource caller; no standalone admission or launch.

Install into the admitted package and explicitly select real_pilot_input in the
existing compact_resource job. Genuine job.worker starts ResearchRun only after
its existing native guard. This module never creates a claim or substitutes an
Owner, dictionary, target, label, graph or scientific completion certificate.
"""
import hashlib
import json
from pathlib import Path
import time

KIND = 'real-data-import-training-pilot-v1'
FILE_MAX = 4 * 1024**2
GIB = 1024**3
KEYS = {'operation','plan_input','producer','pair_checkpoint_input','descriptor',
        'original_dictionary_input','compact_policy_input','native_backend',
        'original_dictionary_stage_input','compact_mcm_input','compact_mcm_output_input',
        'real_pilot_input'}


def require(value, message):
    if not value:
        raise ValueError(message)


def selected(job):
    jobs = job.get('payload', {}).get('representation_jobs', {})
    marked = [s for s in jobs.values() if type(s) is dict and 'real_pilot_input' in s]
    if not marked:
        return False
    require(len(jobs) == len(marked) == 1, 'pilot requires one explicit representation')
    require(type(marked[0]['real_pilot_input']) is str and marked[0]['real_pilot_input'], 'explicit pilot input required')
    return True


def validate_plan(p):
    fields = {'schema_version','kind','asset','seed','batch_size','lookback_days',
              'cell_id','graph_inputs','indices','decisions','graph_sequences',
              'population_plan_input','model_input','training_input','model_execution',
              'max_checkpoint_bytes','outputs'}
    require(type(p) is dict, 'pilot plan must be an object')
    full = type(p.get('schema_version')) is int and p['schema_version'] == 2
    archive='archive_inputs' in p
    if archive:
        refs=p['archive_inputs']
        require(full and type(refs) is dict and set(refs)=={'policy_input','transport_input'} and all(type(v) is str and v for v in refs.values()) and len(set(refs.values()))==2,'explicit schema2 archive input pair required')
    interval='imported_authority_lease_input' in p
    require(not interval or (full and type(p['imported_authority_lease_input']) is str and bool(p['imported_authority_lease_input'])),'explicit schema2 interval input required')
    partial = 'partial_progress' in p
    if partial:
        from .real_pilot_partial_progress import policy
        require(full, 'partial progress requires explicit schema2 plan')
        policy(p['partial_progress'])
    resource_subset = 'population_scope' in p
    require(not resource_subset or (full and p['population_scope'] == 'resource_pilot_subset'), 'explicit schema2 subset scope required')
    require(set(p) == fields | ({'resource_policy'} if full else set()) | ({'population_scope'} if resource_subset else set()) | ({'imported_authority_lease_input'} if interval else set()) | ({'archive_inputs'} if archive else set()) | ({'partial_progress'} if partial else set()), 'pilot plan fields differ')
    require(type(p['schema_version']) is int and p['schema_version'] in (1, 2) and p['kind'] == KIND
            and p['asset'] == 'ETH' and type(p['seed']) is int and p['seed'] == 11
            and type(p['batch_size']) is int and p['batch_size'] == 16
            and type(p['lookback_days']) is int and p['lookback_days'] == 28, 'fixed real ETH pilot differs')
    indices = p['indices']
    if resource_subset:
        require(indices is None, 'resource indices must be derived by the registered worker')
    else:
        require(type(indices) is list and len(indices) == 16 and all(type(i) is int and i >= 0 for i in indices)
                and indices == list(range(indices[0], indices[0]+16)), 'consecutive eligible batch16 required')
    mapping = p['graph_inputs']
    require(type(mapping) is dict and len(mapping) == 7 and len(set(mapping.values())) == 7
            and all(type(h) is str and len(h) == 64 and all(c in '0123456789abcdef' for c in h)
                    and type(role) is str and role for h, role in mapping.items()), 'seven distinct full graph inputs required')
    seq = p['graph_sequences']
    require(type(seq) is list and len(seq) == 16 and all(type(row) is list and len(row) == 28 for row in seq)
            and all(type(h) is str for row in seq for h in row)
            and {h for row in seq for h in row} == set(mapping), 'exact batch graph membership differs')
    dates = p['decisions']
    require(type(dates) is list and len(dates) == 16 and all(type(d) is str and d for d in dates)
            and dates == sorted(set(dates)), 'ordered decision membership required')
    require(all(type(p[k]) is str and p[k] for k in ('cell_id','population_plan_input','model_input','training_input')), 'explicit plan roles required')
    require(p['model_execution'] is None or type(p['model_execution']) is dict, 'explicit model execution policy required')
    require(type(p['max_checkpoint_bytes']) is int and 0 < p['max_checkpoint_bytes'] <= FILE_MAX, 'checkpoint cap differs')
    outputs = p['outputs']
    require(type(outputs) is dict and set(outputs) == {'summary','ledger','binding','journal'}
            and all(type(n) is str and n and not Path(n).is_absolute() and '..' not in Path(n).parts for n in outputs.values())
            and len(set(outputs.values())) == 4, 'four distinct registered output names required')
    if full:_finite_resources(p['resource_policy'])
    return p


def schema(job):
    from .resource_binding import validate_job
    validate_job(job)
    require(selected(job), 'explicit pilot selection absent')
    _, s = next(iter(job['payload']['representation_jobs'].items()))
    archive_keys={'compact_archive_input','compact_archive_transport_input'}
    keys=KEYS | (archive_keys if archive_keys & set(s) else set())
    require(type(s) is dict and set(s) == keys and s['operation'] == 'produce'
            and all(type(s[k]) is str and s[k] for k in keys-{'descriptor','operation'}), 'pilot producer selection differs')
    d = s['descriptor']
    require(type(d) is dict and d.get('arm') == 'proposed' and d.get('dictionary_origin') == 'imported-original-v1'
            and 'resource_fixture' not in d, 'original real proposed descriptor required')
    _finite_resources(job['resources'])


def _tiny_resources(p):
    require('physical_policy' not in p and 'storage_budget' in p, 'whole workspace storage guard required')
    require('schema_version' not in p['storage_budget'],'tiny route cannot select writable union')
    require(type(p.get('wall_seconds')) is int and 0 < p['wall_seconds'] <= 1800
            and type(p.get('memory_max_bytes')) is int and 0 < p['memory_max_bytes'] <= 3*GIB, 'original native envelope exceeded')
    require(p.get('native_unit_limits') == {'file_size_bytes':FILE_MAX}, 'native file cap differs')
    limits = p['storage_budget']['limits']
    ceilings = {'max_allocated_bytes':GIB,'max_logical_bytes':GIB,'max_entries':32768,'max_depth':32,'max_scan_seconds':5}
    require(set(limits) == set(ceilings) and all(type(limits[k]) is int and 0 < limits[k] <= v for k,v in ceilings.items()), 'original storage envelope exceeded')



def _finite_resources(p):
    """Registered finite envelope, bounded by the existing job authority.

    This validates declared numbers, not available headroom or full-size capacity.
    Schema2 additionally pins this exact object in real_pilot_input at admission.
    """
    fields={'memory_max_bytes','memory_high_bytes','reserve_bytes','start_reserve_bytes',
            'disk_floor_bytes','disk_paths','wall_seconds','storage_budget','native_unit_limits'}
    require(type(p) is dict and set(p)==fields, 'explicit real pilot resource fields required')
    numeric=fields-{'disk_paths','storage_budget','native_unit_limits'}
    require(all(type(p[k]) is int and 0<p[k]<2**63 for k in numeric), 'finite integer resource limits required')
    require(p['memory_high_bytes']<=p['memory_max_bytes']<=6*GIB and p['reserve_bytes']>=3*GIB
            and p['start_reserve_bytes']>=p['memory_max_bytes']+p['reserve_bytes'], 'existing job memory/reserve authority exceeded')
    require(p['wall_seconds']<=28800 and p['disk_floor_bytes']>=10*GIB, 'existing job disk/wall authority exceeded')
    paths=p['disk_paths']
    require(type(paths) is list and bool(paths) and all(type(v) is str and Path(v).is_absolute() for v in paths)
            and len(paths)==len(set(paths)), 'explicit distinct absolute guard volumes required')
    native=p['native_unit_limits']
    require(type(native) is dict and set(native)=={'file_size_bytes'} and type(native['file_size_bytes']) is int
            and 0<native['file_size_bytes']<2**63, 'finite registered native file limit required')
    budget=p['storage_budget']
    if type(budget) is dict and budget.get('schema_version')==2:
        require(set(budget)=={'schema_version','kind','authority_root','experiment','roots','shared_files','limits'} and budget['kind']=='real-pilot-writable-union','explicit writable union fields required')
    else:
        require(type(budget) is dict and set(budget)=={'root','limits'} and type(budget['root']) is str
                and Path(budget['root']).is_absolute(), 'explicit whole-root budget required')
    limits=budget['limits']
    require(type(limits) is dict and set(limits)=={'max_allocated_bytes','max_logical_bytes','max_entries','max_depth','max_scan_seconds'}
            and all(type(v) is int and 0<v<2**63 for v in limits.values()), 'finite storage limits required')
    require(limits['max_depth']<=64 and limits['max_scan_seconds']<=5, 'existing bounded census controls exceeded')
    require(native['file_size_bytes']<=min(limits['max_logical_bytes'],limits['max_allocated_bytes']), 'native file ceiling exceeds whole-tree reservation')


def _bind_resources(ad,job,plan):
    resources=job['resources']
    if plan['schema_version']==1:
        _tiny_resources(resources)
    else:
        from .provenance import canonical_bytes
        require(canonical_bytes(plan['resource_policy'])==canonical_bytes(resources), 'pilot plan/job resource policy differs')
    from .job import resource_policy
    resource_policy(resources,ad.root,pilot_context=(ad,job))
    # Physical volume capacity is only an upper bound. Available growth and
    # completed graph/MCM reservations need separate registered entry evidence.
    if plan['schema_version']==2:
        import os
        fs=os.statvfs(ad.root);usable=fs.f_blocks*fs.f_frsize-resources['disk_floor_bytes']
        limits=resources['storage_budget']['limits']
        require(0<usable and max(limits['max_allocated_bytes'],limits['max_logical_bytes'])<=usable,
                'declared tree budget exceeds physical volume less fixed floor')


def worker_limits(job):
    """Exact selected RLIMIT; no default, adaptive increase or fallback."""
    import resource
    schema(job)
    expected=job['resources']['native_unit_limits']['file_size_bytes']
    resource.setrlimit(resource.RLIMIT_FSIZE,(expected,expected))
    require(resource.getrlimit(resource.RLIMIT_FSIZE)==(expected,expected), 'selected worker file limit not enforced')
    return {'rlimit_fsize':expected,'scope':'worker and inherited descendants; outer launcher/log limits separately required'}


def publication_boundary(owner,stage,job):
    """Actual real-route stage; never applies the synthetic failure selector."""
    from . import compact_owner
    require(type(owner) is compact_owner.Owner and type(stage) is compact_owner.Stage
            and stage.owner is owner and owner.bound.record.get('resource_only') is True, 'actual same-owner resource stage required')
    run=owner.bound._run
    run._active();run._check_source();owner.check_binding()
    _,selected_plan,plan=admitted(run.admission,job)
    require(owner.bound.record['job_input']=='execution_job' and stage.kind=='mcm'
            and stage.name in tuple('mcm-'+h for h in sorted(plan['graph_inputs']))
            and selected_plan['descriptor']['required_graphs']==sorted(plan['graph_inputs']), 'real target publication differs')


def _read(ad, name):
    from ..admission import local_path
    info = ad.inputs[name]
    path = local_path(ad.root, info['path'])
    require(path.stat().st_size <= FILE_MAX, 'pilot metadata input too large')
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == info['sha256'], 'registered pilot input differs')
    return json.loads(raw)


def _source_authority_root(ad):
    """Retain directory repositories; authenticate selected worktree topology.

    This metadata join grants no source or run authority. Admission, installed
    code, runtime, Binding and Owner currentness checks remain required.
    """
    marker = ad.root / '.git'
    if marker.is_dir():
        return True
    require(marker.is_file() and not marker.is_symlink()
            and ad.root.is_absolute() and ad.root.resolve(strict=True) == ad.root,
            'canonical worktree source root required')
    require('execution_workspace' in ad.inputs, 'registered worktree layout required')
    from ..admission import _git
    from .job import workspace_binding
    require(Path(_git(ad.root, 'rev-parse', '--show-toplevel').decode().strip()) == ad.root,
            'worktree Git top-level differs')
    require(_read(ad, 'execution_workspace') == workspace_binding(ad.root),
            'registered worktree root/common Git mapping differs')
    # The marker alone can be copied to a different root. The actual Git
    # administration directory must independently point back to this marker.
    import os, stat
    from .owned_io import _opened
    admin = Path(_git(ad.root, 'rev-parse', '--absolute-git-dir').decode().strip())
    require(admin.is_absolute() and admin.resolve(strict=True) == admin,
            'canonical worktree administration directory required')
    backlink = admin / 'gitdir'
    with _opened(backlink, 'rb') as stream:
        original = os.fstat(stream.fileno())
        def pin(info):
            return tuple(getattr(info, key) for key in ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns'))
        require(stat.S_ISREG(original.st_mode) and original.st_nlink == 1
                and 0 < original.st_size <= 8192, 'bounded original worktree backlink required')
        raw = stream.read(8193)
        require(len(raw) == original.st_size and len(raw) <= 8192
                and pin(os.fstat(stream.fileno())) == pin(original) == pin(backlink.lstat()),
                'worktree backlink changed')
    require(raw.endswith(b'\n') and raw.count(b'\n') == 1 and b'\0' not in raw,
            'one original worktree backlink path required')
    target = Path(os.fsdecode(raw[:-1]))
    require(target.is_absolute(), 'absolute worktree backlink required by pinned Git runtime')
    require(target == marker and target.resolve(strict=True) == marker,
            'Git administration backlink differs from admitted worktree')
    return True


def _archive_namespace(ad, s, p, *, fresh=False):
    """Authenticate schema2 archive identity; freshness is an entry-only check."""
    if p['schema_version'] != 2 or 'archive_inputs' not in p:
        return
    import os
    import re
    transport = _read(ad, s['compact_archive_transport_input'])
    archive = _read(ad, s['compact_archive_input'])
    match = re.fullmatch(r'eth-paper-real-data-end-to-end-resource-(\d{8}-\d{2})', ad.experiment_id)
    require(match is not None, 'fixed real-pilot archive launch identity required')
    expected = 'ethpilot-' + match.group(1)
    require(transport.get('namespace') == archive.get('remote_namespace') == expected,
            'archive transport/remote namespace differs from fixed pilot launch')
    if fresh:
        require(not os.path.lexists(ad.root/'research_artifacts'/('archive-dispatch-'+expected)),
                'archive transport namespace already reserved before claim')


def admitted(ad, job, *, fresh_archive=False):
    schema(job)
    name,s = next(iter(job['payload']['representation_jobs'].items()))
    p = validate_plan(_read(ad, s['real_pilot_input']))
    _bind_resources(ad,job,p)
    expected_archive={'policy_input':s['compact_archive_input'],'transport_input':s['compact_archive_transport_input']} if 'compact_archive_input' in s else None
    require(p.get('archive_inputs')==expected_archive,'pilot/producer archive input pair differs')
    require(ad.family['mechanism_id'] == 'celik-sefer-transaction-graph-full-neural-replication' and ad.experiment['cells'] == [p['cell_id']], 'separate one-cell resource pilot admission required')
    budget=job['resources']['storage_budget']
    if budget.get('schema_version')==2:
        from .real_pilot_storage import validate,EXPERIMENT
        require(p['schema_version']==2 and ad.experiment_id==EXPERIMENT,'union requires fixed schema2 real pilot')
        validate(budget,ad.root)
        require(_source_authority_root(ad),'original source authority root required')
    else:
        require(Path(budget['root']) == ad.root and _source_authority_root(ad), 'complete isolated workspace watch required')
    from .job import required_sources
    require(required_sources() <= set(ad.experiment['source_files']), 'complete current package closure required')
    own = 'tradingagents/research/onchain_replication/real_pilot_import_caller.py'
    require(Path(__file__).resolve() == ad.root/own and hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == ad.experiment['source_files'][own], 'caller must be installed as exact admitted source')
    require(set(p['outputs'].values()) <= set(ad.experiment['outputs']), 'pilot outputs not registered')
    d = s['descriptor']
    require(d.get('required_graphs') == sorted(p['graph_inputs']) and d.get('resource_graph_inputs') == p['graph_inputs'], 'producer full graph mapping differs')
    plan = _read(ad, s['plan_input'])
    require(plan['schema_version'] == 2, 'version2 imported producer plan required')
    item = plan['producers'][s['producer']]
    require(all(item.get(k) == v for k,v in s.items()) and item['binding_output'] == p['outputs']['binding']
            and item['journal_output'] == p['outputs']['journal'], 'producer/selected pilot mismatch')
    roles = set(p['graph_inputs'].values()) | {p[k] for k in ('population_plan_input','model_input','training_input')}
    if p.get('imported_authority_lease_input') is not None:
        from .imported_authority_interval import policy
        policy(_read(ad,p['imported_authority_lease_input']));roles.add(p['imported_authority_lease_input'])
    if 'archive_inputs' in p:roles.update(p['archive_inputs'].values())
    if '0114d61904938208c75497bdabe82c5dae32b7d2110a4e460d1942f84dc473ba' in p['graph_inputs']:
        from .real_pilot_legacy_graph import registered
        roles.update(registered(ad.inputs,p['graph_inputs']))
    require(roles <= set(ad.inputs), 'real population/config/graph inputs not registered')
    control = _read(ad, s['original_dictionary_input'])
    require(control['sample_count'] == 512 and control['motif_count'] == 32
            and control['required_graphs'] == sorted(p['graph_inputs']), 'exact original512/32 import required')
    if p['schema_version']==2 and 'archive_inputs' in p:
        _archive_namespace(ad,s,p,fresh=fresh_archive)
        from .real_pilot_reservations import validate as reservations
        output=_read(ad,s['compact_mcm_output_input'])
        require(output.get('payload_archive_input') in ad.inputs,'registered typed payload reservation required')
        for field,key,hash_key in (('compact_policy_input','compact_execution','policy_sha256'),
                ('compact_archive_input','compact_archive_execution','policy_sha256'),
                ('pair_checkpoint_input','pair_execution','policy_sha256'),
                ('original_dictionary_input','original_dictionary_import','sha256'),
                ('original_dictionary_stage_input','original_dictionary_stage','sha256')):
            require(d.get(key,{}).get(hash_key)==ad.inputs[s[field]]['sha256'],'reservation descriptor hash differs: '+key)
        reservations(_read(ad,s['compact_policy_input']),_read(ad,s['original_dictionary_stage_input']),
            _read(ad,s['compact_mcm_input']),output,_read(ad,s['compact_archive_input']),
            _read(ad,output['payload_archive_input']),_read(ad,s['pair_checkpoint_input']),p['graph_inputs'])
    return name,s,p


def _close(journal, owner, targets, reference, binding, plan, training, artifact):
    """Close this explicit resource route from actual typed objects and bytes."""
    from . import compact_owner, import_metadata, resource_binding, resource_fixture
    from .feature_journal import FeatureJournal
    from .provenance import canonical_bytes, thaw
    require(type(journal) is FeatureJournal and type(owner) is compact_owner.Owner, 'genuine journal and Owner required')
    bound = owner.bound; run = bound._run
    require(owner.closed and not owner.poisoned and not journal.sealed and owner.root == journal.directory/'compact', 'actual closed import Owner required')
    bound.check(); journal._resource_check(); resource_binding.assert_selected(bound, 'execution_job')
    require(canonical_bytes(thaw(bound.record)) == binding, 'Binding changed before closure')
    require(tuple(owner.required) == tuple(['dictionary-import']+['mcm-'+h for h in sorted(plan['graph_inputs'])]), 'eight actual stages required')
    records = [resource_fixture.verify_retained(t,owner) for t in targets]
    require(len(records) == 7 and [r['graph_hash'] for r in records] == sorted(plan['graph_inputs'])
            and all(r['motifs'] == 32 and r['cells'] == 32*r['rows'] for r in records), 'seven full original32 targets required')
    raw = import_metadata.read(owner.root, 'complete.json'); terminal = json.loads(raw)
    require(hashlib.sha256(raw).hexdigest() == reference and terminal['owner'] == owner.identity
            and terminal['stages'] == 8 and terminal['pairs'] == sum(r['cells'] for r in records), 'actual Owner completion differs')
    require(json.loads((artifact/'complete.json').read_bytes()) == training
            and training['status'] == 'complete' and training['optimizer_steps'] == 1
            and training['financial_fit_complete'] is False and training['checkpoint_exact_readback'] is True, 'actual one-update completion differs')
    checkpoint = artifact/'checkpoint.pt'
    require(checkpoint.stat().st_size == training['checkpoint_bytes'] <= plan['max_checkpoint_bytes']
            and hashlib.sha256(checkpoint.read_bytes()).hexdigest() == training['checkpoint_sha256'], 'retained checkpoint differs')
    value = {'schema_version':1,'kind':KIND,'status':'complete','resource_only':True,
             'financial_representation_admitted':False,'paper_financial_fits':0,
             'owner':journal.owner,'compact_owner_sha256':reference,'targets':records,'training':training}
    journal._publish(journal.directory/'complete.json', value)
    journal._resource_check(); import_metadata.exact(owner.root,'complete.json',raw)
    require([resource_fixture.verify_retained(t,owner) for t in targets] == records, 'target changed during closure')
    run._active(); bound._guard(); object.__setattr__(journal,'sealed',True)
    return value


def execute(run, payload):
    from tradingagents.research.lifecycle import ResearchRun
    require(type(run) is ResearchRun, 'actual ResearchRun required; caller never starts one')
    run._active(); run._check_source()
    from . import resource_binding, original_import_preparation, original_import_stage
    from . import compact_mcm, compact_owner, resource_fixture, original_dictionary
    from . import real_pilot_training as training_helper
    from .imported_mcm_identity import Target
    from .graph_store import load_graph
    from .population_assembly import produce_registered_population
    from .job_payload import population_from_record
    from .provenance import canonical_bytes, thaw, durable_mkdir
    from .workflow_storage import StorageWatch
    from ..admission import local_path
    job = json.loads(run.read_input('execution_job'))
    require(job['payload'] == payload, 'exact registered pilot payload required')
    name,s,p = admitted(run.admission,job)
    budget=job['resources']['storage_budget']
    if budget.get('schema_version')==2:
        from .real_pilot_storage import WritableUnion
        watch=WritableUnion(budget,run.admission.root)
        from .resources import assert_guarded_worker
        limits=job['resources']
        live=assert_guarded_worker(run.admission.root/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/run.admission.experiment_id/'guard',__import__('sys').orig_argv,required_paths=[run.admission.root],wall_seconds=limits['wall_seconds'],memory_max_bytes=limits['memory_max_bytes'],memory_high_bytes=limits['memory_high_bytes'],disk_floor_bytes=limits['disk_floor_bytes'])
        require(live.get('storage_budget')==budget,'worker/monitor writable scopes differ')
    else:watch=StorageWatch(run.admission.root,budget['limits'])
    watch.check()
    resource_subset = p.get('population_scope') == 'resource_pilot_subset'
    if resource_subset:
        from .real_pilot_population import produce
        examples,scaler,indices = produce(run,p['population_plan_input'],p)
    else:
        assembly = produce_registered_population(run,p['population_plan_input'])
        examples,scaler = population_from_record(assembly['population'])
        indices = p['indices']
    require(indices[-1] < len(examples.train), 'registered eligible batch outside actual training population')
    chosen = [examples.train[i] for i in indices]
    require([x.decision_at for x in chosen] == p['decisions']
            and [list(x.graph_hashes) for x in chosen] == p['graph_sequences']
            and all(len(x.input_prices) == 28 for x in chosen), 'actual checked eligible rows differ')
    if not resource_subset:
        require(assembly['provenance']['source_admission']['asset'] == 'ETH', 'real ETH source required')
    control = json.loads(run.read_input(s['original_dictionary_input']))
    original_dictionary.policy_check(control)
    graphs = {}
    for key,role in sorted(p['graph_inputs'].items()):
        info = run.admission.inputs[role]
        graph = load_graph(local_path(run.admission.root,info['path']),info['sha256'],resident=True)
        require(graph.asset == 'ETH', 'real graph asset differs')
        if key == '0114d61904938208c75497bdabe82c5dae32b7d2110a4e460d1942f84dc473ba':
            from .real_pilot_legacy_graph import verify
            verify(run,graph,role)
        graphs[key] = graph
    model_config = json.loads(run.read_input(p['model_input']))
    training_config = json.loads(run.read_input(p['training_input']))
    # Validate fixed configurations before import Owner birth, not after MCM work.
    require(hashlib.sha256(training_helper._encode(model_config)).hexdigest() == training_helper.MODEL_SHA
            and hashlib.sha256(training_helper._encode(training_config)).hexdigest() == training_helper.TRAINING_SHA, 'original model/training configs differ')
    from .model import ReplicationModel, validate_execution
    validated_execution = validate_execution(p['model_execution'])
    selected_execution = None if validated_execution is None else dict(validated_execution)
    journal = owner = archive_context = None; targets = []; events = []; began = time.monotonic()
    from .real_pilot_throughput import MCMMeasurements
    measurements = MCMMeasurements({key:len(g.node_ids) for key,g in graphs.items()},
        population_scope=p.get('population_scope','full_fold_input'))
    progress = None
    if 'partial_progress' in p:
        from .real_pilot_partial_progress import MCMProgress
        progress = MCMProgress(p['partial_progress'],{key:len(g.node_ids) for key,g in graphs.items()},
            claim_sha256=run._claim_sha256,source=run.admission.source)
    terminal = training = None; primary = None
    def mark(phase):
        events.append({'phase':phase,'elapsed_seconds':time.monotonic()-began})
    try:
        if 'archive_inputs' in p:
            from . import archive_dispatch
            archive_plan=archive_dispatch.preflight(run,payload,{name:True})
            require(archive_plan is not None,'selected real-pilot archive preflight absent')
            archive_context=archive_dispatch.Context(archive_plan)
        journal,bound = resource_binding.open_first(run,representation=name,plan_input=s['plan_input'],producer=s['producer'],policy_input=s['pair_checkpoint_input'],job_input='execution_job')
        binding = canonical_bytes(thaw(bound.record))
        prepared = original_import_preparation.prepare(bound,input_name=s['original_dictionary_input'],job_input='execution_job')
        if archive_context is None:
            owner,stage = original_import_stage.attach(prepared,policy_input=s['compact_policy_input'],stage_policy_input=s['original_dictionary_stage_input'])
        else:
            owner,stage = original_import_stage.attach(prepared,policy_input=s['compact_policy_input'],stage_policy_input=s['original_dictionary_stage_input'],archive_transport=archive_context.view(name))
        execution = original_import_stage.ImportedExecution(stage)
        if p.get('imported_authority_lease_input') is not None:
            from .imported_authority_lease import activate
            activate(execution,p['imported_authority_lease_input'])
        require(len(execution._materialized._dictionary.representatives) == 32, 'all original motifs required')
        mark('original_import')
        checked = [Target(execution,g,k) for k,g in graphs.items()]
        for target in checked:
            compact_mcm._prepare(target,target.key,s['compact_mcm_input'],s['compact_mcm_output_input'])
        for key,g in graphs.items():
            watch.check()
            measurements.begin(key)
            result = compact_mcm.produce_imported(execution,g,graph_hash=key,input_name=s['compact_mcm_input'],output_input=s['compact_mcm_output_input'],
                **({'progress':progress} if progress is not None else {}))
            targets.append(result); result.check()
            retained = resource_fixture.verify_retained(result,owner)
            measurements.completed(key,retained)
            mark('mcm-'+key)
        import torch
        torch.set_num_threads(2)
        from .evaluation import batch_factory
        features = {}; contracts = {}
        for (key,g), result in zip(graphs.items(),targets,strict=True):
            # Complete existing arrays, no node/edge/motif subset or fabricated fill.
            mcm = torch.from_numpy(result.matrix)
            edges = torch.from_numpy(g.edge_index)
            features[key] = {'mcm':mcm,'edge_index':edges}
            contracts[key] = {'nodes':len(g.node_ids),'edges':g.edge_index.shape[1],
                              'mcm_sha256':training_helper._tensor_hash(mcm),
                              'edge_index_sha256':training_helper._tensor_hash(edges)}
        batch = batch_factory('proposed','direction',examples.train,scaler,features)
        def authority():
            run._active(); bound.check(); execution.check(); watch.check()
            require(owner.bound is bound and bound._run is run and not owner.closed and not owner.poisoned, 'live genuine import chain required')
            for target in targets: target.check()
        artifact = run.directory/'artifacts'
        durable_mkdir(artifact)
        training = training_helper.run_one_update(model_factory=lambda:ReplicationModel(model_config,'classification',execution=selected_execution),
            batch_factory=batch,indices=indices,graph_features=features,graph_contracts=contracts,
            graph_sequences=p['graph_sequences'],model_config=model_config,training_config=training_config,
            provenance={'claim_sha256':run._claim_sha256,'pilot_input_sha256':run.admission.inputs[s['real_pilot_input']]['sha256'],
                        'original_dictionary':control['dictionary_identity'],'original_samples':control['sample_identity'],
                        'source':run.admission.source,'train_hash':examples.train_hash,'resource_only':True},
            directory=artifact/'real-pilot-one-update',authority_check=authority,max_checkpoint_bytes=p['max_checkpoint_bytes'],
            task='classification',seed=11,model_execution=p['model_execution'])
        mark('one_update_checkpoint_readback')
        authority()
        with compact_owner._held(owner): reference = owner._finish()
        terminal = _close(journal,owner,targets,reference,binding,p,training,artifact/'real-pilot-one-update')
    except BaseException as error:
        primary = error
        try: measurements.failed(error)
        except BaseException as later: primary = resource_fixture._preserve_terminal(primary,later)
        if journal is not None and not journal.sealed:
            try: journal.seal('failed',reason=type(error).__name__+': '+str(error)[:1024])
            except BaseException as later: primary = resource_fixture._preserve_terminal(primary,later)
    if archive_context is not None:
        try:archive_context.close(primary)
        except BaseException as later:primary=resource_fixture._preserve_terminal(primary,later)
    throughput = None
    try: throughput = measurements.summary(training)
    except BaseException as later: primary = resource_fixture._preserve_terminal(primary,later)
    # Independently attempt each remaining publication; retain the first fatal.
    row = {'id':p['cell_id'],'status':'complete' if primary is None else 'failed','resource_only':True,
           'financial_fit_complete':False,'paper_financial_fits':0}
    if primary is not None: row['reason'] = type(primary).__name__+': '+str(primary)[:1024]
    summary = {'schema_version':1,'kind':KIND,'cell':row,'original_samples':512,'original_motifs':32,
               'full_graphs':7,'retained_target_count':len(targets),'training':training,'events':events,
               'throughput':throughput,
               'financial_fit_complete':False,'full_size_capacity':False,'final_outer_inventory_required':True}
    if progress is not None:summary['partial_mcm_progress'] = progress.summary()
    terminal = terminal or {'schema_version':1,'kind':KIND,'status':'failed','resource_only':True,'reason':row['reason']}
    actions = [lambda:watch.check(),lambda:run.write_json(p['outputs']['binding'],terminal),
               lambda:run.write_json(p['outputs']['journal'],terminal),
               lambda:run.write_json(p['outputs']['ledger'],[row]),lambda:run.write_json(p['outputs']['summary'],summary)]
    for action in actions:
        try: action()
        except BaseException as later: primary = resource_fixture._preserve_terminal(primary,later)
    if primary is not None: raise primary
    return [row]
