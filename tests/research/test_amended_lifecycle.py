"""Disposable Git repositories and invented inputs only; no real certificate/run."""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess

import pytest
from tradingagents.research import ResearchRun as OriginalRun, runtime_hashes as original_hashes
from tradingagents.research.verify import verify_run as verify_original
from tradingagents.research_amended import ResearchRun, runtime_hashes
from tradingagents.research_amended.amendment import canonical, MUTABLE
from tradingagents.research_amended.verify import verify_run, verify_claim


def git(root, *args):
    return subprocess.check_output(['git','-c','core.hooksPath=/dev/null',*args], cwd=root, text=True).strip()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(root, name, value):
    (root/name).write_text(json.dumps(value))


def reference(root, name):
    return {'path':name,'sha256':sha((root/name).read_bytes())}


def commit(root):
    git(root,'add','.')
    git(root,'-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid','commit','-qm','synthetic lifecycle')
    return git(root,'rev-parse','HEAD')


def start(root, source, name='amended'):
    return ResearchRun.start(root=root, registration='registration.json', experiment=name, source=source)


def finish(run):
    assert run.read_input('sample') == b'[1]'
    run.write_json('output.json', {'invented':1})
    run.finish([{'id':'case','status':'complete'}])


def rebind(root, spec, cert):
    child=spec['experiments']['amended']
    cert['target_contract_sha256']=sha(canonical({k:v for k,v in child.items() if k!='budget_amendment'}))
    cert['economic_manifest']=reference(root,'economic.json')
    approval=json.loads((root/'approval.json').read_text())
    approval.update(target_contract_sha256=cert['target_contract_sha256'],economic_manifest_sha256=cert['economic_manifest']['sha256'])
    write(root,'approval.json',approval)
    repair=json.loads((root/'repair.json').read_text())
    repair['economic_manifest_sha256']=cert['economic_manifest']['sha256']
    write(root,'repair.json',repair)
    cert['review']=reference(root,'approval.json')
    cert['repair_preflight']=reference(root,'repair.json')
    write(root,'certificate.json',cert)
    child['budget_amendment']=reference(root,'certificate.json')
    write(root,'registration.json',spec)
    return commit(root)


@pytest.fixture
def amendment(tmp_path):
    root=tmp_path
    git(root,'init','-q')
    for name in ('economic.py','old_harness.py','new_harness.py','charter.md','independent-review.md','guard-report.json'):
        (root/name).write_text('Invented fixture '+name)
    (root/'sample.json').write_bytes(b'[1]')
    family={'mechanism_id':'mechanism','attempt_budget':2,'prior_attempts':0,'history_reference':'invented complete prior history'}
    exp={'family':'family','parent':None,'charter':reference(root,'charter.md'),'question':'invented fixed question',
         'stage':'development','reuse':'exploratory','windows':[{'dataset':'sample','start':'2000-01-01T00:00:00Z','end':'2001-01-01T00:00:00Z','availability':'existing'}],
         'inputs':{'sample':{**reference(root,'sample.json'),'dataset':'sample'}},
         'source_files':{name:reference(root,name)['sha256'] for name in ('economic.py','old_harness.py')},
         'runtime_hashes':original_hashes(),'selection':None,'cells':['case'],'outputs':['output.json']}
    spec={'schema_version':1,'program_id':'program','families':{'family':family},
          'datasets':{'sample':{'identity':'invented-sample','history_reference':'invented','exposures':[{'start':'2000-01-01T00:00:00Z','end':'2001-01-01T00:00:00Z','state':'spent'}]}},
          'experiments':{'failed-one':deepcopy(exp)}}
    for name,parent in (('failed-one',None),('failed-two','failed-one')):
        current=deepcopy(exp);current['parent']=parent
        spec['experiments'][name]=current
        write(root,'registration.json',spec)
        source=commit(root)
        run=OriginalRun.start(root=root,registration='registration.json',experiment=name,source=source)
        run.fail('invented harness failure before numerical evaluation')
        assert verify_original(run.directory)['status']=='failed'
    child=deepcopy(spec['experiments']['failed-two']);child['parent']='failed-two'
    child['runtime_hashes']=runtime_hashes()
    child['source_files']={name:reference(root,name)['sha256'] for name in ('economic.py','new_harness.py')}
    spec['experiments']['amended']=child
    manifest={'schema_version':1,'baseline_experiment':'failed-two','economic_source_files':{'economic.py':reference(root,'economic.py')['sha256']},
              'baseline_harness_source_files':{'old_harness.py':reference(root,'old_harness.py')['sha256']},
              'target_harness_source_files':{'new_harness.py':reference(root,'new_harness.py')['sha256']},
              'experiment_invariants':{k:v for k,v in child.items() if k not in MUTABLE}}
    write(root,'economic.json',manifest)
    write(root,'approval.json',{'decision':'approve-single-amendment','target_experiment':'amended','increment':1,'target_contract_sha256':'pending','economic_manifest_sha256':'pending','independent_review':reference(root,'independent-review.md')})
    write(root,'repair.json',{'status':'pass','target_experiment':'amended','economic_manifest_sha256':'pending','reports':[reference(root,'guard-report.json')]})
    cert={'schema_version':1,'amendment_id':'once','program_id':'program','family_id':'family','mechanism_id':'mechanism','family_sha256':sha(canonical(family)),
          'increment':1,'target_experiment':'amended','parent_experiment':'failed-two','target_contract_sha256':'pending','prior_claims':{}}
    for name in ('failed-one','failed-two'):
        directory=root/'research_runs'/name
        cert['prior_claims'][name]={'claim_sha256':sha((directory/'claim.json').read_bytes()),'terminal':'failed.json','terminal_sha256':sha((directory/'failed.json').read_bytes())}
    source=rebind(root,spec,cert)
    return root,spec,cert,source


def test_complete_single_child_and_preserve_original_claims(amendment):
    root,spec,cert,source=amendment
    before={p: p.read_bytes() for p in (root/'research_runs').glob('*/*.json')}
    run=start(root,source);finish(run)
    assert verify_run(run.directory)['status']=='complete'
    assert run.admission.amendment['effective_budget']==3
    assert all(p.read_bytes()==raw for p,raw in before.items())
    assert verify_original(root/'research_runs/failed-two')['status']=='failed'
    with pytest.raises(ValueError,match='repeat'):
        start(root,source)


@pytest.mark.parametrize('value',[0,-1,True,2])
def test_increment_must_be_exact_one(amendment,value):
    root,spec,cert,_=amendment;cert['increment']=value
    with pytest.raises(ValueError,match='exactly one'):
        start(root,rebind(root,spec,cert))


@pytest.mark.parametrize('mutation',['inventory_missing','terminal_hash','family_hash','target','parent','approval','preflight','economic_input','economic_source','parent_rewrite','family_budget','history','empty_economic'])
def test_adversarial_bound_amendments_refused_before_claim(amendment,mutation):
    root,spec,cert,_=amendment
    child=spec['experiments']['amended']
    if mutation=='inventory_missing':cert['prior_claims'].pop('failed-one')
    elif mutation=='terminal_hash':cert['prior_claims']['failed-one']['terminal_sha256']='0'*64
    elif mutation=='family_hash':cert['family_sha256']='0'*64
    elif mutation=='target':cert['target_experiment']='different'
    elif mutation=='parent':cert['parent_experiment']='failed-one'
    elif mutation=='approval':
        value=json.loads((root/'approval.json').read_text());value['decision']='engineering-only';write(root,'approval.json',value)
    elif mutation=='preflight':
        value=json.loads((root/'repair.json').read_text());value['status']='failed';write(root,'repair.json',value)
    elif mutation=='economic_input':child['inputs']['sample']['sha256']='0'*64
    elif mutation=='economic_source':
        (root/'economic.py').write_text('different economics');child['source_files']['economic.py']=reference(root,'economic.py')['sha256']
    elif mutation=='parent_rewrite':spec['experiments']['failed-one']['question']='rewritten'
    elif mutation=='family_budget':spec['families']['family']['attempt_budget']=3
    elif mutation=='history':spec['families']['family']['prior_attempts']=0;spec['families']['family']['history_reference']='reset'
    else:
        value=json.loads((root/'economic.json').read_text());value['economic_source_files']={};write(root,'economic.json',value)
    source=rebind(root,spec,cert)
    with pytest.raises(ValueError):start(root,source)
    assert not (root/'research_runs/amended').exists()


def test_ordinary_budget_path_still_exhausted(amendment):
    root,spec,_,_=amendment
    spec['experiments']['amended'].pop('budget_amendment')
    write(root,'registration.json',spec)
    with pytest.raises(ValueError,match='exhausted'):
        start(root,commit(root))


def test_failed_target_spends_only_increment_and_blocks_chain(amendment):
    root,spec,cert,source=amendment
    run=start(root,source);run.fail('invented second harness failure')
    assert verify_run(run.directory)['status']=='failed'
    with pytest.raises(ValueError,match='repeat'):start(root,source)
    spec['experiments']['another']=deepcopy(spec['experiments']['amended'])
    spec['experiments']['another']['parent']='amended'
    write(root,'registration.json',spec)
    with pytest.raises(ValueError):start(root,commit(root),'another')


def test_concurrent_start_only_one_claim(amendment):
    root,_,_,source=amendment
    def attempt():
        try:return start(root,source)
        except (ValueError,FileExistsError):return None
    with ThreadPoolExecutor(max_workers=2) as pool:runs=list(pool.map(lambda _:attempt(),range(2)))
    winners=[run for run in runs if run is not None]
    assert len(winners)==1
    winners[0].fail('synthetic concurrency test')


def test_revalidate_mutated_evidence_on_every_operation(amendment):
    root,_,_,source=amendment
    run=start(root,source)
    (root/'approval.json').write_text('{}')
    with pytest.raises(ValueError):run.read_input('sample')
    with pytest.raises(ValueError):run.write_json('output.json',{})
    with pytest.raises(ValueError):run.finish([{'id':'case','status':'complete'}])
    assert (run.directory/'failed.json').exists()


def test_independent_verifier_rejects_accounting_tamper(amendment):
    root,_,_,source=amendment
    run=start(root,source);finish(run)
    path=run.directory/'claim.json';claim=json.loads(path.read_text());claim['budget_amendment']['effective_budget']=99;write(run.directory,'claim.json',claim)
    with pytest.raises(ValueError,match='accounting'):verify_claim(run.directory)


def test_uncommitted_certificate_and_claim_only_attempt_are_not_reusable(amendment):
    root,_,_,source=amendment
    path=root/'certificate.json';saved=path.read_bytes();path.write_bytes(saved+b' ')
    with pytest.raises(ValueError,match='committed'):start(root,source)
    path.write_bytes(saved)
    run=start(root,source)
    with pytest.raises(ValueError,match='repeat'):start(root,source)
    assert not (run.directory/'complete.json').exists() and not (run.directory/'failed.json').exists()
    run.fail('synthetic cleanup; interrupted claim remains spent')


def test_chain_certificate_cannot_spend_another_increment(amendment):
    root,spec,cert,source=amendment
    run=start(root,source);run.fail('invented failure')
    child=deepcopy(spec['experiments']['amended']);child['parent']='amended'
    cert=deepcopy(cert);cert.update(target_experiment='chain',parent_experiment='amended',amendment_id='twice')
    cert['target_contract_sha256']=sha(canonical({k:v for k,v in child.items() if k!='budget_amendment'}))
    write(root,'chain-certificate.json',cert);child['budget_amendment']=reference(root,'chain-certificate.json')
    spec['experiments']['chain']=child;write(root,'registration.json',spec)
    with pytest.raises(ValueError,match='chaining'):start(root,commit(root),'chain')


def test_prior_failed_receipt_mutation_rejected_by_independent_verifier(amendment):
    root,_,_,source=amendment
    run=start(root,source);finish(run)
    path=root/'research_runs/failed-one/failed.json'
    data=json.loads(path.read_text());data['reason']='changed history';path.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='receipt binding'):verify_claim(run.directory)


def test_actual_git_lifecycle_under_guard(tmp_path):
    import importlib.util
    import sys
    directory=Path(__file__).resolve().parents[2]/'research/strategy-search-2026-09-11'
    loader=importlib.util.spec_from_file_location('amended_test_guard',directory/'resource_guard_v2.py')
    guard=importlib.util.module_from_spec(loader);loader.loader.exec_module(guard)
    driver=tmp_path/'driver.py'
    driver.write_text('''import importlib.util,json,os
from pathlib import Path
p=Path(__file__).resolve().parent
loader=importlib.util.spec_from_file_location('fixture',TEST_PATH)
m=importlib.util.module_from_spec(loader);loader.loader.exec_module(m)
root,spec,cert,source=m.amendment.__wrapped__(p)
run=m.start(root,source);m.finish(run)
result=m.verify_run(run.directory)
assert result['status']=='complete' and len(os.sched_getaffinity(0))<=2
(p/'synthetic-result.json').write_text(json.dumps({'result':result,'cpus':len(os.sched_getaffinity(0)),'runtime_hashes':m.runtime_hashes()}))
'''.replace('TEST_PATH',repr(str(Path(__file__).resolve()))))
    report=guard.run_guard([sys.executable,'-B',str(driver)])
    write(tmp_path,'guard-report.json',report)
    assert report['child_exit_code']==0 and report['limit_reason'] is None,report
    assert report['rss_limit_bytes']==512*1024**2 and report['wall_limit_seconds']==120
    result=json.loads((tmp_path/'synthetic-result.json').read_text())
    assert result['result']['cell_count']==1 and result['cpus']<=2


@pytest.mark.parametrize('field,value',[('identity','renamed-unexposed'),('history_reference','reset'),('exposures',[])])
def test_dataset_definition_reset_refused_before_claim(amendment,field,value):
    root,spec,cert,_=amendment
    spec['datasets']['sample'][field]=value
    with pytest.raises(ValueError,match='dataset history'):
        start(root,rebind(root,spec,cert))
    assert not (root/'research_runs/amended').exists()


def test_removed_dataset_refused_before_claim(amendment):
    root,spec,cert,_=amendment;spec['datasets'].pop('sample')
    with pytest.raises(ValueError,match='dataset history'):
        start(root,rebind(root,spec,cert))
    assert not (root/'research_runs/amended').exists()


@pytest.mark.parametrize('field,value',[('identity','renamed'),('history_reference','reset'),('exposures',[])])
def test_independent_verifier_rejects_recommitted_dataset_reset(amendment,field,value):
    root,spec,_,source=amendment
    run=start(root,source);finish(run)
    spec['datasets']['sample'][field]=value
    write(root,'registration.json',spec);new_source=commit(root)
    claim=json.loads((run.directory/'claim.json').read_text())
    claim.update(source=new_source,design_source=new_source,registration_sha256=reference(root,'registration.json')['sha256'])
    claim['windows']=[{**w,'identity':spec['datasets'][w['dataset']]['identity'],'state':'exposed'} for w in claim['experiment']['windows']]
    claim['prior_exposures']=[{**row,'identity':info['identity']} for info in spec['datasets'].values() for row in info['exposures']]
    write(run.directory,'claim.json',claim)
    with pytest.raises(ValueError,match='dataset history definition'):
        verify_claim(run.directory)
