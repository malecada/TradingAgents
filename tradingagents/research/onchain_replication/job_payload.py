"""Prepared component assembly inside one resource-guarded admitted job.

The source and population inputs must already be admitted. No automatic source
acquisition, mask repair or hidden representation fallback occurs during a fit.
"""
from dataclasses import asdict, fields
import json

from .contracts import Fold
from .dataset import Example, ExampleManifest, Scaler
from .provenance import canonical_bytes, freeze


def population_record(examples, scaler):
    return {'schema_version': 1,
        'examples': {'train': [asdict(x) for x in examples.train], 'test': [asdict(x) for x in examples.test],
            'exclusions': [dict(x) for x in examples.exclusions], 'train_hash': examples.train_hash,
            'test_mask_hash': examples.test_mask_hash, 'source_hashes': list(examples.source_hashes), 'fold_hash': examples.fold_hash},
        'scaler': asdict(scaler)}


def population_from_record(record):
    if set(record) != {'schema_version', 'examples', 'scaler'} or record['schema_version'] != 1:
        raise ValueError('population payload schema differs')
    source = record['examples']
    if set(source) != {f.name for f in fields(ExampleManifest)}:
        raise ValueError('example manifest fields differ')
    def example(row):
        if set(row) != {f.name for f in fields(Example)}:
            raise ValueError('example payload fields differ')
        return Example(**{k: tuple(v) if k in ('input_dates', 'input_prices', 'graph_hashes', 'graph_available_at') else v for k, v in row.items()})
    examples = ExampleManifest(tuple(map(example, source['train'])), tuple(map(example, source['test'])),
        tuple(freeze(x) for x in source['exclusions']), source['train_hash'], source['test_mask_hash'],
        tuple(source['source_hashes']), source['fold_hash'])
    scaler = Scaler(**{**record['scaler'], 'dates': tuple(record['scaler']['dates'])})
    return examples, scaler


def execute_fit_payload(run, payload, *, job_input='execution_job'):
    """Build/reuse registered fixed representations, then execute the batch."""
    from .graph_store import load_graph
    from .registered_features import prepare_registered_features, reuse_registered_features
    from .run import execute_batch, preflight_batch
    from .feature_pipeline import representation_arm
    from .cache import cache_key
    registered = json.loads(run.read_input(job_input))
    if registered['kind'] != 'fit' or canonical_bytes(registered['payload']) != canonical_bytes(payload):
        raise ValueError('fit job payload differs from registration')
    populations = {}
    for name, reference in payload['population_inputs'].items():
        if isinstance(reference, str):
            record = json.loads(run.read_input(reference))
        elif isinstance(reference, dict) and set(reference) == {'producer_input'}:
            from .population_assembly import produce_registered_population
            record = produce_registered_population(run, reference['producer_input'])['population']
        else:
            raise ValueError('invalid population input/producer reference')
        populations[name] = population_from_record(record)
    batch_plan = json.loads(run.read_input(payload['batch_plan_input']))
    if set(populations) != set(batch_plan['populations']):
        raise ValueError('job population membership differs from batch')
    if set(payload['representation_jobs']) != set(batch_plan['representations']):
        raise ValueError('job representation membership differs from batch')
    used = {item['representation'] for item in batch_plan['cells'] if item['status'] == 'ready' and item['representation'] is not None}
    if used != set(payload['representation_jobs']):
        raise ValueError('unreferenced representation computation forbidden')
    preflight_batch(run, populations, plan_input=payload['batch_plan_input'])
    for item in batch_plan['cells']:
        if item['status'] != 'ready' or item['representation'] is None:
            continue
        cell = item['cell']
        job = payload['representation_jobs'][item['representation']]
        descriptor = job['descriptor']
        examples, _ = populations[item['population']]
        required = sorted({h for row in (*examples.train, *examples.test) for h in row.graph_hashes})
        if descriptor['arm'] != representation_arm(cell['arm']) or descriptor['seed'] != cell['seed'] or descriptor['fold']['id'] != cell['fold'] or descriptor['fold']['member_hash'] != examples.fold_hash or descriptor['train_hash'] != examples.train_hash or descriptor['required_graphs'] != required or not set(required) <= set(descriptor['graph_population']):
            raise ValueError('representation job science differs from cell/population before fitting')
    for name, job in payload['representation_jobs'].items():
        reference = batch_plan['representations'][name]
        if 'output' not in reference or not reference.get('failure_output') or not {reference['output'], reference['failure_output']} <= set(run.admission.experiment['outputs']):
            raise ValueError('job binding/failure outputs must be registered before fitting')
        if job['operation'] == 'produce':
            source_examples, _ = populations[job['population']]
            required = sorted({h for row in (*source_examples.train, *source_examples.test) for h in row.graph_hashes})
            descriptor = job['descriptor']
            if source_examples.train_hash != descriptor['train_hash'] or source_examples.fold_hash != descriptor['fold']['member_hash'] or descriptor['required_graphs'] != required:
                raise ValueError('producer population differs from descriptor before fitting')
            producer = json.loads(run.read_input(job['plan_input']))['producers'][job['producer']]
            if canonical_bytes(producer['descriptor']) != canonical_bytes(job['descriptor']) or producer['binding_output'] != reference['output'] or producer['journal_output'] not in run.admission.experiment['outputs']:
                raise ValueError('producer descriptor/output differs before fitting')
        elif job['operation'] == 'reuse':
            run.read_input(job['journal_input'])
        else:
            raise ValueError('unknown representation operation before fitting')
    prepared = {}
    for name, job in payload['representation_jobs'].items():
        reference = batch_plan['representations'][name]
        if 'output' not in reference or not reference.get('failure_output'):
            raise ValueError('job representations require registered binding/failure outputs')
        try:
            descriptor = job['descriptor']
            if job['operation'] == 'reuse':
                value = reuse_registered_features(run, job['journal_input'], descriptor,
                                                 max_array_bytes=job['max_array_bytes'])
                run.write_json(reference['output'], value.binding)
            elif job['operation'] == 'produce':
                plan = json.loads(run.read_input(job['plan_input']))
                producer = plan['producers'][job['producer']]
                if canonical_bytes(producer['descriptor']) != canonical_bytes(descriptor) or producer['binding_output'] != reference['output']:
                    raise ValueError('job representation descriptor/output differs')
                examples, _ = populations[job['population']]
                manifests = []
                declared_bytes = 0
                for h in descriptor['graph_population']:
                    graph_reference = producer['graphs'][h]
                    if set(graph_reference) != {'input'}:
                        raise ValueError('job graph loader requires admitted immutable graph input')
                    input_name = graph_reference['input']
                    metadata = json.loads(run.read_input(input_name))
                    declared_bytes += sum(x['bytes'] for x in metadata['arrays'].values())
                    info = run.admission.inputs[input_name]
                    manifests.append((run.admission.root/info['path'], info['sha256']))
                if type(job['max_graph_payload_bytes']) is not int or not 0 < declared_bytes <= job['max_graph_payload_bytes']:
                    raise ValueError('registered aggregate graph payload capacity exceeded; Python/temporary overhead needs outer guard')
                graphs = tuple(load_graph(path, sha) for path, sha in manifests)
                value, _ = prepare_registered_features(run, job['producer'], graphs, examples,
                    Fold(**descriptor['fold']), descriptor['arm'], descriptor['seed'], descriptor['configs'],
                    plan_input=job['plan_input'], max_entries=producer['max_entries'],
                    max_array_bytes=producer['max_array_bytes'], continuation_input=job.get('continuation_input'))
                del graphs
            else:
                raise ValueError('unknown representation operation')
            if value.binding['workflow_identity'] != cache_key(descriptor):
                raise ValueError('job representation workflow differs')
            run.write_json(reference['failure_output'], {'status': 'complete', 'representation': name,
                'reason': 'fixed representation available; no failure', 'workflow_identity': value.binding['workflow_identity']})
            prepared[name] = value
        except (ValueError, RuntimeError, OSError) as error:
            reason = type(error).__name__+': '+str(error)
            # Completed numerical journals/partial outputs remain untouched.
            run.write_json(reference['failure_output'], {'status': 'failed', 'representation': name, 'reason': reason})
            if reference['output'] not in run._published_outputs:
                run.write_json(reference['output'], {'status': 'unavailable', 'reason': reason})
            if job['operation'] == 'produce':
                producer = json.loads(run.read_input(job['plan_input']))['producers'][job['producer']]
                if producer['journal_output'] not in run._published_outputs:
                    run.write_json(producer['journal_output'], {'status': 'unavailable', 'reason': reason})
    return execute_batch(run, populations, prepared, plan_input=payload['batch_plan_input'])
