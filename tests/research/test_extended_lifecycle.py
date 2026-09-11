"""Invented four-claim history and one source extension; no empirical inputs."""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import pytest
from tradingagents.research import ResearchRun as OriginalRun,runtime_hashes as original_hashes
from tradingagents.research_amended import ResearchRun as RepairRun,runtime_hashes as repair_hashes
from tradingagents.research_amended.amendment import MUTABLE
from tradingagents.research_amended.verify import verify_run as frozen_v1_verify
from tradingagents.research_extended import ResearchRun,runtime_hashes
from tradingagents.research_extended.extension import canonical,changes,TARGET
from tradingagents.research_extended.verify import verify_run


def sha(raw):return hashlib.sha256(raw).hexdigest()
def git(root,*args):return subprocess.check_output(['git','-c','core.hooksPath=/dev/null',*args],cwd=root,text=True).strip()
def write(root,name,value):(root/name).write_text(json.dumps(value))
def ref(root,name):return {'path':name,'sha256':sha((root/name).read_bytes())}
def commit(root):
    git(root,'add','.')
    git(root,'-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid','commit','-qm','invented lifecycle')
    return git(root,'rev-parse','HEAD')


def rebind_extension(root,spec,cert):
    target={key:value for key,value in spec['experiments'][TARGET].items() if key!='budget_extension'}
    baseline=spec['experiments'][cert['parent_experiment']]
    manifest={'schema_version':1,'baseline_experiment':cert['parent_experiment'],'target_experiment':TARGET,
              'baseline_contract_sha256':sha(canonical(baseline)),'target_contract_sha256':sha(canonical(target)),'changes':changes(baseline,target)}
    write(root,'extension-changes.json',manifest)
    cert['target_contract_sha256']=manifest['target_contract_sha256'];cert['change_manifest']=ref(root,'extension-changes.json')
    approval={'decision':'approve-single-source-extension','target_experiment':TARGET,'increment':1,'target_contract_sha256':cert['target_contract_sha256'],
              'change_manifest_sha256':cert['change_manifest']['sha256'],'independent_review':ref(root,'extension-review.md')}
    write(root,'extension-approval.json',approval)
    write(root,'extension-preflight.json',{'status':'pass','target_experiment':TARGET,'change_manifest_sha256':cert['change_manifest']['sha256'],'reports':[ref(root,'extension-report.json')]})
    cert['review']=ref(root,'extension-approval.json');cert['preflight']=ref(root,'extension-preflight.json')
    write(root,'extension-certificate.json',cert)
    spec['experiments'][TARGET]['budget_extension']=ref(root,'extension-certificate.json')
    write(root,'extension-registration.json',spec)
    return commit(root)


def build_extension(root,*,target_updates=None,datasets=None):
    """Reusable synthetic-only fixture; callers may place additional files first."""
    root=Path(root);root.mkdir(exist_ok=True)
    git(root,'init','-q')
    for name in ('synthetic-economic.py','synthetic-old.py','synthetic-repair.py','synthetic-source.py','synthetic-charter.md','repair-review.md','repair-report.json','extension-review.md','extension-report.json'):
        (root/name).write_text('Invented '+name)
    (root/'synthetic-input.json').write_bytes(b'[1]')
    family={'mechanism_id':'invented-dated','attempt_budget':4,'prior_attempts':1,'history_reference':'one historical and complete invented program history'}
    exp={'family':'dated','parent':None,'charter':ref(root,'synthetic-charter.md'),'question':'invented question','stage':'development','reuse':'exploratory',
         'windows':[{'dataset':'sample','start':'2000-01-01T00:00:00Z','end':'2001-01-01T00:00:00Z','availability':'existing'}],
         'inputs':{'sample':{**ref(root,'synthetic-input.json'),'dataset':'sample'}},'source_files':{name:ref(root,name)['sha256'] for name in ('synthetic-economic.py','synthetic-old.py')},
         'runtime_hashes':original_hashes(),'selection':None,'cells':['case'],'outputs':['output.json']}
    spec={'schema_version':1,'program_id':'invented-program','families':{'dated':family},'datasets':{'sample':{'identity':'invented-sample','history_reference':'invented','exposures':[{'start':'2000-01-01T00:00:00Z','end':'2001-01-01T00:00:00Z','state':'spent'}]}},'experiments':{}}
    spec['families']['unrelated']={'mechanism_id':'unrelated-mechanism','attempt_budget':1,'prior_attempts':0,'history_reference':'unrelated frozen history'}
    spec['experiments']['unrun-baseline']=deepcopy(exp)
    previous=None
    for name in ('original-a','original-b','original-c'):
        current=deepcopy(exp);current['parent']=previous;spec['experiments'][name]=current
        write(root,'history-registration.json',spec);source=commit(root)
        run=OriginalRun.start(root=root,registration='history-registration.json',experiment=name,source=source)
        run.fail('invented harness outcome')
        previous=name
    repaired=deepcopy(spec['experiments'][previous]);repaired['parent']=previous;repaired['runtime_hashes']=repair_hashes()
    repaired['source_files']={name:ref(root,name)['sha256'] for name in ('synthetic-economic.py','synthetic-repair.py')}
    spec['experiments']['repair']=repaired
    write(root,'repair-manifest.json',{'schema_version':1,'baseline_experiment':previous,'economic_source_files':{'synthetic-economic.py':ref(root,'synthetic-economic.py')['sha256']},
          'baseline_harness_source_files':{'synthetic-old.py':ref(root,'synthetic-old.py')['sha256']},'target_harness_source_files':{'synthetic-repair.py':ref(root,'synthetic-repair.py')['sha256']},
          'experiment_invariants':{key:value for key,value in repaired.items() if key not in MUTABLE}})
    repair_contract=sha(canonical(repaired))
    write(root,'repair-approval.json',{'decision':'approve-single-amendment','target_experiment':'repair','increment':1,'target_contract_sha256':repair_contract,'economic_manifest_sha256':ref(root,'repair-manifest.json')['sha256'],'independent_review':ref(root,'repair-review.md')})
    write(root,'repair-preflight.json',{'status':'pass','target_experiment':'repair','economic_manifest_sha256':ref(root,'repair-manifest.json')['sha256'],'reports':[ref(root,'repair-report.json')]})
    inventory={}
    for name in ('original-a','original-b','original-c'):
        path=root/'research_runs'/name
        inventory[name]={'claim_sha256':sha((path/'claim.json').read_bytes()),'terminal':'failed.json','terminal_sha256':sha((path/'failed.json').read_bytes())}
    repair_cert={'schema_version':1,'amendment_id':'invented-repair','program_id':spec['program_id'],'family_id':'dated','mechanism_id':family['mechanism_id'],'family_sha256':sha(canonical(family)),
                 'increment':1,'target_experiment':'repair','parent_experiment':previous,'target_contract_sha256':repair_contract,'prior_claims':inventory,
                 'review':ref(root,'repair-approval.json'),'repair_preflight':ref(root,'repair-preflight.json'),'economic_manifest':ref(root,'repair-manifest.json')}
    write(root,'repair-certificate.json',repair_cert);repaired['budget_amendment']=ref(root,'repair-certificate.json')
    write(root,'history-registration.json',spec);source=commit(root)
    run=RepairRun.start(root=root,registration='history-registration.json',experiment='repair',source=source)
    run.write_json('output.json',{'invented':1});run.finish([{'id':'case','status':'complete'}])
    assert frozen_v1_verify(run.directory)['status']=='complete'
    path=run.directory;inventory['repair']={'claim_sha256':sha((path/'claim.json').read_bytes()),'terminal':'complete.json','terminal_sha256':sha((path/'complete.json').read_bytes())}
    target=deepcopy(exp);target['parent']='repair';target['runtime_hashes']=runtime_hashes();target['source_files']={'synthetic-source.py':ref(root,'synthetic-source.py')['sha256']};target['question']='invented source-only new question'
    if target_updates:target.update(deepcopy(target_updates))
    if datasets:
        if set(datasets)&set(spec['datasets']):raise ValueError('fixture only appends dataset definitions')
        spec['datasets'].update(deepcopy(datasets))
    spec['experiments'][TARGET]=target
    cert={'schema_version':1,'extension_id':'invented-source-extension','program_id':spec['program_id'],'family_id':'dated','mechanism_id':family['mechanism_id'],'family_sha256':sha(canonical(family)),
          'increment':1,'original_budget':4,'prior_effective_budget':5,'effective_budget':6,'target_experiment':TARGET,'parent_experiment':'repair','target_contract_sha256':'pending','prior_claims':inventory,
          'consumed_amendment':{'experiment_id':'repair','certificate':ref(root,'repair-certificate.json')}}
    source=rebind_extension(root,spec,cert)
    return root,spec,cert,source


@pytest.fixture
def extension(tmp_path):return build_extension(tmp_path)


def start(root,source,name=TARGET):return ResearchRun.start(root=root,registration='extension-registration.json',experiment=name,source=source)
def finish(run):
    assert run.read_input('sample')==b'[1]'
    run.write_json('output.json',{'invented':2});run.finish([{'id':'case','status':'complete'}])


def test_single_source_and_v1_closed_snapshot(extension):
    root,spec,cert,source=extension
    before={str(p.relative_to(root)):sha(p.read_bytes()) for p in (root/'research_runs').rglob('*') if p.is_file()}
    run=start(root,source);finish(run)
    assert verify_run(run.directory)['status']=='complete'
    assert verify_run(root/'research_runs/repair')['status']=='complete'
    with pytest.raises(ValueError):frozen_v1_verify(root/'research_runs/repair')
    assert all(sha((root/name).read_bytes())==value for name,value in before.items())
    claim=json.loads((run.directory/'claim.json').read_text())
    assert claim['budget_extension']['effective_budget']==6 and claim['budget_extension']['prior_attempts']==1
    with pytest.raises(ValueError):start(root,source)


@pytest.mark.parametrize('mutation',['increment','target','parent','family','inventory','dataset','historical-contract','consumed','manifest'])
def test_tampering_before_claim(extension,mutation):
    root,spec,cert,source=extension
    if mutation=='increment':cert['increment']=True
    elif mutation=='target':cert['target_experiment']='other'
    elif mutation=='parent':spec['experiments'][TARGET]['parent']='original-c';cert['parent_experiment']='original-c'
    elif mutation=='family':spec['families']['dated']['attempt_budget']=5
    elif mutation=='inventory':del cert['prior_claims']['original-a']
    elif mutation=='dataset':spec['datasets']['sample']['exposures']=[]
    elif mutation=='historical-contract':spec['experiments']['original-a']['question']='rewritten'
    elif mutation=='consumed':cert['consumed_amendment']['experiment_id']='original-c'
    elif mutation=='manifest':spec['experiments'][TARGET]['budget_extension']['sha256']='0'*64
    if mutation=='manifest':write(root,'extension-registration.json',spec);source=commit(root)
    else:source=rebind_extension(root,spec,cert)
    with pytest.raises((ValueError,KeyError)):start(root,source)
    assert not (root/'research_runs'/TARGET).exists()


def test_without_certificate_exhausted_and_failed_grant_consumed(extension):
    root,spec,cert,source=extension
    del spec['experiments'][TARGET]['budget_extension'];write(root,'extension-registration.json',spec);source=commit(root)
    with pytest.raises(ValueError,match='exhausted'):start(root,source)
    source=rebind_extension(root,spec,cert);run=start(root,source);run.fail('invented unavailable source')
    assert verify_run(run.directory)['status']=='failed'
    with pytest.raises(ValueError):start(root,source)


def test_concurrent_only_one_claim(extension):
    root,spec,cert,source=extension
    def attempt():
        try:return start(root,source)
        except (ValueError,FileExistsError):return None
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda _:attempt(),range(2)))
    winners=[r for r in results if r is not None];assert len(winners)==1;finish(winners[0])


@pytest.mark.parametrize('operation',['read','write','finish'])
def test_revalidation_after_mutation(extension,operation):
    root,spec,cert,source=extension;run=start(root,source)
    (root/'extension-review.md').write_text('changed')
    with pytest.raises(ValueError):
        if operation=='read':run.read_input('sample')
        elif operation=='write':run.write_json('output.json',{})
        else:run.finish([{'id':'case','status':'unavailable','reason':'invented'}])


def test_independent_verifier_rejects_accounting_and_historical_output_tamper(extension):
    root,spec,cert,source=extension;run=start(root,source);finish(run)
    path=root/'research_runs/repair/outputs/output.json';old=path.read_bytes();path.write_bytes(b'{}')
    with pytest.raises(ValueError):verify_run(run.directory)
    path.write_bytes(old)
    claim=json.loads((run.directory/'claim.json').read_text());claim['budget_extension']['effective_budget']=7
    write(run.directory,'claim.json',claim)
    with pytest.raises(ValueError):verify_run(run.directory)


def test_interrupted_claim_and_implicit_further_child_rejected(extension):
    root,spec,cert,source=extension
    run=start(root,source)
    with pytest.raises(ValueError):start(root,source)
    # A new name or new certificate cannot manufacture another allowance.
    later=deepcopy(spec['experiments'][TARGET]);later['parent']=TARGET
    spec['experiments']['another-source']=later
    write(root,'extension-registration.json',spec);source=commit(root)
    with pytest.raises(ValueError):start(root,source,'another-source')
    assert not (root/'research_runs/another-source').exists()


def test_unfinished_prior_and_mutated_historical_source_rejected(extension):
    root,spec,cert,source=extension
    terminal=root/'research_runs/repair/complete.json';old=terminal.read_bytes();terminal.unlink()
    with pytest.raises(ValueError):start(root,source)
    terminal.write_bytes(old)
    (root/'synthetic-old.py').write_text('changed old code')
    source=commit(root)
    with pytest.raises(ValueError):start(root,source)


@pytest.mark.parametrize('artifact',['approval','preflight','manifest'])
def test_review_preflight_or_change_manifest_cannot_be_rebound_to_invalid_fact(extension,artifact):
    root,spec,cert,source=extension
    filename={'approval':'extension-approval.json','preflight':'extension-preflight.json','manifest':'extension-changes.json'}[artifact]
    value=json.loads((root/filename).read_text())
    if artifact=='approval':value['decision']='engineering-only'
    elif artifact=='preflight':value['status']='failed'
    else:value['changes']={}
    write(root,filename,value)
    key={'approval':'review','preflight':'preflight','manifest':'change_manifest'}[artifact]
    cert[key]=ref(root,filename)
    write(root,'extension-certificate.json',cert);spec['experiments'][TARGET]['budget_extension']=ref(root,'extension-certificate.json')
    write(root,'extension-registration.json',spec);source=commit(root)
    with pytest.raises(ValueError):start(root,source)


@pytest.mark.parametrize('mutation',['dataset','unrun','family','runtime','physical'])
def test_independent_recommitted_dataset_reset_rejected(extension,mutation):
    root,spec,cert,source=extension;run=start(root,source);finish(run)
    claim=json.loads((run.directory/'claim.json').read_text())
    if mutation=='dataset':spec['datasets']['sample']['identity']='covert-reset'
    elif mutation=='unrun':del spec['experiments']['unrun-baseline']
    elif mutation=='family':spec['families']['unrelated']['history_reference']='covert-reset'
    elif mutation=='runtime':spec['experiments'][TARGET]['runtime_hashes']['original/admission.py']='0'*64
    else:(root/'history-registration.json').write_text('{}')
    source=rebind_extension(root,spec,cert)
    claim.update(source=source,design_source=source,registration_sha256=ref(root,'extension-registration.json')['sha256'],experiment=spec['experiments'][TARGET])
    if mutation=='dataset':
        claim['windows'][0]['identity']='covert-reset';claim['prior_exposures'][0]['identity']='covert-reset'
    claim['budget_extension']['certificate']=spec['experiments'][TARGET]['budget_extension']
    write(run.directory,'claim.json',claim)
    terminal=json.loads((run.directory/'complete.json').read_text());terminal.update(source=source,registration_sha256=claim['registration_sha256'],claim_sha256=sha((run.directory/'claim.json').read_bytes()))
    write(run.directory,'complete.json',terminal)
    with pytest.raises(ValueError):verify_run(run.directory)


def test_guarded_disposable_full_extension(tmp_path):
    directory=Path(__file__).resolve().parents[2]/'research/strategy-search-2026-09-11'
    spec=importlib.util.spec_from_file_location('extension_guard',directory/'resource_guard_v2.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
    driver=tmp_path/'driver.py';repository=tmp_path/'repo'
    driver.write_text("import importlib.util,json,os\nfrom pathlib import Path\nspec=importlib.util.spec_from_file_location('extension_fixture',"+repr(str(Path(__file__).resolve()))+")\nm=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)\nroot,spec,cert,source=m.build_extension(Path("+repr(str(repository))+"))\nrun=m.start(root,source);m.finish(run)\nresult=m.verify_run(run.directory)\nassert result['cell_count']==1 and result['status']=='complete'\nassert len(os.sched_getaffinity(0))<=2\n(root.parent/'synthetic-result.json').write_text(json.dumps(result))\n")
    report=guard.run_guard([sys.executable,'-B',str(driver)])
    (tmp_path/'guard-report.json').write_text(json.dumps(report,indent=2))
    assert report['child_exit_code']==0 and report['limit_reason'] is None,report
    assert report['rss_limit_bytes']==512*1024**2 and report['wall_limit_seconds']==120


@pytest.mark.parametrize('change',['remove-unrun','unrelated-family','physical-gate','ancestor-runtime'])
def test_full_pre_extension_preservation(extension,change):
    root,spec,cert,source=extension
    if change=='remove-unrun':del spec['experiments']['unrun-baseline']
    elif change=='unrelated-family':spec['families']['unrelated']['history_reference']='reset'
    elif change=='physical-gate':
        value=json.loads((root/'history-registration.json').read_text());value['irrelevant']='changed';write(root,'history-registration.json',value)
    else:spec['experiments'][TARGET]['runtime_hashes']['original/admission.py']='0'*64
    source=rebind_extension(root,spec,cert)
    with pytest.raises(ValueError):start(root,source)
    assert not (root/'research_runs'/TARGET).exists()
