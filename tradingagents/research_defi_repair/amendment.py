"""One reviewed +1 certificate; this does not assess scientific information value."""
import hashlib
import json


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


MUTABLE = {'parent', 'charter', 'question', 'source_files', 'runtime_hashes', 'outputs', 'budget_amendment'}
CERT_FIELDS = {'schema_version', 'amendment_id', 'program_id', 'family_id', 'mechanism_id', 'family_sha256',
               'increment', 'target_experiment', 'parent_experiment', 'target_contract_sha256', 'prior_claims',
               'review', 'repair_preflight', 'economic_manifest'}


def validate(*, root, source, design_source, spec, experiment, relevant, own_claim, committed):
    """Validate metadata and retained receipt bytes before empirical reads."""
    from .admission import identity, utc, _git
    from tradingagents.research.verify import verify_run
    exp = spec['experiments'][experiment]
    family = spec['families'][exp['family']]
    def reference(ref):
        if not isinstance(ref, dict) or set(ref) != {'path', 'sha256'}:
            raise ValueError('amendment reference must contain path and sha256 only')
        raw = committed(root, source, ref['path'], ref['sha256'])
        if committed(root, design_source, ref['path'], ref['sha256']) != raw:
            raise ValueError('amendment evidence changed from design freeze')
        return raw
    certificate = json.loads(reference(exp['budget_amendment']))
    if set(certificate) != CERT_FIELDS or type(certificate['schema_version']) is not int or certificate['schema_version'] != 1:
        raise ValueError('invalid amendment certificate schema')
    identity(certificate['amendment_id'], 'amendment')
    if type(certificate['increment']) is not int or certificate['increment'] != 1:
        raise ValueError('amendment must grant exactly one attempt')
    for field, expected in {'program_id': spec['program_id'], 'family_id': exp['family'],
                            'mechanism_id': family['mechanism_id'], 'family_sha256': sha(canonical(family)),
                            'target_experiment': experiment, 'parent_experiment': exp['parent'],
                            'target_contract_sha256': sha(canonical({k:v for k,v in exp.items() if k != 'budget_amendment'}))}.items():
        if certificate[field] != expected:
            raise ValueError('amendment identity/contract mismatch: ' + field)
    old = [claim for claim in relevant if claim['experiment_id'] != own_claim]
    if any('budget_amendment' in claim['experiment'] for claim in old):
        raise ValueError('amendment chaining or reuse prohibited')
    if len(old) + family['prior_attempts'] != family['attempt_budget']:
        raise ValueError('one amendment requires exactly exhausted original budget')
    inventory = certificate['prior_claims']
    if not isinstance(inventory, dict) or set(inventory) != {c['experiment_id'] for c in old}:
        raise ValueError('amendment prior claim inventory differs')
    parent = None
    for claim in old:
        name = claim['experiment_id']
        if claim['program_id'] != spec['program_id'] or claim['experiment']['family'] != exp['family'] or canonical(claim['family']) != canonical(family):
            raise ValueError('amendment cannot rename family/program or reset history')
        if name not in spec['experiments'] or canonical(spec['experiments'][name]) != canonical(claim['experiment']):
            raise ValueError('amendment cannot rewrite historical experiment objects')
        directory = root / 'research_runs' / name
        record = inventory[name]
        if set(record) != {'claim_sha256', 'terminal', 'terminal_sha256'} or record['terminal'] not in ('complete.json', 'failed.json'):
            raise ValueError('invalid amendment receipt binding')
        verify_run(directory)
        if sha((directory/'claim.json').read_bytes()) != record['claim_sha256'] or sha((directory/record['terminal']).read_bytes()) != record['terminal_sha256']:
            raise ValueError('amendment prior receipt bytes changed')
        if name == exp['parent']:
            if record['terminal'] != 'failed.json':
                raise ValueError('amendment baseline must be a failed parent')
            parent = claim
    if parent is None:
        raise ValueError('amendment parent absent from complete prior inventory')
    if any(utc(c['started_at']) > utc(parent['started_at']) for c in old):
        raise ValueError('amendment parent must be the latest family attempt')
    parent_registration = json.loads(_git(root, 'show', parent['source'] + ':' + parent['registration']))
    for name, definition in parent_registration['datasets'].items():
        if name not in spec['datasets'] or canonical(spec['datasets'][name]) != canonical(definition):
            raise ValueError('amendment cannot change or remove parent dataset history definitions')
    manifest = json.loads(reference(certificate['economic_manifest']))
    if set(manifest) != {'schema_version','baseline_experiment','economic_source_files','baseline_harness_source_files','target_harness_source_files','experiment_invariants'} or type(manifest['schema_version']) is not int or manifest['schema_version'] != 1 or manifest['baseline_experiment'] != exp['parent']:
        raise ValueError('invalid economic preservation manifest')
    invariant = lambda obj: {k:v for k,v in obj.items() if k not in MUTABLE}
    if canonical(invariant(parent['experiment'])) != canonical(manifest['experiment_invariants']) or canonical(invariant(exp)) != canonical(manifest['experiment_invariants']):
        raise ValueError('economic experiment invariants changed')
    economic = manifest['economic_source_files']
    if not isinstance(economic, dict) or not economic:
        raise ValueError('nonempty preserved economic source manifest required')
    for obj, label in ((parent['experiment'], 'baseline'), (exp, 'target')):
        harness = manifest[label + '_harness_source_files']
        if not isinstance(harness, dict) or set(economic) & set(harness) or canonical({**economic, **harness}) != canonical(obj['source_files']):
            raise ValueError('source partition omits, changes or misclassifies registered files')
    approval = json.loads(reference(certificate['review']))
    if set(approval) != {'decision','target_experiment','increment','target_contract_sha256','economic_manifest_sha256','independent_review'} or approval['decision'] != 'approve-single-amendment' or type(approval['increment']) is not int or approval['increment'] != 1:
        raise ValueError('explicit single-amendment review approval required')
    for field in ('target_experiment','target_contract_sha256'):
        if approval[field] != certificate[field]:
            raise ValueError('review approval target differs')
    if approval['economic_manifest_sha256'] != certificate['economic_manifest']['sha256']:
        raise ValueError('review economic preservation binding differs')
    reference(approval['independent_review'])
    repair = json.loads(reference(certificate['repair_preflight']))
    if set(repair) != {'status','target_experiment','economic_manifest_sha256','reports'} or repair['status'] != 'pass' or repair['target_experiment'] != experiment or repair['economic_manifest_sha256'] != certificate['economic_manifest']['sha256'] or not isinstance(repair['reports'], list) or not repair['reports']:
        raise ValueError('bound passing repair preflight required')
    for report in repair['reports']:
        reference(report)
    return {'certificate': exp['budget_amendment'], 'amendment_id': certificate['amendment_id'],
            'original_budget': family['attempt_budget'], 'effective_budget': family['attempt_budget'] + 1,
            'prior_claim_count': len(old), 'prior_attempts': family['prior_attempts'], 'target_experiment': experiment}
