"""Synthetic seventh-attempt gate; no financial inputs or arithmetic."""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import pytest
from tradingagents.research_spread import ResearchRun,runtime_hashes
from tradingagents.research_spread.grant import TARGET,canonical,changes
from tradingagents.research_spread.verify import verify_run
from tradingagents.research_extended.verify import verify_run as frozen_v2_verify
from tradingagents.research_amended.verify import verify_run as frozen_v1_verify


def previous_fixture():
    spec=importlib.util.spec_from_file_location('preserved_extension_fixture',Path(__file__).with_name('test_extended_lifecycle.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def sha(raw):return hashlib.sha256(raw).hexdigest()
def write(root,name,value):(root/name).write_text(json.dumps(value))
def ref(root,name):return {'path':name,'sha256':sha((root/name).read_bytes())}
def git(root,*args):return subprocess.check_output(['git','-c','core.hooksPath=/dev/null',*args],cwd=root,text=True).strip()
def commit(root):
    git(root,'add','.')
    git(root,'-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid','commit','-qm','invented spread lifecycle')
    return git(root,'rev-parse','HEAD')


def rebind_spread(root,spec,cert):
    target={key:value for key,value in spec['experiments'][TARGET].items() if key!='budget_book_grant'}
    baseline=spec['experiments'][cert['parent_experiment']]
    manifest={'schema_version':1,'baseline_experiment':cert['parent_experiment'],'target_experiment':TARGET,'baseline_contract_sha256':sha(canonical(baseline)),
              'target_contract_sha256':sha(canonical(target)),'changes':changes(baseline,target)}
    write(root,'spread-changes.json',manifest);cert['target_contract_sha256']=manifest['target_contract_sha256'];cert['change_manifest']=ref(root,'spread-changes.json')
    write(root,'spread-approval.json',{'decision':'approve-single-book-investigation','target_experiment':TARGET,'increment':1,'target_contract_sha256':cert['target_contract_sha256'],
          'change_manifest_sha256':cert['change_manifest']['sha256'],'prior_claims_sha256':sha(canonical(cert['prior_claims'])),'independent_review':ref(root,'spread-review.md')})
    write(root,'spread-preflight.json',{'status':'pass','target_experiment':TARGET,'change_manifest_sha256':cert['change_manifest']['sha256'],'reports':[ref(root,'spread-report.json')]})
    cert['review']=ref(root,'spread-approval.json');cert['preflight']=ref(root,'spread-preflight.json')
    write(root,'spread-certificate.json',cert);spec['experiments'][TARGET]['budget_book_grant']=ref(root,'spread-certificate.json')
    write(root,'spread-registration.json',spec);return commit(root)


def build_spread(root,*,target_updates=None,datasets=None):
    """Build five invented predecessors; preserve caller files for exact CLI tests."""
    previous=previous_fixture();root,spec,source_cert,source=previous.build_extension(root)
    run=previous.start(root,source);previous.finish(run)
    assert frozen_v2_verify(run.directory)['status']=='complete'
    for name in ('synthetic-book.py','spread-review.md','spread-report.json'):(root/name).write_text('Invented '+name)
    target=deepcopy(spec['experiments'][previous.TARGET]);del target['budget_extension']
    target.update(parent=previous.TARGET,question='invented fixed book contract, no financial evaluation',runtime_hashes=runtime_hashes(),source_files={'synthetic-book.py':ref(root,'synthetic-book.py')['sha256']})
    if target_updates:target.update(deepcopy(target_updates))
    if datasets:
        if set(datasets)&set(spec['datasets']):raise ValueError('fixture dataset replacement prohibited')
        spec['datasets'].update(deepcopy(datasets))
    spec['experiments'][TARGET]=target
    inventory=deepcopy(source_cert['prior_claims']);inventory[previous.TARGET]={'claim_sha256':sha((run.directory/'claim.json').read_bytes()),'terminal':'complete.json','terminal_sha256':sha((run.directory/'complete.json').read_bytes())}
    cert={'schema_version':1,'grant_id':'invented-book-grant','program_id':spec['program_id'],'family_id':'dated','mechanism_id':spec['families']['dated']['mechanism_id'],'family_sha256':sha(canonical(spec['families']['dated'])),
          'increment':1,'original_budget':4,'prior_effective_budget':6,'effective_budget':7,'target_experiment':TARGET,'parent_experiment':previous.TARGET,'prior_claims':inventory,
          'consumed_grants':{'repair':deepcopy(source_cert['consumed_amendment']),'source':{'experiment_id':previous.TARGET,'certificate':deepcopy(spec['experiments'][previous.TARGET]['budget_extension'])}}}
    source=rebind_spread(root,spec,cert)
    return root,spec,cert,source


@pytest.fixture
def spread(tmp_path):return build_spread(tmp_path)
def start(root,source,name=TARGET):return ResearchRun.start(root=root,registration='spread-registration.json',experiment=name,source=source)
def finish(run):
    assert run.read_input('sample')==b'[1]'
    run.write_json('output.json',{'invented':3});run.finish([{'id':'case','status':'complete'}])


def test_seventh_claim_and_nested_closed_certificates(spread):
    root,spec,cert,source=spread
    saved={str(p.relative_to(root)):sha(p.read_bytes()) for p in (root/'research_runs').rglob('*') if p.is_file()}
    run=start(root,source);finish(run)
    assert verify_run(run.directory)['status']=='complete'
    assert verify_run(root/'research_runs/dated-mark-20260911')['status']=='complete'
    assert verify_run(root/'research_runs/repair')['status']=='complete'
    with pytest.raises(ValueError):frozen_v2_verify(root/'research_runs/dated-mark-20260911')
    with pytest.raises(ValueError):frozen_v1_verify(root/'research_runs/repair')
    assert all(sha((root/p).read_bytes())==digest for p,digest in saved.items())
    claim=json.loads((run.directory/'claim.json').read_text())
    assert claim['budget_book_grant']['effective_budget']==7 and len(cert['prior_claims'])==5
    with pytest.raises(ValueError):start(root,source)


@pytest.mark.parametrize('change',['increment','target','parent','missing-history','consumed','unrun','family','dataset','physical-gate','runtime'])
def test_preclaim_adversarial_changes(spread,change):
    root,spec,cert,source=spread
    if change=='increment':cert['increment']=True
    elif change=='target':cert['target_experiment']='other'
    elif change=='parent':spec['experiments'][TARGET]['parent']='repair';cert['parent_experiment']='repair'
    elif change=='missing-history':del cert['prior_claims']['original-a']
    elif change=='consumed':cert['consumed_grants']['source']['experiment_id']='repair'
    elif change=='unrun':del spec['experiments']['unrun-baseline']
    elif change=='family':spec['families']['unrelated']['history_reference']='reset'
    elif change=='dataset':spec['datasets']['sample']['identity']='reset'
    elif change=='physical-gate':(root/'extension-registration.json').write_text('{}')
    elif change=='runtime':spec['experiments'][TARGET]['runtime_hashes']['extended/admission.py']='0'*64
    source=rebind_spread(root,spec,cert)
    with pytest.raises(ValueError):start(root,source)
    assert not (root/'research_runs'/TARGET).exists()


def test_no_certificate_and_failed_grant_cannot_repeat(spread):
    root,spec,cert,source=spread;del spec['experiments'][TARGET]['budget_book_grant'];write(root,'spread-registration.json',spec);source=commit(root)
    with pytest.raises(ValueError,match='exhausted'):start(root,source)
    source=rebind_spread(root,spec,cert);run=start(root,source);run.fail('invented failure')
    assert verify_run(run.directory)['status']=='failed'
    with pytest.raises(ValueError):start(root,source)


def test_concurrent_claim_and_no_eighth(spread):
    root,spec,cert,source=spread
    def attempt():
        try:return start(root,source)
        except (ValueError,FileExistsError):return None
    with ThreadPoolExecutor(max_workers=2) as pool:attempts=list(pool.map(lambda _:attempt(),range(2)))
    winners=[run for run in attempts if run];assert len(winners)==1;finish(winners[0])
    later=deepcopy(spec['experiments'][TARGET]);later['parent']=TARGET;spec['experiments']['eighth']=later
    write(root,'spread-registration.json',spec);source=commit(root)
    with pytest.raises(ValueError):start(root,source,'eighth')


@pytest.mark.parametrize('operation',['read','write','finish'])
def test_every_operation_revalidates(spread,operation):
    root,spec,cert,source=spread;run=start(root,source);(root/'spread-review.md').write_text('changed')
    with pytest.raises(ValueError):
        if operation=='read':run.read_input('sample')
        elif operation=='write':run.write_json('output.json',{})
        else:run.finish([{'id':'case','status':'unavailable','reason':'invented'}])


@pytest.mark.parametrize('mutation',['unrun','runtime','dataset','physical','approval'])
def test_independent_recommitted_tamper(spread,mutation):
    root,spec,cert,source=spread;run=start(root,source);finish(run)
    claim=json.loads((run.directory/'claim.json').read_text())
    if mutation=='unrun':del spec['experiments']['unrun-baseline']
    elif mutation=='runtime':spec['experiments'][TARGET]['runtime_hashes']['extended/admission.py']='0'*64
    elif mutation=='dataset':spec['datasets']['sample']['identity']='reset'
    elif mutation=='physical':(root/'extension-registration.json').write_text('{}')
    source=rebind_spread(root,spec,cert)
    if mutation=='approval':
        value=json.loads((root/'spread-approval.json').read_text());value['prior_claims_sha256']='0'*64;write(root,'spread-approval.json',value)
        cert['review']=ref(root,'spread-approval.json');write(root,'spread-certificate.json',cert);spec['experiments'][TARGET]['budget_book_grant']=ref(root,'spread-certificate.json');write(root,'spread-registration.json',spec);source=commit(root)
    claim.update(source=source,design_source=source,experiment=spec['experiments'][TARGET],registration_sha256=ref(root,'spread-registration.json')['sha256'])
    claim['budget_book_grant']['certificate']=spec['experiments'][TARGET]['budget_book_grant']
    if mutation=='dataset':claim['windows'][0]['identity']='reset';claim['prior_exposures'][0]['identity']='reset'
    write(run.directory,'claim.json',claim)
    terminal=json.loads((run.directory/'complete.json').read_text());terminal.update(source=source,registration_sha256=claim['registration_sha256'],claim_sha256=sha((run.directory/'claim.json').read_bytes()));write(run.directory,'complete.json',terminal)
    with pytest.raises(ValueError):verify_run(run.directory)


def test_unfinished_parent_and_interrupted_target(spread):
    root,spec,cert,source=spread
    terminal=root/'research_runs/dated-mark-20260911/complete.json';saved=terminal.read_bytes();terminal.unlink()
    with pytest.raises(ValueError):start(root,source)
    terminal.write_bytes(saved)
    run=start(root,source)
    with pytest.raises(ValueError):start(root,source)
    assert not (run.directory/'complete.json').exists() and not (run.directory/'failed.json').exists()


@pytest.mark.parametrize('field',['repair','source'])
def test_both_consumed_artifacts_are_immutable(spread,field):
    root,spec,cert,source=spread;path=root/cert['consumed_grants'][field]['certificate']['path'];path.write_text('{}')
    source=commit(root)
    with pytest.raises(ValueError):start(root,source)


def test_source_only_approval_cannot_authorize_book(spread):
    root,spec,cert,source=spread
    value=json.loads((root/'spread-approval.json').read_text());value['decision']='approve-single-source-extension';write(root,'spread-approval.json',value)
    cert['review']=ref(root,'spread-approval.json');write(root,'spread-certificate.json',cert);spec['experiments'][TARGET]['budget_book_grant']=ref(root,'spread-certificate.json');write(root,'spread-registration.json',spec);source=commit(root)
    with pytest.raises(ValueError):start(root,source)


def test_guarded_disposable_spread_lifecycle(tmp_path):
    directory=Path(__file__).resolve().parents[2]/'research/strategy-search-2026-09-11'
    spec=importlib.util.spec_from_file_location('spread_guard',directory/'resource_guard_v2.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
    repository=tmp_path/'repo';driver=tmp_path/'driver.py'
    driver.write_text("import importlib.util,json,os\nfrom pathlib import Path\nspec=importlib.util.spec_from_file_location('spread_fixture',"+repr(str(Path(__file__).resolve()))+")\nm=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)\nroot,spec,cert,source=m.build_spread(Path("+repr(str(repository))+"))\nrun=m.start(root,source);m.finish(run)\nresult=m.verify_run(run.directory)\nassert result['status']=='complete' and len(os.sched_getaffinity(0))<=2\n(root.parent/'synthetic-result.json').write_text(json.dumps(result))\n")
    report=guard.run_guard([sys.executable,'-B',str(driver)])
    (tmp_path/'guard-report.json').write_text(json.dumps(report,indent=2))
    assert report['child_exit_code']==0 and report['limit_reason'] is None,report
    assert report['rss_limit_bytes']==512*1024**2 and report['wall_limit_seconds']==120
