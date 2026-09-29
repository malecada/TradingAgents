"""Synthetic committed extensions; no financial registrations or raw inputs."""
from copy import deepcopy
import hashlib
import json
import pytest
from tests.research.test_lifecycle import registered,start,complete,commit,git
from tradingagents.research.admission import admit
from tradingagents.research.verify import verify_claim


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def closed(fixture,count=3):
    root,spec,source=fixture
    template=deepcopy(spec['experiments']['example-a'])
    for i in range(count):
        name='example-'+chr(ord('a')+i)
        spec['experiments'][name]=deepcopy(template)
        if i:source=commit(root,spec)
        with start((root,spec,source),experiment=name) as run:complete(run)
    return root,spec,source


def extension(fixture,*,initial='example-d',ceiling=4,fault=None,prefix=''):
    root,spec,_=fixture
    exp=deepcopy(spec['experiments']['example-a']);spec['experiments'][initial]=exp
    paths=[]
    def store(name,value):
        name=prefix+name
        p=root/name;p.write_text(json.dumps(value));paths.append(name)
        ref={'path':name,'sha256':sha(p)};exp['source_files'][name]=ref['sha256'];return ref
    allocation=store('allocation.json',{'scope':'synthetic extra failed attempt, no new scientific lane'})
    rows=[]
    for p in sorted((root/'research_runs').glob('*/claim.json')):
        terminals=[q for q in (p.parent/'complete.json',p.parent/'failed.json') if q.exists()]
        assert len(terminals)==1
        rows.append({'experiment':p.parent.name,'claim_sha256':sha(p),'terminal_status':terminals[0].stem,'terminal_sha256':sha(terminals[0])})
    body={'schema_version':1,'program_id':spec['program_id'],'base_family':deepcopy(spec['families']['family-a']),
          'cumulative_ceiling':ceiling,'consumed_before':spec['families']['family-a']['prior_attempts']+len(rows),'initial_experiment':initial,'allocation':allocation,
          'claims':rows,'reason':'Synthetic failed continuation allowance; preserve all prior attempts.'}
    if fault=='missing_claim':body['claims']=rows[:-1];body['consumed_before']-=1
    if fault=='claim_hash':body['claims'][0]['claim_sha256']='0'*64
    if fault=='terminal_hash':body['claims'][0]['terminal_sha256']='0'*64
    if fault=='history':body['base_family']['prior_attempts']=1
    if fault=='boolean_ceiling':body['cumulative_ceiling']=True
    if fault=='wrong_adopter':body['initial_experiment']='example-z'
    core=store('extension.json',body)
    review=store('extension-review.json',{'schema_version':1,'decision':'rejected' if fault=='rejected_review' else 'accepted',
        'extension_sha256':'0'*64 if fault=='review_hash' else core['sha256'],'reviewer':'synthetic-independent-fixture','scope':'budget only; no empirical release'})
    exp['cumulative_budget_extension']={'extension':core,'review':review}
    if fault=='unpinned':exp['source_files'].pop('extension-review.json')
    git(root,'add',*paths);source=commit(root,spec)
    return root,spec,source


def test_reviewed_extension_preserves_family_and_spends_failed_allowance(registered):
    fixture=extension(closed(registered));root,spec,source=fixture
    frozen={p: p.read_bytes() for p in (root/'research_runs').glob('*/*.json')}
    with pytest.raises(RuntimeError,match='synthetic failure'):
        with start(fixture,experiment='example-d') as run:
            assert run.admission.effective_attempt_budget==4
            raise RuntimeError('synthetic failure after claim')
    claim=verify_claim(root/'research_runs/example-d')
    assert claim['effective_attempt_budget']==4
    assert claim['family']==spec['families']['family-a'] and claim['family']['attempt_budget']==3
    assert all(p.read_bytes()==raw for p,raw in frozen.items())
    spec['experiments']['example-e']=deepcopy(spec['experiments']['example-d']);source=commit(root,spec)
    with pytest.raises(ValueError,match='budget exhausted'):
        admit(root=root,registration='registration.json',experiment='example-e',source=source)
    assert not (root/'research_runs/example-e').exists()


@pytest.mark.parametrize('fault',['missing_claim','claim_hash','terminal_hash','history','boolean_ceiling','wrong_adopter','rejected_review','review_hash','unpinned'])
def test_bad_extensions_refused_even_before_original_budget_is_spent(registered,fault):
    fixture=extension(closed(registered,1),fault=fault);root,_,_=fixture
    with pytest.raises(ValueError,match='extension|review|snapshot|budget'):
        start(fixture,experiment='example-d')
    assert not (root/'research_runs/example-d').exists()


def test_snapshot_cannot_omit_new_closed_claim_before_first_adoption(registered):
    fixture=extension(closed(registered,1));root,spec,_=fixture
    spec['experiments']['example-b']=deepcopy(spec['experiments']['example-a']);source=commit(root,spec)
    with start((root,spec,source),experiment='example-b') as run:complete(run)
    with pytest.raises(ValueError,match='snapshot'):
        start((root,spec,source),experiment='example-d')
    assert not (root/'research_runs/example-d').exists()


def test_later_claims_must_carry_extension_and_verifier_checks_effective_ceiling(registered):
    fixture=extension(closed(registered,1));root,spec,source=fixture
    with start(fixture,experiment='example-d') as run:complete(run)
    p=root/'research_runs/example-d/claim.json';original=p.read_bytes();claim=json.loads(original);claim['effective_attempt_budget']=500;p.write_text(json.dumps(claim))
    with pytest.raises(ValueError,match='budget|ceiling'):verify_claim(p.parent)
    p.write_bytes(original)
    spec['experiments']['example-e']=deepcopy(spec['experiments']['example-a']);source=commit(root,spec)
    with pytest.raises(ValueError,match='extension'):
        start((root,spec,source),experiment='example-e')
    spec['experiments']['example-e']=deepcopy(spec['experiments']['example-d']);source=commit(root,spec)
    with start((root,spec,source),experiment='example-e') as run:complete(run)
    assert verify_claim(root/'research_runs/example-e')['effective_attempt_budget']==4


def test_historical_attempts_are_counted_without_rewriting_family(registered):
    root,spec,_=registered
    spec['families']['family-a'].update(prior_attempts=17,attempt_budget=18)
    fixture=extension(closed((root,spec,commit(root,spec)),1),ceiling=19)
    with start(fixture,experiment='example-d') as run:complete(run)
    spec['experiments']['example-e']=deepcopy(spec['experiments']['example-d'])
    with pytest.raises(ValueError,match='budget exhausted'):
        start((root,spec,commit(root,spec)),experiment='example-e')
    assert verify_claim(root/'research_runs/example-d')['family']['prior_attempts']==17


@pytest.mark.parametrize('include_live',[False,True])
def test_first_extension_requires_all_claims_closed(registered,include_live):
    fixture=extension(closed(registered,1));root,spec,_=fixture
    spec['experiments']['example-b']=deepcopy(spec['experiments']['example-a'])
    source=commit(root,spec)
    live=start((root,spec,source),experiment='example-b')
    try:
        if include_live:
            p=root/'extension.json';body=json.loads(p.read_bytes())
            body['claims'].append({'experiment':'example-b','claim_sha256':sha(live.directory/'claim.json'),
                                  'terminal_status':'complete','terminal_sha256':'0'*64})
            body['consumed_before']+=1;p.write_text(json.dumps(body))
            review=root/'extension-review.json';value=json.loads(review.read_bytes())
            value['extension_sha256']=sha(p);review.write_text(json.dumps(value))
            exp=spec['experiments']['example-d']
            for kind,path in [('extension',p),('review',review)]:
                exp['cumulative_budget_extension'][kind]['sha256']=sha(path);exp['source_files'][path.name]=sha(path)
            git(root,'add',p.name,review.name);source=commit(root,spec)
        with pytest.raises(ValueError,match='snapshot'):
            start((root,spec,source),experiment='example-d')
        assert not (root/'research_runs/example-d').exists()
    finally:
        live.fail('synthetic active-owner fixture cleanup')


def test_second_extension_preserves_first_and_blocks_rollback(registered):
    fixture=extension(closed(registered,1));root,spec,_=fixture
    with start(fixture,experiment='example-d') as run:complete(run)
    old=(root/'research_runs/example-d/claim.json').read_bytes()
    fixture=extension(fixture,initial='example-e',ceiling=5,prefix='second-')
    body=json.loads((root/'second-extension.json').read_bytes())
    assert {c['experiment'] for c in body['claims']}=={'example-a','example-d'}
    with start(fixture,experiment='example-e') as run:complete(run)
    assert (root/'research_runs/example-d/claim.json').read_bytes()==old
    spec['experiments']['example-f']=deepcopy(spec['experiments']['example-d'])
    with pytest.raises(ValueError,match='retain adopted ceiling'):
        start((root,spec,commit(root,spec)),experiment='example-f')
    spec['experiments']['example-f']=deepcopy(spec['experiments']['example-e'])
    with start((root,spec,commit(root,spec)),experiment='example-f') as run:complete(run)
    assert verify_claim(root/'research_runs/example-f')['effective_attempt_budget']==5


@pytest.mark.parametrize('kind',['extension','review','allocation'])
def test_metadata_drift_refused_before_claim(registered,kind):
    fixture=extension(closed(registered,1));root,_,_=fixture
    p=root/({'review':'extension-review.json'}.get(kind,kind+'.json'))
    p.write_bytes(p.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='committed source differs'):
        start(fixture,experiment='example-d')
    assert not (root/'research_runs/example-d').exists()


def test_other_mechanism_is_not_charged_for_extension(registered):
    fixture=extension(closed(registered,1));root,spec,_=fixture
    with start(fixture,experiment='example-d') as run:complete(run)
    spec['families']['family-b']={**spec['families']['family-a'],'mechanism_id':'other-mechanism','attempt_budget':1}
    spec['experiments']['other-a']={**deepcopy(spec['experiments']['example-a']),'family':'family-b'}
    with start((root,spec,commit(root,spec)),experiment='other-a') as run:complete(run)
    assert verify_claim(root/'research_runs/other-a')['effective_attempt_budget']==1


def test_historical_custom_certificate_remains_readable(registered):
    root,spec,_=registered
    # Same shape as the separately implemented dated-mark historical certificate.
    # This pre-existing metadata field does not opt in to the new generic ceiling.
    p=root/'legacy-certificate.json';p.write_text('{"status":"synthetic legacy certificate"}')
    spec['experiments']['example-a']['budget_extension']={'path':p.name,'sha256':sha(p)}
    spec['experiments']['example-a']['source_files'][p.name]=sha(p)
    git(root,'add',p.name)
    fixture=(root,spec,commit(root,spec))
    with start(fixture) as run:complete(run)
    assert verify_claim(root/'research_runs/example-a')['effective_attempt_budget']==3
