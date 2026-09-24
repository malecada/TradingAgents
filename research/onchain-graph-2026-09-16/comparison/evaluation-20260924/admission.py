"""One additive comparison admission; no price decoding or fitting here."""
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import time

from tradingagents.research import admit

BASE = 'research/onchain-graph-2026-09-16/comparison/evaluation-20260924'
EXPERIMENT = 'eth-matched-direction-20260924'
GRAPH_EXPERIMENT = 'eth-full-history-feature-panel-resume2-20260922'
MECHANISM = 'ethereum-temporal-motif-incremental-direction-screen'
CONFIG_SHA = 'ea07a698b667963dafc51a4a37b7afb1c68d8bd6f0be13c4b4d2d4ebd248ac2c'
PROTOCOL_SHA = '7d77e709d886dc14324a94f6b5245c88ada3dddbdbf739534e56b2b71a35a89f'
MONTHS = ['2021-12']+[f'{year}-{month:02d}' for year in range(2022,2025) for month in range(1,13)]+['2025-01']
FOLDS = [f'2024-{month:02d}' for month in range(1,13)]
OUTPUTS = ['inputs-admission.json','market.json','graph.json','panel.json','fits.json',
           'predictions.json','evaluation.json','summary.json']
LINEAGE = ['eth-graph-source-20260916','eth-graph-prototype-20260916',
           'eth-temporal-motifs-20260916','eth-temporal-motifs-8gib-20260916',
           'eth-panel-readiness-20260916','eth-seven-day-pilot-20260916',
           'eth-matched-input-capture-20260916','eth-remaining-graph-capture-20260916',
           'eth-graph-source-recovery-20260917','eth-graph-source-resume-20260917',
           'eth-graph-source-resume2-20260918','eth-graph-source-resume3-20260918',
           'eth-seven-day-offline-pilot-20260922','eth-full-history-feature-panel-20260922',
           'eth-full-history-feature-panel-resume-20260922',GRAPH_EXPERIMENT]
FAILED = {'eth-temporal-motifs-20260916','eth-seven-day-pilot-20260916','eth-full-history-feature-panel-20260922',
          'eth-full-history-feature-panel-resume-20260922'}


def expected_cells():
    return ['spot-'+m for m in MONTHS]+['graph-panel']+[
        f'fold-{m}-{arm}' for m in FOLDS for arm in ['M0','M1','M2']]+['inference','screening']


def required_inputs():
    return {'config','protocol','history','approval','amendment','release_review',
            'graph_panel','graph_terminal','graph_review','graph_review_guard',
            'spot_capture_review','spot_manifest','preservation','preservation_manifest',
            'backup','verification','verification_log'} | {
                f'spot_{m}_{kind}' for m in MONTHS for kind in ['metadata','zip','checksum']}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def contract(exp):
    # These release objects bind this contract and cannot include their own hash.
    omitted = {'amendment','approval','release_review'}
    value = dict(exp,inputs={k:v for k,v in exp['inputs'].items() if k not in omitted})
    return sha(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode())


def validate_metadata(gate,history,approval,amendment):
    e=gate['experiments'][EXPERIMENT];f=gate['families'][e['family']]
    if e['family']!='eth-matched-direction' or f['mechanism_id']!=MECHANISM or (f['prior_attempts'],f['attempt_budget'])!=(16,17):
        raise ValueError('one cumulative17 comparison required')
    if (e['parent'],e.get('graph_parent'),e['stage'],e['reuse'])!=(None,GRAPH_EXPERIMENT,'development','exploratory'):
        raise ValueError('exploratory parent/sample routing differs')
    if e['cells']!=expected_cells() or e['outputs']!=OUTPUTS:
        raise ValueError('registered cell/output denominator differs')
    if set(e['inputs'])!=required_inputs():
        raise ValueError('exact registered input cohort required')
    if e['inputs']['config']['sha256']!=CONFIG_SHA or e['inputs']['protocol']['sha256']!=PROTOCOL_SHA:
        raise ValueError('scientific protocol or configuration changed')
    refs={f'research_runs/{name}/{file}' for name in LINEAGE
          for file in ['claim.json','failed.json' if name in FAILED else 'complete.json']}
    if history['lineage']!=LINEAGE or set(history['metadata_hashes'])!=refs:
        raise ValueError('complete sixteen-attempt lineage required')
    if approval.get('decision')!='approve-single-matched-comparison' or approval.get('review_sha256')!=e['inputs']['release_review']['sha256']:
        raise ValueError('independent comparison release approval missing')
    wanted=dict(additional_claims=1,prior_claims=16,cumulative_cap=17,
                target_experiment=EXPERIMENT,network_allowed=False,prices_or_models_allowed=True,
                target_contract_sha256=contract(e))
    if any(amendment.get(k)!=v for k,v in wanted.items()):
        raise ValueError('explicit single comparison allowance differs')


def guard_module(root):
    path=Path(root)/'research/onchain-graph-2026-09-16/fullpanel_resume2/memory_guard.py'
    spec=importlib.util.spec_from_file_location('matched_kernel_guard',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m


def assert_guard(root,source,*,review=False):
    root=Path(root).resolve();ns=root/BASE;phase='review' if review else 'compute'
    receipts=ns/'resources'/phase
    live=json.loads((receipts/'live.json').read_bytes())
    command=[sys.executable,'-B',str(ns/('check_final.py' if review else 'run.py'))]
    if review:command+=['--root',str(root)]
    command+=['--source',source]
    if review:command+=['--report',str(ns/'independent-report.json')]
    if live.get('phase')!='running' or live.get('command')!=command or live.get('cwd')!=str(root) or live.get('receipt_dir')!=str(receipts):
        raise RuntimeError('worker/guard command identity differs')
    if json.loads((receipts/'release.json').read_bytes())!={'kernel_controls_verified':True}:
        raise RuntimeError('kernel guard not released')
    if live.get('boot_id')!=Path('/proc/sys/kernel/random/boot_id').read_text().strip():
        raise RuntimeError('guard boot differs')
    if not 0<live['lease_seconds']<=15 or not 0<=time.monotonic()-live['monotonic_seconds']<=live['lease_seconds']:
        raise RuntimeError('guard lease expired')
    m=guard_module(root);cg=m._own_cgroup()
    if str(cg)!=live.get('cgroup') or cg.name!=live.get('unit'):
        raise RuntimeError('worker outside guarded cgroup')
    m._verify_controls(m._read_controls(cg),6*2**30,6*2**30,2**29)
    if live.get('reserve_bytes')!=3*2**30 or live.get('start_reserve_bytes')!=9*2**30:
        raise RuntimeError('host reserve differs')
    if sorted(os.sched_getaffinity(0))!=live['cpus'] or not 0<len(live['cpus'])<=2:
        raise RuntimeError('CPU allocation differs')
    return live


def runtime_module(root):
    path=Path(root)/'scripts/research_runtime.py'
    spec=importlib.util.spec_from_file_location('matched_pinned_runtime',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def assert_runtime(root):
    root=Path(root).resolve()
    if Path(sys.executable).absolute()!=root/'.venv/bin/python':
        raise ValueError('exact pinned research interpreter required')
    result=runtime_module(root).receipt(root)
    if result.get('ok') is not True or result.get('problems'):
        raise ValueError('pinned offline runtime check failed: '+str(result.get('problems')))
    return result


def admit_execution(root,source,*,review=False,require_guard=True):
    root=Path(root).resolve()
    assert_runtime(root)
    if require_guard:assert_guard(root,source,review=review)
    for path in [root,Path('/home/malecada/Data')]:
        if shutil.disk_usage(path).free<20*2**30:raise OSError('20GiB disk reserve required')
    a=admit(root=root,registration=BASE+'/gates.json',experiment=EXPERIMENT,
            source=source,_own_claim=EXPERIMENT if review else None)
    def read(name):
        ref=a.inputs[name];raw=(root/ref['path']).read_bytes()
        if sha(raw)!=ref['sha256']:raise ValueError('metadata hash differs: '+name)
        return json.loads(raw)
    history=read('history');validate_metadata(a.spec,history,read('approval'),read('amendment'))
    for path,digest in history['metadata_hashes'].items():
        if sha((root/path).read_bytes())!=digest:raise ValueError('ancestor receipt changed')
    if importlib.metadata.version('lightgbm')!='4.6.0':raise ValueError('pinned LightGBM version required')
    result=read('preservation');backup=read('backup');verification=read('verification')
    if result.get('status')!='verified' or result.get('intent_sha256')!=a.inputs['preservation_manifest']['sha256']:
        raise ValueError('full graph preservation not verified')
    if backup.get('remote_verified') is not True or backup.get('preservation_result_sha256')!=a.inputs['preservation']['sha256']:
        raise ValueError('graph evidence remote backup missing')
    if verification.get('exit_code')!=0 or verification.get('log_sha256')!=a.inputs['verification_log']['sha256']:
        raise ValueError('named offline verification missing')
    return a
