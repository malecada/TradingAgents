"""Source-only caller binding; no admission, launch or empirical reads."""
import ast
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = HERE.parent / 'real-data-pilot-final21-2026-10-08'


def pin(path):
    return {'path': str(path.relative_to(ROOT)),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


EDITS = {
    'root_io.py': [
        ("EXPERIMENT = 'eth-paper-real-data-end-to-end-resource-20261008-21'\n", ''),
        ("    if args.experiment != EXPERIMENT or not io['outer_log_handles_closed'] or not io['supervisor_reaped']:\n",
         "    if not io['outer_log_handles_closed'] or not io['supervisor_reaped']:\n"),
        ("    base = root/PREFIX/'runs'/EXPERIMENT\n", "    base = root/PREFIX/'runs'/args.experiment\n"),
        ("launch['experiment'] != EXPERIMENT:", "launch['experiment'] != args.experiment:"),
        ("    observation = WritableUnion(job['resources']['storage_budget'],root).check()\n",
         "    observation = WritableUnion(job['resources']['storage_budget'],root,experiment=args.experiment).check()\n"),
        ("        'experiment':EXPERIMENT,'source':args.source,\n", "        'experiment':args.experiment,'source':args.source,\n"),
        ("    if args.experiment != EXPERIMENT:\n        raise ValueError('This Root IO seam admits only the fixed unused pilot')\n    _, job = _admitted(args)\n",
         "    admission, job = _admitted(args)\n    if args.experiment != admission.experiment_id:\n        raise ValueError('Root IO experiment differs from genuine admission')\n"),
        ("    logs = root/PREFIX/'pilot-parent'/EXPERIMENT\n", "    logs = root/PREFIX/'pilot-parent'/admission.experiment_id\n"),
    ],
    'preflight01.py': [
        ('    storage=WritableUnion(budget,ROOT).check()\n',
         '    storage=WritableUnion(budget,ROOT,experiment=admission.experiment_id).check()\n'),
    ],
}


def main():
    rows = {}
    for name, edits in EDITS.items():
        original = (BASE/name).read_text()
        source = original
        for old, new in edits:
            if source.count(old) != 1:
                raise ValueError('exact original seam differs: '+name+': '+old)
            source = source.replace(old, new, 1)
        inverse = source
        for old, new in reversed(edits):
            if not new:
                inverse = inverse.replace("PREFIX = 'research_artifacts/", old+"PREFIX = 'research_artifacts/", 1)
            else:
                if inverse.count(new) != 1:
                    raise ValueError('exact inverse seam differs: '+name)
                inverse = inverse.replace(new, old, 1)
        if inverse != original:
            raise ValueError('unrelated source changed: '+name)
        ast.parse(source)
        (HERE/('baseline_'+name)).write_text(original)
        target = HERE/name
        target.write_text(source)
        (HERE/(name+'.diff')).write_text(''.join(difflib.unified_diff(
            original.splitlines(True), source.splitlines(True),
            fromfile='accepted21/'+name, tofile='source-only/'+name)))
        rows[name] = {'baseline': pin(BASE/name), 'candidate': pin(target),
                      'literal_inverse_exact': True, 'edit_count': len(edits)}
    body = {'status': 'SOURCE_ONLY_NOT_INSTALLED_NOT_ENTRY_RELEASED',
            'files': rows,
            'scope': 'Reuse original capture, cleanup, guards and fixed per-entry preflight. Root launch uses genuine admitted identity; storage scans receive the same explicit identity. No empirical read, registration, budget, source integration or launch.',
            'limitations': ['Independent changed-seam review pending.',
                            'Fixed preflight name, gate, resources and allowance remain entry-specific and unchanged.',
                            'Source acceptance alone never grants execution.']}
    (HERE/'CANDIDATE01.json').write_text(json.dumps(body, indent=2, sort_keys=True)+'\n')
    print(json.dumps({'files': rows, 'status': body['status']}, sort_keys=True))


if __name__ == '__main__':
    main()
