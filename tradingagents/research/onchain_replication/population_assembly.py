"""Assemble chronological populations from admitted metadata without graph arrays.

This is preparation, not a source-admission bypass: exact manifest, price-panel,
calendar and fold identities must already be frozen. Array content verification
remains the graph loader's responsibility before representation computation.
"""
from dataclasses import asdict
from datetime import timedelta
import json
from pathlib import Path

from .calendar import expected_week, stamp
from .dataset import CalendarGraph, build_examples_from_metadata, fit_scaler
from .evaluation import example_binding
from .job_payload import population_record
from .provenance import canonical_bytes, digest, require_hash, utc, durable_mkdir, sync_directory


def required_weeks(fold, lookback_days):
    if type(lookback_days) is not int or lookback_days <= 0:
        raise ValueError('positive integer lookback required')
    if not utc(fold.train_start) < utc(fold.train_end) <= utc(fold.test_start) < utc(fold.test_end):
        raise ValueError('invalid fold')
    start = utc(fold.train_start) - timedelta(days=lookback_days-1)
    end = utc(fold.test_end)
    weeks = set()
    while start < end:
        weeks.add(expected_week(stamp(start)))
        start += timedelta(days=1)
    return tuple(sorted(weeks))


def assemble_population(graph_references, price_panel, fold, calendar_config,
                        expected_weeks, source_admission):
    c = source_admission
    required = {'asset', 'graph_config_hash', 'price_source_hash', 'price_panel_hash',
                'calendar_hash', 'fold_hash', 'graph_manifest_hashes', 'source_hashes', 'unavailable_week_hashes'}
    if set(c) != required:
        raise ValueError('source admission fields differ')
    for key in ('graph_config_hash', 'price_source_hash', 'price_panel_hash', 'calendar_hash', 'fold_hash'):
        require_hash(c[key])
    if (c['asset'] not in ('ETH','BTC') or price_panel.symbol != c['asset']+'-USD'
            or price_panel.source_hash != c['price_source_hash']
            or digest(canonical_bytes(asdict(price_panel))) != c['price_panel_hash']
            or digest(canonical_bytes(calendar_config)) != c['calendar_hash']
            or fold.member_hash != c['fold_hash']):
        raise ValueError('price/calendar/fold identity differs from admission')
    matching = [row for row in calendar_config['folds'] if row['id'] == fold.id]
    actual_fold = {k:v for k,v in asdict(fold).items() if k != 'member_hash'}
    if len(matching) != 1:
        raise ValueError('fold not uniquely declared by calendar')
    declared_fold = {k:stamp(v) if v is not None and k != 'id' else v for k,v in matching[0].items()}
    if canonical_bytes(actual_fold) != canonical_bytes(declared_fold):
        raise ValueError('fold fields differ from frozen calendar')
    weeks = required_weeks(fold, calendar_config['lookback_days'])
    if tuple(expected_weeks) != weeks or set(graph_references) != set(weeks):
        raise ValueError('weekly source denominator differs')
    hashes = c['graph_manifest_hashes']
    if hashes != sorted(set(hashes)):
        raise ValueError('duplicate or unordered admitted manifest identity')
    if not c['source_hashes'] or len(c['source_hashes']) != len(set(c['source_hashes'])):
        raise ValueError('invalid admitted source membership')
    for value in [*hashes, *c['source_hashes']]:
        require_hash(value)
    unavailable = {week:digest(canonical_bytes(ref)) for week,ref in graph_references.items() if ref['status'] == 'unavailable'}
    if unavailable != c['unavailable_week_hashes']:
        raise ValueError('unavailable week evidence differs from admission')
    used = []
    metadata = []
    dispositions = {}
    for week in weeks:
        ref = graph_references[week]
        if ref['status'] == 'unavailable':
            if set(ref) != {'status', 'reason', 'evidence_hashes'} or not ref['reason'] or not ref['evidence_hashes']:
                raise ValueError('unavailable week requires reason and evidence')
            for h in ref['evidence_hashes']:
                require_hash(h)
            dispositions[week] = dict(ref)
            continue
        if ref['status'] != 'complete' or set(ref) != {'status', 'raw_manifest', 'sha256'}:
            raise ValueError('weekly graph reference fields differ')
        if digest(ref['raw_manifest']) != ref['sha256'] or ref['sha256'] not in hashes:
            raise ValueError('graph manifest hash differs from admission')
        manifest = json.loads(ref['raw_manifest'])
        if set(manifest) != {'metadata', 'graph_hash', 'arrays'}:
            raise ValueError('graph manifest schema differs')
        m = manifest['metadata']
        if (m['asset'] != c['asset'] or m['graph_config_hash'] != c['graph_config_hash']
                or stamp(m['start_utc']) != week or not m['source_hashes']
                or not set(m['source_hashes']) <= set(c['source_hashes'])):
            raise ValueError('graph metadata differs from admission/week')
        require_hash(manifest['graph_hash'])
        arrays = manifest['arrays']
        if not {'node_ids','node_features','edge_index','edge_features'} <= set(arrays) <= {'node_ids','node_features','edge_index','edge_features','edge_aggregates'}:
            raise ValueError('graph array manifest fields differ')
        for name, record in arrays.items():
            if (set(record) != {'path','sha256','bytes'} or record['path'] != name+'.npy'
                    or type(record['bytes']) is not int or record['bytes'] <= 0):
                raise ValueError('invalid graph array reference')
            require_hash(record['sha256'])
        metadata.append(CalendarGraph(m['asset'], m['start_utc'], m['end_utc'],
                                      m['available_at'], tuple(m['source_hashes']), manifest['graph_hash']))
        used.append(ref['sha256'])
        dispositions[week] = {'status':'complete','manifest_sha256':ref['sha256'],
                              'graph_hash':manifest['graph_hash'], 'available_at':stamp(m['available_at'])}
    if sorted(used) != hashes:
        raise ValueError('admitted graph manifest denominator differs')
    examples = build_examples_from_metadata(metadata, price_panel, fold, calendar_config)
    scaler = fit_scaler(examples, price_panel, fold)
    decision_count = (utc(fold.test_end)-utc(fold.train_start)).days
    if len(examples.train)+len(examples.test)+len(examples.exclusions) != decision_count:
        raise ValueError('decision denominator differs')
    return {'schema_version':1, 'population':population_record(examples, scaler),
            'binding':example_binding(examples, scaler), 'weeks':dispositions,
            'decision_count':decision_count,
            'provenance':{'source_admission':c, 'source_admission_hash':digest(canonical_bytes(c)),
                          'expected_weeks':weeks, 'calendar':calendar_config,
                          'fold':asdict(fold), 'array_bytes_reverified':False,
                          'scope':'metadata population assembly; arrays require verification before representation fitting'}}


def publish_population(directory, assembly):
    """Exclusive prepared artifact; not an empirical claim or automatic admission."""
    from tradingagents.research.lifecycle import _immutable
    directory = Path(directory)
    durable_mkdir(directory.parent)
    directory.mkdir(exist_ok=False)
    sync_directory(directory.parent)
    _immutable(directory/'intent.json', {'assembly_hash':digest(canonical_bytes(assembly))})
    values = {'population.json':assembly['population'], 'binding.json':assembly['binding'],
              'assembly.json':{k:v for k,v in assembly.items() if k not in ('population','binding')}}
    for name, value in values.items():
        _immutable(directory/name, value)
    receipt = {'status':'complete', 'files':{name:digest((directory/name).read_bytes()) for name in values}}
    _immutable(directory/'complete.json', receipt)
    return receipt


def produce_registered_population(run, plan_input):
    """Publish population/binding inside an already admitted claim, before fitting."""
    from .contracts import Fold, PricePanel
    plan = json.loads(run.read_input(plan_input))
    if set(plan) != {'schema_version','graphs','price_input','fold','calendar_input',
                     'expected_weeks','admission_input','outputs'} or plan['schema_version'] != 1:
        raise ValueError('population producer plan schema differs')
    outputs = plan['outputs']
    if (set(outputs) != {'population','binding','assembly'} or len(set(outputs.values())) != 3
            or not set(outputs.values()) <= set(run.admission.experiment['outputs'])):
        raise ValueError('population producer outputs not registered')
    if set(outputs.values()) & set(run._published_outputs):
        raise ValueError('population producer output already published')
    refs = {}
    for week, reference in plan['graphs'].items():
        if set(reference) != {'input','status'}:
            raise ValueError('population graph requires an admitted input')
        raw = run.read_input(reference['input'])
        if reference['status'] == 'complete':
            refs[week] = {'status':'complete','raw_manifest':raw,'sha256':digest(raw)}
        elif reference['status'] == 'unavailable':
            refs[week] = json.loads(raw)
            if refs[week].get('status') != 'unavailable':
                raise ValueError('unavailable source disposition differs')
        else:
            raise ValueError('unknown weekly population disposition')
    price_record = json.loads(run.read_input(plan['price_input']))
    prices = PricePanel(**{k:tuple(v) if k in ('dates','closes','missing_dates') else v for k,v in price_record.items()})
    result = assemble_population(refs, prices, Fold(**plan['fold']),
                json.loads(run.read_input(plan['calendar_input'])), plan['expected_weeks'],
                json.loads(run.read_input(plan['admission_input'])))
    run.write_json(outputs['population'], result['population'])
    run.write_json(outputs['binding'], result['binding'])
    run.write_json(outputs['assembly'], {k:v for k,v in result.items() if k not in ('population','binding')})
    return result
