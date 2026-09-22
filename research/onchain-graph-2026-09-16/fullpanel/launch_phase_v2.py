"""One separately frozen final-checker serialization correction, no compute replay."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = 'research/onchain-graph-2026-09-16/fullpanel'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def validate_contract(root, source):
    """Bind actual checker bytes to an explicit committed correction ancestor."""
    root = Path(root)
    if not re.fullmatch('[0-9a-f]{40}', source):
        raise ValueError('full correction commit required')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    subprocess.check_call(['git', 'merge-base', '--is-ancestor', source, head], cwd=root)
    relative = BASE + '/phase-correction.json'
    raw = (root / relative).read_bytes()
    if subprocess.check_output(['git', 'show', f'{source}:{relative}'], cwd=root) != raw:
        raise ValueError('correction contract differs from frozen source')
    contract = json.loads(raw)
    if contract['execution_source'] != 'fdb33cf27ca97b8d32926f046be422d8b8b45b6f' or contract['compute_replay_allowed'] is not False:
        raise ValueError('correction scope differs')
    for relative, digest in contract['committed_files'].items():
        if sha(root / relative) != digest or hashlib.sha256(subprocess.check_output(['git', 'show', f'{source}:{relative}'], cwd=root)).hexdigest() != digest:
            raise ValueError('correction source binding differs: ' + relative)
    execution = Path(contract['execution_root'])
    if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=execution, text=True).strip() != contract['execution_source']:
        raise ValueError('execution source differs')
    for relative, digest in contract['execution_files'].items():
        if sha(execution / relative) != digest:
            raise ValueError('execution binding differs: ' + relative)
    approval = json.loads((root / BASE / 'PHASE_CORRECTION_APPROVAL.json').read_bytes())
    if approval['decision'] != 'approve-phase-serialization-correction' or approval['review_sha256'] != sha(root / BASE / 'PHASE_CORRECTION_REVIEW.md'):
        raise ValueError('independent correction approval differs')
    return contract, raw


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True, help='Full committed correction source, allowed as unchanged ancestor of coordinator HEAD')
    args = parser.parse_args()
    contract, raw = validate_contract(ROOT, args.source)
    execution = Path(contract['execution_root'])
    destination = execution / BASE
    run = execution / 'research_runs/eth-full-history-feature-panel-20260922'
    if sum((run / name).exists() for name in ('complete.json', 'failed.json')) != 1:
        raise ValueError('unique compute terminal required before corrected review')
    compute = json.loads((destination / 'resource.json').read_bytes())
    if compute['source'] != contract['execution_source']:
        raise ValueError('compute guard source differs')
    report = destination / 'independent-report-v2.json'
    receipt = destination / 'independent-resource-v2.json'
    if report.exists() or receipt.exists():
        raise FileExistsError('corrected review already attempted')
    guard = module('phase_v2_cpu_guard', execution / 'research/strategy-search-2026-09-11/resource_guard_v2.py')
    memory = module('phase_v2_memory_guard', execution / 'research/onchain-graph-2026-09-16/motifs8gib/launch.py')
    os.environ['TMPDIR'] = str(destination / 'sparse-scratch')
    os.environ['PYTHONPATH'] = str(execution)
    command = [sys.executable, '-B', str(HERE / 'check_final_phase_v2.py'), '--root', str(execution), '--source', contract['execution_source'], '--report', str(report)]
    with receipt.open('x') as stream:
        result = memory.run_with_limit(command, guard, execution)
        result.update(source=contract['execution_source'], correction_source=args.source, correction_contract_sha256=hashlib.sha256(raw).hexdigest())
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result), flush=True)
    return int(result['child_exit_code'] != 0 or result['limit_reason'] is not None)


if __name__ == '__main__':
    raise SystemExit(main())
