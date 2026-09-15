"""Disposable full source lifecycle; inject invented transport, never network."""
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
    fixture = load('invented_q1_fixture', ROOT/'tests/research/test_defi_depth_source.py')
    sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
    began = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='defi-q1-invented-') as directory:
        root = Path(directory)
        here = root/'research/defi-depth-2026-09-15'
        here.mkdir(parents=True)
        real = json.loads((HERE/'gates-q1.json').read_text())
        exp = copy.deepcopy(real['experiments']['defi-depth-q1-20260915'])
        for name in exp['source_files']:
            dest = root/name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/name, dest)
        shutil.copyfile(HERE/'q1-charter.md', here/'q1-charter.md')
        synthetic = fixture.fixture()
        (here/'q1-spec.json').write_text(json.dumps(synthetic, indent=2)+'\n')
        shutil.copyfile(HERE/'phase-grant.json', here/'phase-grant.json')
        for name, ref in exp['inputs'].items():
            if name not in ('spec', 'phase'):
                ref['path'] = 'invented_inputs/'+name+'.json'
            path = root/ref['path']
            path.parent.mkdir(parents=True, exist_ok=True)
            if name not in ('spec', 'phase'):
                path.write_text(json.dumps({'scope': 'Invented placeholder; no actual predecessor or market data'})+'\n')
            ref['sha256'] = sha(path)
        exp['runtime_hashes'] = runtime_hashes()
        gate = {'schema_version': 1, 'program_id': 'invented-protocol-fixture',
                'families': {'protocol-state-source': {'mechanism_id': 'invented-protocol-observability',
                'prior_attempts': 0, 'attempt_budget': 1, 'history_reference': 'Invented source fixture only'}},
                'datasets': {k: {**v, 'identity': 'invented-protocol-seeds', 'history_reference': 'Invented no-network fixture'}
                for k, v in real['datasets'].items() if k == 'defi-protocol-source-seeds'},
                'experiments': {'defi-depth-q1-20260915': exp}}
        (here/'gates-q1.json').write_text(json.dumps(gate, indent=2)+'\n')

        def git(*args):
            return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.STDOUT).decode().strip()
        git('init', '-q')
        git('config', 'user.name', 'Synthetic research fixture')
        git('config', 'user.email', 'synthetic@example.invalid')
        git('add', '.')
        git('commit', '-qm', 'Freeze invented protocol source fixture')
        module = load('isolated_q1', here/'q1_source.py')
        fake, calls = fixture.fake_transport(synthetic)
        original = module.capture
        module.capture = lambda spec, publish: original(spec, publish, fake)
        args = sys.argv[:]
        sys.argv = ['q1_source.py', '--source', git('rev-parse', 'HEAD')]
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                module.main()
        finally:
            sys.argv = args
        result = verify_run(root/'research_runs/defi-depth-q1-20260915')
        assert len(calls) == 129
        receipt = {'scope': 'Disposable invented source states, no network/actual market inputs; real Q1 main/ResearchRun with transport injected',
                   'verification': result, 'requests': len(calls), 'elapsed_seconds': time.monotonic()-began,
                   'tested_sources': exp['source_files'], 'elapsed_time_kill': False,
                   'temporary_fixture_removed_on_exit': True}
    (HERE/'reviews/q1-synthetic-preflight.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
