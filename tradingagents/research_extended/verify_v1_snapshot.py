"""Frozen v1 rules reconstructed at its closed inventory; never grants later attempts.

Derived from research_amended/verify_amendment.py, preserved unchanged.
Unlike its live-ledger scan, later claims remain visible but outside the historical
snapshot. The separate extension checker must bind the entire current inventory.
"""
import hashlib
from datetime import datetime
import json
import re
from tradingagents.research.verify import verify_claim as original_claim, verify_run as original_run


def check(directory, claim, registered, blob):
    root = directory.parent.parent
    exp = claim['experiment']
    ref = exp.get('budget_amendment')
    if ref is None:
        if 'budget_amendment' in claim:
            raise ValueError('unregistered amendment accounting in claim')
        return
    def digest(raw):
        return hashlib.sha256(raw).hexdigest()
    def encoded(value):
        return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    def evidence(item):
        if not isinstance(item, dict) or set(item) != {'path','sha256'}:
            raise ValueError('invalid amendment evidence reference')
        raw = blob(root, claim['source'], item['path'])
        if digest(raw) != item['sha256'] or blob(root, claim['design_source'], item['path']) != raw:
            raise ValueError('amendment evidence hash/design mismatch')
        return raw
    cert = json.loads(evidence(ref))
    fields = {'schema_version','amendment_id','program_id','family_id','mechanism_id','family_sha256','increment','target_experiment','parent_experiment','target_contract_sha256','prior_claims','review','repair_preflight','economic_manifest'}
    if set(cert) != fields or type(cert['schema_version']) is not int or cert['schema_version'] != 1 or type(cert['increment']) is not int or cert['increment'] != 1:
        raise ValueError('invalid single increment certificate')
    if not isinstance(cert['amendment_id'], str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}', cert['amendment_id']):
        raise ValueError('invalid amendment identifier')
    family = claim['family']
    expected = {'program_id':claim['program_id'],'family_id':exp['family'],'mechanism_id':family['mechanism_id'],
                'family_sha256':digest(encoded(family)),'target_experiment':claim['experiment_id'],
                'parent_experiment':exp['parent'],'target_contract_sha256':digest(encoded({k:v for k,v in exp.items() if k!='budget_amendment'}))}
    if any(cert[key] != value for key,value in expected.items()):
        raise ValueError('amendment identity/contract reconstruction differs')
    previous = {}
    if not isinstance(cert['prior_claims'],dict):raise ValueError('invalid closed v1 inventory')
    for name in cert['prior_claims']:
        if not isinstance(name,str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}',name):raise ValueError('invalid closed v1 identity')
    for child in sorted(directory.parent.iterdir()):
        if child.name.startswith('.') or child == directory:
            continue
        previous_claim = original_claim(child)
        if previous_claim['family']['mechanism_id'] != family['mechanism_id']:continue
        if child.name not in cert['prior_claims']:
            if datetime.fromisoformat(previous_claim['started_at']) <= datetime.fromisoformat(claim['started_at']):
                raise ValueError('unbound claim predates closed v1 snapshot')
            continue  # Explicit later live claim; grants verified separately, never silently reusable.
        if 'budget_amendment' in previous_claim['experiment'] or 'budget_amendment' in previous_claim or 'budget_extension' in previous_claim['experiment'] or 'budget_extension' in previous_claim:
            raise ValueError('closed v1 inventory contains an extension')
        previous[child.name]=previous_claim
    if set(cert['prior_claims']) != set(previous) or len(previous)+family['prior_attempts'] != family['attempt_budget']:
        raise ValueError('amendment inventory or original budget differs')
    parent = None
    for name, old in previous.items():
        if old['program_id'] != claim['program_id'] or old['experiment']['family'] != exp['family'] or encoded(old['family']) != encoded(family):
            raise ValueError('historical family/program reset')
        if name not in registered['experiments'] or encoded(registered['experiments'][name]) != encoded(old['experiment']):
            raise ValueError('historical experiment rewritten')
        item = cert['prior_claims'][name]
        if set(item) != {'claim_sha256','terminal','terminal_sha256'} or item['terminal'] not in ('failed.json','complete.json'):
            raise ValueError('invalid prior terminal binding')
        olddir = directory.parent/name
        original_run(olddir)
        if digest((olddir/'claim.json').read_bytes()) != item['claim_sha256'] or digest((olddir/item['terminal']).read_bytes()) != item['terminal_sha256']:
            raise ValueError('prior receipt binding mismatch')
        if name == exp['parent']:
            if item['terminal'] != 'failed.json':
                raise ValueError('baseline is not failed')
            parent = old
    if parent is None:
        raise ValueError('amendment parent absent')
    if any(datetime.fromisoformat(c['started_at']) > datetime.fromisoformat(parent['started_at']) for c in previous.values()):
        raise ValueError('amendment parent is not latest family attempt')
    prior_registration = json.loads(blob(root, parent['source'], parent['registration']))
    for label, definition in prior_registration['datasets'].items():
        if label not in registered['datasets'] or encoded(registered['datasets'][label]) != encoded(definition):
            raise ValueError('parent dataset history definition changed or removed')
    manifest = json.loads(evidence(cert['economic_manifest']))
    if set(manifest) != {'schema_version','baseline_experiment','economic_source_files','baseline_harness_source_files','target_harness_source_files','experiment_invariants'} or type(manifest['schema_version']) is not int or manifest['schema_version'] != 1 or manifest['baseline_experiment'] != exp['parent']:
        raise ValueError('economic manifest schema/baseline differs')
    mutable = {'parent','charter','question','source_files','runtime_hashes','outputs','budget_amendment'}
    economic = manifest['economic_source_files']
    if not isinstance(economic, dict) or not economic:
        raise ValueError('empty preserved economic manifest')
    for contract, label in ((parent['experiment'],'baseline'), (exp,'target')):
        if encoded({k:v for k,v in contract.items() if k not in mutable}) != encoded(manifest['experiment_invariants']):
            raise ValueError('economic invariant changed')
        harness = manifest[label+'_harness_source_files']
        if not isinstance(harness, dict) or set(harness)&set(economic) or encoded({**economic,**harness}) != encoded(contract['source_files']):
            raise ValueError('source partition differs')
    review = json.loads(evidence(cert['review']))
    if set(review) != {'decision','target_experiment','increment','target_contract_sha256','economic_manifest_sha256','independent_review'} or review['decision'] != 'approve-single-amendment' or type(review['increment']) is not int or review['increment'] != 1:
        raise ValueError('single attempt review missing')
    if review['target_experiment'] != claim['experiment_id'] or review['target_contract_sha256'] != cert['target_contract_sha256'] or review['economic_manifest_sha256'] != cert['economic_manifest']['sha256']:
        raise ValueError('review binds different target/economics')
    evidence(review['independent_review'])
    repair = json.loads(evidence(cert['repair_preflight']))
    if set(repair) != {'status','target_experiment','economic_manifest_sha256','reports'} or repair['status'] != 'pass' or repair['target_experiment'] != claim['experiment_id'] or repair['economic_manifest_sha256'] != cert['economic_manifest']['sha256'] or not isinstance(repair['reports'],list) or not repair['reports']:
        raise ValueError('repair evidence is not bound passing preflight')
    for report in repair['reports']:
        evidence(report)
    accounting = {'certificate':ref,'amendment_id':cert['amendment_id'],'original_budget':family['attempt_budget'],
                  'effective_budget':family['attempt_budget']+1,'prior_claim_count':len(previous),
                  'prior_attempts':family['prior_attempts'],'target_experiment':claim['experiment_id']}
    if encoded(claim.get('budget_amendment')) != encoded(accounting):
        raise ValueError('saved amendment accounting differs')
