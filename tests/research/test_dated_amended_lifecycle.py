"""Actual dated CLI on invented inputs under a disposable amended lifecycle."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
DIRECTORY=ROOT/'research/strategy-search-2026-09-11'
FILES=('dated_book_amended.py','dated_book_correction.py','dated_book_run.py','dated_book.py','dated_statistics.py',
       'dated_archive.py','carry_capture.py','carry_book.py','resource_guard.py','resource_guard_v2.py')

DRIVER=r'''
import base64,hashlib,importlib.util,json,math,os,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent
program=root/'research/strategy-search-2026-09-11'
sys.path.insert(0,str(root));sys.path.insert(0,str(program))
from tradingagents.research import ResearchRun as OldRun,runtime_hashes as old_hashes
from tradingagents.research_amended import runtime_hashes
from tradingagents.research_amended.verify import verify_run
from tradingagents.research_amended.amendment import canonical,MUTABLE
loader=importlib.util.spec_from_file_location('invented_inputs',root/'tests/research/test_dated_book_run.py')
fixture=importlib.util.module_from_spec(loader);loader.loader.exec_module(fixture)
inputs=fixture.synthetic_inputs()
for receipt in inputs[2]['requests']:
    if receipt['kind']!='spot':continue
    rows=json.loads(base64.b64decode(receipt['body_base64']))
    is_btc=receipt['id']=='btc-spot'
    for i,row in enumerate(rows):
        price=100 + (2*math.sin(i*.31) if is_btc else 3*math.cos(i*.19)) + .02*i
        row[1:5]=[price,price,price,price]
    raw=json.dumps(rows).encode()
    receipt.update(body_base64=base64.b64encode(raw).decode(),body_bytes=len(raw),body_sha256=hashlib.sha256(raw).hexdigest())
def sha(raw):return hashlib.sha256(raw).hexdigest()
def write(name,value):(root/name).write_text(json.dumps(value))
def ref(name):return {'path':name,'sha256':sha((root/name).read_bytes())}
def git(*args):return subprocess.check_output(['git','-c','core.hooksPath=/dev/null',*args],cwd=root,text=True).strip()
def commit():
    git('add','.')
    git('-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid','commit','-qm','invented dated amended lifecycle')
    return git('rev-parse','HEAD')
git('init','-q')
for name,value in zip(('capture','admission','spot_capture','spot_admission'),inputs):write(name+'.json',value)
del inputs
(root/'charter.md').write_text('Invented inputs; no actual market observation. Fixed 8 cases, 3 outputs.')
(root/'review.md').write_text('Invented independent approval fixture only.')
(root/'repair-report.json').write_text('{"synthetic":true}')
prefix='research/strategy-search-2026-09-11/'
economic={prefix+n:ref(prefix+n)['sha256'] for n in ('dated_book_run.py','dated_book.py','dated_statistics.py','dated_archive.py','carry_capture.py','carry_book.py')}
economic['uv.lock']=ref('uv.lock')['sha256']
old_harness={prefix+n:ref(prefix+n)['sha256'] for n in ('dated_book_correction.py','resource_guard.py')}
new_harness={prefix+n:ref(prefix+n)['sha256'] for n in ('dated_book_amended.py','resource_guard_v2.py')}
for path in sorted((root/'tradingagents/research_amended').glob('*.py')):
    name=str(path.relative_to(root));new_harness[name]=ref(name)['sha256']
family={'mechanism_id':'invented-dated','attempt_budget':4,'prior_attempts':1,'history_reference':'invented previous administrative attempt'}
base={'family':'dated','parent':None,'charter':ref('charter.md'),'question':'invented fixed dated episode',
      'stage':'development','reuse':'exploratory','windows':[{'dataset':'sample','start':'2026-05-01T00:00:00Z','end':'2026-06-26T00:00:00Z','availability':'existing'}],
      'inputs':{n:{**ref(n+'.json'),'dataset':'sample'} for n in ('capture','admission','spot_capture','spot_admission')},
      'source_files':{**economic,**old_harness},'runtime_hashes':old_hashes(),'selection':None,
      'cells':[fixture.runner.case_id(*case) for case in fixture.runner.CASES],'outputs':['books.json','summary.json','resource.json']}
spec={'schema_version':1,'program_id':'invented-dated','families':{'dated':family},
      'datasets':{'sample':{'identity':'invented-dated-sample','history_reference':'invented','exposures':[{'start':'2026-05-01T00:00:00Z','end':'2026-06-26T00:00:00Z','state':'spent'}]}},'experiments':{}}
registration=prefix+'gates-dated-amended.json'
prior=None
for i in range(3):
    name='invented-failed-'+str(i)
    exp=json.loads(json.dumps(base));exp['parent']=prior
    spec['experiments'][name]=exp;write(registration,spec);source=commit()
    run=OldRun.start(root=root,registration=registration,experiment=name,source=source)
    run.fail('invented harness failure with no numerical evaluation')
    prior=name
name='dated-book-amended-20260911'
child=json.loads(json.dumps(spec['experiments'][prior]));child.update(parent=prior,source_files={**economic,**new_harness},runtime_hashes=runtime_hashes())
spec['experiments'][name]=child
manifest={'schema_version':1,'baseline_experiment':prior,'economic_source_files':economic,'baseline_harness_source_files':old_harness,
          'target_harness_source_files':new_harness,'experiment_invariants':{k:v for k,v in child.items() if k not in MUTABLE}}
write('economic.json',manifest)
contract_hash=sha(canonical(child))
write('approval.json',{'decision':'approve-single-amendment','target_experiment':name,'increment':1,'target_contract_sha256':contract_hash,
                      'economic_manifest_sha256':ref('economic.json')['sha256'],'independent_review':ref('review.md')})
write('repair.json',{'status':'pass','target_experiment':name,'economic_manifest_sha256':ref('economic.json')['sha256'],'reports':[ref('repair-report.json')]})
cert={'schema_version':1,'amendment_id':'invented-once','program_id':spec['program_id'],'family_id':'dated','mechanism_id':family['mechanism_id'],
      'family_sha256':sha(canonical(family)),'increment':1,'target_experiment':name,'parent_experiment':prior,'target_contract_sha256':contract_hash,
      'prior_claims':{},'economic_manifest':ref('economic.json'),'review':ref('approval.json'),'repair_preflight':ref('repair.json')}
for i in range(3):
    old='invented-failed-'+str(i)
    cert['prior_claims'][old]={'claim_sha256':ref('research_runs/'+old+'/claim.json')['sha256'],'terminal':'failed.json','terminal_sha256':ref('research_runs/'+old+'/failed.json')['sha256']}
write('certificate.json',cert);child['budget_amendment']=ref('certificate.json');write(registration,spec);source=commit()
import dated_book_amended
sys.argv=['dated_book_amended.py','--source',source]
dated_book_amended.main()
result=verify_run(root/'research_runs'/name)
summary=json.loads((root/'research_runs'/name/'outputs/summary.json').read_text())
assert result['cell_count']==8 and result['unavailable_count']==0 and result['output_count']==3,result
assert all(case['statistics']['market_exposure']['status']=='complete' for case in summary['cases'])
assert all(case['statistics']['expected_return_confidence']['status']=='unavailable' and case['statistics']['power']['status']=='unavailable' for case in summary['cases'])
write('synthetic-result.json',{'verification':result,'exposure_complete':8,'cpu_count':len(os.sched_getaffinity(0)),
                             'source_sha256':child['source_files'],'runtime_hashes':runtime_hashes()})
'''


def test_actual_dated_cli_real_hac_under_amended_guard(tmp_path):
    loader=importlib.util.spec_from_file_location('dated_amended_guard',DIRECTORY/'resource_guard_v2.py')
    guard=importlib.util.module_from_spec(loader);loader.loader.exec_module(guard)
    program=tmp_path/'research/strategy-search-2026-09-11';program.mkdir(parents=True)
    for name in FILES:shutil.copyfile(DIRECTORY/name,program/name)
    shutil.copyfile(ROOT/'uv.lock',tmp_path/'uv.lock')
    package=tmp_path/'tradingagents';package.mkdir()
    shutil.copyfile(ROOT/'tradingagents/__init__.py',package/'__init__.py')
    for name in ('research','research_amended'):
        shutil.copytree(ROOT/'tradingagents'/name,package/name,ignore=shutil.ignore_patterns('__pycache__'))
    fixtures=tmp_path/'tests/research';fixtures.mkdir(parents=True)
    shutil.copyfile(ROOT/'tests/research/test_dated_book_run.py',fixtures/'test_dated_book_run.py')
    (tmp_path/'driver.py').write_text(DRIVER)
    report=guard.run_guard([sys.executable,'-B',str(tmp_path/'driver.py')])
    (tmp_path/'guard-report.json').write_text(json.dumps(report,indent=2)+'\n')
    assert report['child_exit_code']==0 and report['limit_reason'] is None,report
    assert report['rss_limit_bytes']==512*1024**2 and report['wall_limit_seconds']==120
    result=json.loads((tmp_path/'synthetic-result.json').read_text())
    assert result['exposure_complete']==8 and result['cpu_count']<=2
