"""Independent live-inventory/book-grant reconstruction; no admission imports."""
import hashlib
import json
from datetime import datetime
import re
from tradingagents.research.verify import verify_claim as old_claim,verify_run as old_run
from .verify_v2_snapshot import check as v2_snapshot


def check(directory,claim,registered,blob):
    exp=claim['experiment'];ref=exp.get('budget_book_grant')
    if ref is None:
        if 'budget_book_grant' in claim:raise ValueError('unregistered extension accounting')
        return
    root=directory.parent.parent
    def digest(raw):return hashlib.sha256(raw).hexdigest()
    def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    def evidence(item):
        if not isinstance(item,dict) or set(item)!={'path','sha256'}:raise ValueError('invalid extension artifact reference')
        raw=blob(root,claim['source'],item['path'])
        if digest(raw)!=item['sha256'] or blob(root,claim['design_source'],item['path'])!=raw:raise ValueError('extension committed/design binding changed')
        if (root/item['path']).read_bytes()!=raw:raise ValueError('extension retained artifact changed')
        return raw
    cert=json.loads(evidence(ref));family=claim['family']
    fields={'schema_version','grant_id','program_id','family_id','mechanism_id','family_sha256','increment','original_budget','prior_effective_budget','effective_budget','target_experiment','parent_experiment','target_contract_sha256','prior_claims','consumed_grants','review','preflight','change_manifest'}
    if set(cert)!=fields:raise ValueError('source extension schema mismatch')
    for key,value in [('schema_version',1),('increment',1),('original_budget',4),('prior_effective_budget',6),('effective_budget',7)]:
        if type(cert[key]) is not int or cert[key]!=value:raise ValueError('source extension fixed accounting mismatch')
    if not isinstance(cert['grant_id'],str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}',cert['grant_id']):raise ValueError('extension identifier invalid')
    name=claim['experiment_id']
    if name!='dated-spread-book-20260911' or 'budget_amendment' in exp or 'budget_extension' in exp or type(family['attempt_budget']) is not int or family['attempt_budget']!=4 or type(family['prior_attempts']) is not int or family['prior_attempts']!=1:raise ValueError('named book grant/original family mismatch')
    target={key:value for key,value in exp.items() if key!='budget_book_grant'}
    expected={'program_id':claim['program_id'],'family_id':exp['family'],'mechanism_id':family['mechanism_id'],'family_sha256':digest(encoded(family)),
              'target_experiment':name,'parent_experiment':exp['parent'],'target_contract_sha256':digest(encoded(target))}
    if any(cert[key]!=value for key,value in expected.items()):raise ValueError('extension target identity differs')
    prior={}
    for path in sorted(directory.parent.iterdir()):
        if path.name.startswith('.') or path==directory:continue
        previous=old_claim(path)
        if previous['family']['mechanism_id']==family['mechanism_id']:prior[path.name]=previous
    if len(prior)!=5 or not isinstance(cert['prior_claims'],dict) or set(cert['prior_claims'])!=set(prior):raise ValueError('complete current prior inventory differs')
    if any('budget_book_grant' in previous or 'budget_book_grant' in previous['experiment'] for previous in prior.values()):raise ValueError('duplicate/further source grant')
    repairs=[p for p in prior.values() if 'budget_amendment' in p['experiment']]
    sources=[p for p in prior.values() if 'budget_extension' in p['experiment']]
    if len(repairs)!=1 or len(sources)!=1:raise ValueError('two distinct consumed grants required')
    repair=repairs[0];parent=sources[0]
    if parent['experiment_id']!='dated-mark-20260911' or parent['experiment_id']!=exp['parent']:raise ValueError('named source parent required')
    if any(datetime.fromisoformat(p['started_at'])>datetime.fromisoformat(parent['started_at']) for p in prior.values()):raise ValueError('source parent not latest')
    for registration_path in {p['registration'] for p in prior.values()}:
        baseline_gate=blob(root,parent['source'],registration_path)
        if blob(root,claim['source'],registration_path)!=baseline_gate or blob(root,claim['design_source'],registration_path)!=baseline_gate or (root/registration_path).read_bytes()!=baseline_gate:
            raise ValueError('pre-extension physical registration changed')
    consumed=cert['consumed_grants']
    expected_consumed={'repair':{'experiment_id':repair['experiment_id'],'certificate':repair['experiment']['budget_amendment']},'source':{'experiment_id':parent['experiment_id'],'certificate':parent['experiment']['budget_extension']}}
    if encoded(consumed)!=encoded(expected_consumed):raise ValueError('consumed certificate identity differs')
    for previous_name,previous in prior.items():
        if previous['program_id']!=claim['program_id'] or previous['experiment']['family']!=exp['family'] or encoded(previous['family'])!=encoded(family):raise ValueError('historical identity/budget reset')
        if encoded(registered['experiments'].get(previous_name))!=encoded(previous['experiment']):raise ValueError('rewritten historical contract')
        item=cert['prior_claims'][previous_name];path=directory.parent/previous_name
        if not isinstance(item,dict) or set(item)!={'claim_sha256','terminal','terminal_sha256'} or item['terminal'] not in ('complete.json','failed.json'):raise ValueError('prior receipt reference malformed')
        old_run(path)
        if digest((path/'claim.json').read_bytes())!=item['claim_sha256'] or digest((path/item['terminal']).read_bytes())!=item['terminal_sha256']:raise ValueError('prior receipt hash differs')
        if previous_name==exp['parent'] and item['terminal']!='complete.json':raise ValueError('amended parent must be complete')
        old_spec=json.loads(blob(root,previous['source'],previous['registration']))
        for category in ('families','experiments','datasets'):
            for label,definition in old_spec[category].items():
                if label not in registered[category] or encoded(registered[category][label])!=encoded(definition):raise ValueError('historical '+category+' object changed')
        prior_runtime=previous['experiment']['runtime_hashes']
        prefix='extended/' if 'budget_extension' in previous['experiment'] else 'amended/' if 'budget_amendment' in previous['experiment'] else 'original/'
        for filename,value in prior_runtime.items():
            target_key=filename if filename.startswith(('original/','amended/')) else prefix+filename
            if exp['runtime_hashes'].get(target_key)!=value:raise ValueError('ancestor runtime preservation differs')
        pins=dict(previous['experiment']['source_files'])
        for label in ('charter','selection'):
            if previous['experiment'].get(label):pins[previous['experiment'][label]['path']]=previous['experiment'][label]['sha256']
        for path,expected_sha in pins.items():
            if digest(blob(root,claim['source'],path))!=expected_sha or digest((root/path).read_bytes())!=expected_sha:raise ValueError('historical source artifact changed')
    parent_spec=json.loads(blob(root,parent['source'],parent['registration']))
    v2_snapshot(directory.parent/parent['experiment_id'],parent,parent_spec,blob)
    source_cert=json.loads(evidence(consumed['source']['certificate']))
    if set(source_cert['prior_claims'])!=set(prior)-{parent['experiment_id']}:raise ValueError('closed v2 inventory mismatch')
    if encoded(source_cert['consumed_amendment'])!=encoded(consumed['repair']):raise ValueError('nested repair certificate differs')
    repair_cert=json.loads(evidence(consumed['repair']['certificate']))
    for certificate,keys,report_key in ((source_cert,('review','preflight','change_manifest'),'preflight'),(repair_cert,('review','repair_preflight','economic_manifest'),'repair_preflight')):
        for key in keys:evidence(certificate[key])
        evidence(json.loads(evidence(certificate['review']))['independent_review'])
        for item in json.loads(evidence(certificate[report_key]))['reports']:evidence(item)
    manifest=json.loads(evidence(cert['change_manifest']))
    before=parent['experiment'];differences={}
    for key in sorted(set(before)|set(target)):
        if key not in before or key not in target or encoded(before[key])!=encoded(target[key]):
            differences[key]={'before':{'present':key in before,**({'value':before[key]} if key in before else {})},'after':{'present':key in target,**({'value':target[key]} if key in target else {})}}
    expected_manifest={'schema_version':1,'baseline_experiment':exp['parent'],'target_experiment':name,'baseline_contract_sha256':digest(encoded(before)),'target_contract_sha256':digest(encoded(target)),'changes':differences}
    if encoded(manifest)!=encoded(expected_manifest):raise ValueError('complete explicit change manifest mismatch')
    review=json.loads(evidence(cert['review']))
    if set(review)!={'decision','target_experiment','increment','target_contract_sha256','change_manifest_sha256','prior_claims_sha256','independent_review'} or review['decision']!='approve-single-book-investigation' or type(review['increment']) is not int or review['increment']!=1:raise ValueError('book-specific information-value approval missing')
    if review['target_experiment']!=name or review['target_contract_sha256']!=cert['target_contract_sha256'] or review['change_manifest_sha256']!=cert['change_manifest']['sha256']:raise ValueError('approval target mismatch')
    if review['prior_claims_sha256']!=digest(encoded(cert['prior_claims'])):raise ValueError('approval current inventory differs')
    evidence(review['independent_review'])
    preflight=json.loads(evidence(cert['preflight']))
    if set(preflight)!={'status','target_experiment','change_manifest_sha256','reports'} or preflight['status']!='pass' or preflight['target_experiment']!=name or preflight['change_manifest_sha256']!=cert['change_manifest']['sha256'] or not isinstance(preflight['reports'],list) or not preflight['reports']:raise ValueError('bound passing preflight missing')
    for item in preflight['reports']:evidence(item)
    accounting={'certificate':ref,'grant_id':cert['grant_id'],'original_budget':4,'prior_effective_budget':6,'effective_budget':7,'prior_claim_count':5,'prior_attempts':1,
                'consumed_grants':consumed,'target_experiment':name,'scope':'One named fixed book investigation only; no further investigation or trading-execution authorization.'}
    if encoded(claim.get('budget_book_grant'))!=encoded(accounting):raise ValueError('claim extension accounting mismatch')
