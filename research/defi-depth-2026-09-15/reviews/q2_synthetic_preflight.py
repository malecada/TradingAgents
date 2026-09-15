"""Disposable compact source lifecycle plus full fixed inventory in memory; inject invented transport, never network."""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

from tradingagents.research import runtime_hashes
from tradingagents.research.verify import verify_run

ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT/'research/defi-depth-2026-09-15'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    fixture = load('invented_q2_fixture', ROOT/'tests/research/test_defi_depth_history.py')
    sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
    began = time.monotonic()
    full_spec = json.loads((HERE/'q2-spec.json').read_text())
    full_fake, full_calls = fixture.fake(full_spec)
    full_outputs = {}
    with contextlib.redirect_stdout(io.StringIO()):
        full_report = fixture.q2.capture(full_spec, lambda k,v: full_outputs.__setitem__(k,v), full_fake)
    assert len(full_report['cells']) == 20890
    assert len(full_outputs) == 5483
    assert full_report['http_requests'] == 2193
    assert full_report['rpc_subcalls'] == 18689
    assert sum(r['status']=='unavailable' for r in full_report['cells']) == 3
    with tempfile.TemporaryDirectory(prefix='defi-q2-invented-') as directory:
        root = Path(directory)
        here = root/'research/defi-depth-2026-09-15'
        here.mkdir(parents=True)
        real = json.loads((HERE/'gates-q2.json').read_text())
        exp = copy.deepcopy(real['experiments']['defi-depth-q2-20260915'])
        for name in exp['source_files']:
            dest = root/name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/name, dest)
        shutil.copyfile(HERE/'q2-charter.md', here/'q2-charter.md')
        synthetic = fixture.fixture()
        (here/'q2-spec.json').write_text(json.dumps(synthetic, indent=2)+'\n')
        shutil.copyfile(HERE/'phase-grant.json', here/'phase-grant.json')
        for name, ref in exp['inputs'].items():
            if name not in ('spec', 'phase'):
                ref['path'] = 'invented_inputs/'+name+'.json'
            path = root/ref['path']
            path.parent.mkdir(parents=True, exist_ok=True)
            if name not in ('spec', 'phase'):
                path.write_text(json.dumps({'scope': 'Invented placeholder; no actual predecessor or market data'})+'\n')
            ref['sha256'] = sha(path)
        exp['parent'] = None
        exp['cells'] = fixture.q2.cells_for(synthetic)
        exp['outputs'] = fixture.q2.outputs_for(synthetic)
        exp['runtime_hashes'] = runtime_hashes()
        gate = {'schema_version': 1, 'program_id': 'invented-protocol-fixture',
                'families': {'protocol-state-source': {'mechanism_id': 'invented-protocol-observability',
                'prior_attempts': 0, 'attempt_budget': 1, 'history_reference': 'Invented source fixture only'}},
                'datasets': {k: {**v, 'identity': 'invented-protocol-seeds', 'history_reference': 'Invented no-network fixture'}
                for k, v in real['datasets'].items() if k == 'defi-base-daily-history'},
                'experiments': {'defi-depth-q2-20260915': exp}}
        (here/'gates-q2.json').write_text(json.dumps(gate, indent=2)+'\n')

        def git(*args):
            return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.STDOUT).decode().strip()
        git('init', '-q')
        git('config', 'user.name', 'Synthetic research fixture')
        git('config', 'user.email', 'synthetic@example.invalid')
        git('add', '.')
        git('commit', '-qm', 'Freeze invented protocol source fixture')
        module = load('isolated_q2', here/'q2_source.py')
        fake, calls = fixture.fake(synthetic)
        original = module.capture
        module.capture = lambda spec, publish: original(spec, publish, fake)
        args = sys.argv[:]
        sys.argv = ['q2_source.py', '--source', git('rev-parse', 'HEAD')]
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                module.main()
        finally:
            sys.argv = args
        result = verify_run(root/'research_runs/defi-depth-q2-20260915')
        assert len(calls) == 5
        receipt = {'scope': 'Invented source states only; compact real Q2 main/ResearchRun with injected transport plus complete 1096-day invented capture in memory; no actual network/market inputs',
                   'verification': result, 'requests': len(calls),
                   'full_in_memory_inventory': {'cells':len(full_report['cells']), 'outputs_before_summary':len(full_outputs), 'http_requests':full_report['http_requests'], 'rpc_subcalls':full_report['rpc_subcalls'], 'unavailable_executable_route_cells':3}, 'elapsed_seconds': time.monotonic()-began,
                   'tested_sources': exp['source_files'], 'elapsed_time_kill': False,
                   'temporary_fixture_removed_on_exit': True}
    (HERE/'reviews/q2-synthetic-preflight.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
