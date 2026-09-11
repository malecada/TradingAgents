"""One fixed book question after two consumed grants; no general budget mechanism."""
import hashlib
import json

TARGET='dated-spread-book-20260911'
FIELDS={'schema_version','grant_id','program_id','family_id','mechanism_id','family_sha256','increment',
        'original_budget','prior_effective_budget','effective_budget','target_experiment','parent_experiment',
        'target_contract_sha256','prior_claims','consumed_grants','review','preflight','change_manifest'}


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def changes(before,after):
    return {key:{'before':{'present':key in before,**({'value':before[key]} if key in before else {})},
                 'after':{'present':key in after,**({'value':after[key]} if key in after else {})}}
            for key in sorted(set(before)|set(after)) if key not in before or key not in after or canonical(before[key])!=canonical(after[key])}


def validate(*,root,source,design_source,spec,experiment,relevant,own_claim,committed):
    from .admission import identity,utc,_git
    from tradingagents.research.verify import verify_run as structural_run
    from .verify_v2_snapshot import check as snapshot
    from .verify import _blob
    exp=spec['experiments'][experiment];family=spec['families'][exp['family']]
    def reference(ref):
        if not isinstance(ref,dict) or set(ref)!={'path','sha256'}:raise ValueError('extension artifact requires exact path/hash')
        raw=committed(root,source,ref['path'],ref['sha256'])
        if committed(root,design_source,ref['path'],ref['sha256'])!=raw:raise ValueError('extension design artifact differs')
        return raw
    cert=json.loads(reference(exp['budget_book_grant']))
    if set(cert)!=FIELDS:raise ValueError('extension certificate schema')
    for key,value in {'schema_version':1,'increment':1,'original_budget':4,'prior_effective_budget':6,'effective_budget':7}.items():
        if type(cert[key]) is not int or cert[key]!=value:raise ValueError('fixed extension accounting required')
    identity(cert['grant_id'],'extension')
    if experiment!=TARGET or 'budget_amendment' in exp or 'budget_extension' in exp:raise ValueError('only named book target receives grant')
    if type(family['attempt_budget']) is not int or family['attempt_budget']!=4 or type(family['prior_attempts']) is not int or family['prior_attempts']!=1:raise ValueError('original4/prior1 family must remain unchanged')
    target={key:value for key,value in exp.items() if key!='budget_book_grant'}
    expected={'program_id':spec['program_id'],'family_id':exp['family'],'mechanism_id':family['mechanism_id'],'family_sha256':sha(canonical(family)),
              'target_experiment':TARGET,'parent_experiment':exp['parent'],'target_contract_sha256':sha(canonical(target))}
    if any(cert[key]!=value for key,value in expected.items()):raise ValueError('extension identity/target binding differs')
    old=[claim for claim in relevant if claim['experiment_id']!=own_claim]
    if len(old)!=5 or len(old)+family['prior_attempts']!=6:raise ValueError('current inventory must contain exactly5 prior program claims plus historical1')
    if any('budget_book_grant' in claim['experiment'] or 'budget_book_grant' in claim for claim in old):raise ValueError('further extension/chaining prohibited')
    inventory=cert['prior_claims']
    if not isinstance(inventory,dict) or set(inventory)!={claim['experiment_id'] for claim in old}:raise ValueError('live historical inventory differs')
    amended=[claim for claim in old if 'budget_amendment' in claim['experiment']]
    source_claims=[claim for claim in old if 'budget_extension' in claim['experiment']]
    if len(amended)!=1 or len(source_claims)!=1:raise ValueError('exactly one consumed repair and source grant required')
    repair=amended[0];parent=source_claims[0]
    if parent['experiment_id']!='dated-mark-20260911' or parent['experiment_id']!=exp['parent'] or any(utc(c['started_at'])>utc(parent['started_at']) for c in old):raise ValueError('latest completed dated-mark parent required')
    for registration_path in {c['registration'] for c in old}:
        baseline_gate=_git(root,'show',parent['source']+':'+registration_path)
        committed(root,source,registration_path,sha(baseline_gate))
        committed(root,design_source,registration_path,sha(baseline_gate))
    consumed=cert['consumed_grants']
    expected_consumed={'repair':{'experiment_id':repair['experiment_id'],'certificate':repair['experiment']['budget_amendment']},
                       'source':{'experiment_id':parent['experiment_id'],'certificate':parent['experiment']['budget_extension']}}
    if canonical(consumed)!=canonical(expected_consumed):raise ValueError('two consumed certificate bindings differ')
    for claim in old:
        name=claim['experiment_id'];directory=root/'research_runs'/name
        if claim['program_id']!=spec['program_id'] or claim['experiment']['family']!=exp['family'] or canonical(claim['family'])!=canonical(family):raise ValueError('historical family/program reset')
        if canonical(spec['experiments'].get(name))!=canonical(claim['experiment']):raise ValueError('historical experiment changed')
        item=inventory[name]
        if not isinstance(item,dict) or set(item)!={'claim_sha256','terminal','terminal_sha256'} or item['terminal'] not in ('complete.json','failed.json'):raise ValueError('historical terminal schema')
        structural_run(directory)
        if sha((directory/'claim.json').read_bytes())!=item['claim_sha256'] or sha((directory/item['terminal']).read_bytes())!=item['terminal_sha256']:raise ValueError('historical receipt changed')
        if name==exp['parent'] and item['terminal']!='complete.json':raise ValueError('book grant requires completed source parent')
        prior_spec=json.loads(_git(root,'show',claim['source']+':'+claim['registration']))
        for collection in ('families','experiments','datasets'):
            for key,value in prior_spec[collection].items():
                if key not in spec[collection] or canonical(spec[collection][key])!=canonical(value):raise ValueError('historical '+collection+' object changed or removed')
        for key,digest in claim['experiment']['runtime_hashes'].items():
            mapped=key if key.startswith(('original/','amended/')) else ('extended/' if 'budget_extension' in claim['experiment'] else 'amended/' if 'budget_amendment' in claim['experiment'] else 'original/')+key
            if exp['runtime_hashes'].get(mapped)!=digest:raise ValueError('frozen ancestor runtime hash changed')
        # Historical code/charter/selection bytes remain available unchanged, not merely in Git.
        pinned=dict(claim['experiment']['source_files'])
        for key in ('charter','selection'):
            if claim['experiment'].get(key):pinned[claim['experiment'][key]['path']]=claim['experiment'][key]['sha256']
        for path,digest in pinned.items():committed(root,source,path,digest)
    parent_spec=json.loads(_git(root,'show',parent['source']+':'+parent['registration']))
    snapshot(root/'research_runs'/parent['experiment_id'],parent,parent_spec,_blob)
    source_cert=json.loads(reference(consumed['source']['certificate']))
    if set(source_cert['prior_claims'])!={c['experiment_id'] for c in old if c is not parent}:raise ValueError('closed v2 inventory differs from all live predecessors')
    if canonical(source_cert['consumed_amendment'])!=canonical(consumed['repair']):raise ValueError('nested repair binding differs')
    old_cert=json.loads(reference(consumed['repair']['certificate']))
    for certificate,fields,report_key in ((source_cert,('review','preflight','change_manifest'),'preflight'),(old_cert,('review','repair_preflight','economic_manifest'),'repair_preflight')):
        for key in fields:reference(certificate[key])
        reference(json.loads(reference(certificate['review']))['independent_review'])
        for report in json.loads(reference(certificate[report_key]))['reports']:reference(report)
    manifest=json.loads(reference(cert['change_manifest']))
    baseline=parent['experiment']
    expected_manifest={'schema_version':1,'baseline_experiment':exp['parent'],'target_experiment':TARGET,
                       'baseline_contract_sha256':sha(canonical(baseline)),'target_contract_sha256':sha(canonical(target)),
                       'changes':changes(baseline,target)}
    if canonical(manifest)!=canonical(expected_manifest):raise ValueError('explicit complete target change manifest differs')
    review=json.loads(reference(cert['review']))
    if set(review)!={'decision','target_experiment','increment','target_contract_sha256','change_manifest_sha256','prior_claims_sha256','independent_review'} or review['decision']!='approve-single-book-investigation' or type(review['increment']) is not int or review['increment']!=1:raise ValueError('explicit book-specific information-value approval required')
    if review['target_experiment']!=TARGET or review['target_contract_sha256']!=cert['target_contract_sha256'] or review['change_manifest_sha256']!=cert['change_manifest']['sha256']:raise ValueError('information-value approval target differs')
    if review['prior_claims_sha256']!=sha(canonical(inventory)):raise ValueError('approval current inventory binding differs')
    reference(review['independent_review'])
    preflight=json.loads(reference(cert['preflight']))
    if set(preflight)!={'status','target_experiment','change_manifest_sha256','reports'} or preflight['status']!='pass' or preflight['target_experiment']!=TARGET or preflight['change_manifest_sha256']!=cert['change_manifest']['sha256'] or not isinstance(preflight['reports'],list) or not preflight['reports']:raise ValueError('passing target-bound preflight required')
    for report in preflight['reports']:reference(report)
    return {'certificate':exp['budget_book_grant'],'grant_id':cert['grant_id'],'original_budget':4,'prior_effective_budget':6,'effective_budget':7,
            'prior_claim_count':5,'prior_attempts':1,'consumed_grants':consumed,'target_experiment':TARGET,
            'scope':'One named fixed book investigation only; no further investigation or trading-execution authorization.'}
