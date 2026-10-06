"""Metadata-only, stdout-only FAILED May30 preservation selection. Never reads payload bodies."""
import hashlib
import json
import os
from pathlib import Path
import stat

ID = 'real-pilot-fifth-graph-failed-preservation-20261006-01'
GRAPH = 'eth-paper-real-pilot-graph-20220530-20261005-01'
SOURCE = '14414c1637256dd286eafbe92391129dee3d29bf'
PROGRAM = 'onchain-paper-replication-2026-09-24'
PREFIX = 'research_artifacts/' + PROGRAM
ROOTS = ('research_runs/' + GRAPH, PREFIX + '/runs/' + GRAPH, PREFIX + '/sources/' + GRAPH)
GIB = 1024**3
MAX_META = 4 * 1024**2
CALLER = 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-fifth-graph01-2026-10-06'
EXTRA_CONTROLS = (CALLER + '/ROOT_TERMINAL01.json', CALLER + '/outer-exit01.json')
FAILED_ROOT_SHA = '498bee3919eee4a79d3b983746cd5f0090963780b58e272128b5a70f3548cc1a'
OPAQUE_BYTES = {
    ROOTS[2] + '/aggregation/ledger.sqlite': 3189231616,
    ROOTS[2] + '/graph-2022-05-30/edge_index.npy': 38817824,
    ROOTS[2] + '/graph-2022-05-30/node_features.npy': 50606240,
}



def require(ok, message):
    if not ok:
        raise ValueError(message)


def identity(s):
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns]


def canonical(root, relative):
    p = Path(relative)
    require(not p.is_absolute() and '..' not in p.parts, 'relative scope required')
    path = root / p
    require(path.resolve(strict=True) == path, 'canonical original path required')
    return path


def metadata(root, relative, digest=None):
    path = canonical(root, relative)
    s = path.lstat()
    require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1 and s.st_size <= MAX_META,
            'bounded single-link metadata required')
    raw = path.read_bytes()
    require(identity(path.lstat()) == identity(s), 'metadata changed during read')
    sha = hashlib.sha256(raw).hexdigest()
    require(digest is None or sha == digest, 'metadata hash differs')
    return raw, sha


def select(root, review_ref, bodies_ref):
    root = Path(root).resolve(strict=True)
    # Refuse active runs before enumerating any output body.
    run = root / ROOTS[0]
    terminals = [p for p in (run/'complete.json', run/'failed.json') if os.path.lexists(p)]
    require(len(terminals) == 1 and terminals[0].name == 'failed.json',
            'genuine FAILED original required; active/complete is unavailable')
    require(all(type(ref) is dict and set(ref) == {'path', 'sha256'}
                and type(ref['path']) is str and type(ref['sha256']) is str
                and len(ref['sha256']) == 64 for ref in (review_ref, bodies_ref)),
            'actual independent outcome and body references required; draft nulls refuse')
    review = json.loads(metadata(root, review_ref['path'], review_ref['sha256'])[0])
    require(review['decision'] == 'accepted' and review['experiment'] == GRAPH
            and review['source'] == SOURCE and review['root_actual_exit']['exit_code'] == 1,
            'independent exact failed outcome and actual Root one required')
    evidence = review['evidence']
    require(evidence.get(bodies_ref['path']) == bodies_ref['sha256'], 'body review not anchored by outcome review')
    bodies = json.loads(metadata(root, bodies_ref['path'], bodies_ref['sha256'])[0])
    require(bodies['decision'] == 'pass', 'independent retained-body hash pass required')
    claim_path = ROOTS[0] + '/claim.json'
    claim_raw, claim_sha = metadata(root, claim_path, review['claim_sha256'])
    claim = json.loads(claim_raw)
    require(claim['experiment_id'] == GRAPH and claim['source'] == SOURCE
            and claim['program_id'] == PROGRAM, 'original claim identity differs')
    terminal_path = str(terminals[0].relative_to(root))
    require(terminal_path in evidence, 'actual terminal absent from review')
    terminal = json.loads(metadata(root, terminal_path, evidence[terminal_path])[0])
    status = terminals[0].stem
    require(terminal['experiment_id'] == GRAPH and terminal['claim_sha256'] == claim_sha
            and terminal['status'] == status == 'failed' and terminal['output_sha256'] == {},
            'original terminal join differs')
    guard_path = ROOTS[1] + '/guard/final.json'
    require(guard_path in evidence, 'closed native guard absent from review')
    guard = json.loads(metadata(root, guard_path, evidence[guard_path])[0])
    require(guard['cleanup_verified'] is True and guard['phase'] in ('complete', 'failed'),
            'actual native cleanup required')
    require(review['cleanup']['original_guard_cleanup_verified'] is True
            and review['cleanup']['recorded_cgroup_absent'] is True,
            'independent cleanup observation required')
    require(guard['phase'] == 'failed' and guard['child_exit_code'] == 125
            and guard['cleanup_stop_returncode'] == 0, 'original failed native fields differ')
    require(not Path(guard['cgroup']).exists(), 'failed original cgroup still present')
    root_ref = EXTRA_CONTROLS[0]
    require(evidence.get(root_ref) == FAILED_ROOT_SHA, 'actual failed Root observation not anchored')
    root_exit = json.loads(metadata(root, root_ref, FAILED_ROOT_SHA)[0])
    outer_ref = EXTRA_CONTROLS[1]
    require(outer_ref in evidence, 'original outer exit absent from review')
    outer = json.loads(metadata(root, outer_ref, evidence[outer_ref])[0])
    require(root_exit['identity'] == GRAPH and root_exit['source_commit'] == SOURCE
            and root_exit['actual_root_tool_exit_code'] == root_exit['actual_parent_exit_code'] == 1
            and root_exit['failed_marker_sha256'] == evidence[terminal_path]
            and root_exit['guard_final_sha256'] == evidence[guard_path]
            and root_exit['selected_recorded_pids_absent'] is True
            and root_exit['actual_current_cgroup_absent'] is True
            and outer['experiment'] == GRAPH and outer['source'] == SOURCE and outer['exit_code'] == 1,
            'original Root/outer/failed/guard joins differ')
    pids = root_exit['actual_selected_recorded_pids']
    require(type(pids) is list and len(pids) == 5 and len(set(pids)) == 5
            and all(type(pid) is int and pid > 0 and not Path('/proc', str(pid)).exists() for pid in pids),
            'five selected recorded PIDs not absent; lifetime remains unknown')
    cell_path = ROOTS[1] + '/postmortem-cells.json'
    require(cell_path in evidence, 'original failed postmortem denominator unreviewed')
    cells = json.loads(metadata(root, cell_path, evidence[cell_path])[0])
    require(type(cells) is list and len(cells) == 2
            and cells[0]['id'] == 'source-000000' and cells[0]['status'] == 'complete'
            and cells[0]['rows'] == 7507236 and cells[1]['id'] == 'graph-2022-05-30'
            and cells[1]['status'] == 'unavailable', 'failed original cell denominator differs')
    unavailable = (ROOTS[0] + '/outputs/artifact-index.json', ROOTS[2] + '/aggregation/complete.json',
                   ROOTS[2] + '/graph-2022-05-30/manifest.json', ROOTS[2] + '/graph-2022-05-30.json')
    require(not any(os.path.lexists(root / name) for name in unavailable)
            and bodies.get('index_sha256') is None, 'failed scope acquired fictional complete graph/index')
    payloads = {}
    for row in bodies['files']:
        require(row['path'] not in payloads, 'duplicate reviewed payload')
        require(any(Path(row['path']).is_relative_to(Path(r)) for r in ROOTS),
                'payload outside actual increment')
        payloads[row['path']] = row
    require(set(payloads) == set(OPAQUE_BYTES)
            and all(payloads[path]['bytes'] == size for path, size in OPAQUE_BYTES.items()),
            'exact ledger and two partial-array body proof required')
    files, directories, seen, absent_roots = [], [], set(), []
    for relative_root in ROOTS:
        if not os.path.lexists(root/relative_root):
            require(status == 'failed' and relative_root == ROOTS[2], 'required original control root absent')
            absent_roots.append(relative_root)
            continue
        start = canonical(root, relative_root)
        require(start.is_dir(), 'original increment root missing')
        for base, dirs, names in os.walk(start, followlinks=False):
            dirs.sort(); names.sort()
            paths = [Path(base)] + [Path(base)/name for name in names]
            for path in paths:
                rel = str(path.relative_to(root)); canonical(root, rel); s = path.lstat()
                require(len(files) + len(directories) < 4096, 'finite member bound exceeded')
                if stat.S_ISDIR(s.st_mode):
                    directories.append({'path': rel, 'mode': stat.S_IMODE(s.st_mode)})
                    continue
                require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1, 'regular single-link original required')
                if rel in payloads:
                    row = payloads[rel]
                    require(row['stat_identity'] == [s.st_dev, s.st_ino, s.st_nlink, s.st_size, s.st_mtime_ns, s.st_ctime_ns]
                            and row['bytes'] == s.st_size, 'reviewed payload stat differs')
                    digest = row['sha256']; seen.add(rel)
                    role = 'independently-hashed-original-payload'
                else:
                    require(path.suffix in ('.json', '.jsonl', '.log') and s.st_size <= MAX_META,
                            'opaque body needs independent hash evidence')
                    require(rel in evidence, 'actual failed control not independently reviewed: ' + rel)
                    _, digest = metadata(root, rel, evidence[rel])
                    role = 'actual-graph-control-evidence'
                require(isinstance(digest, str) and len(digest) == 64
                        and all(c in '0123456789abcdef' for c in digest), 'invalid body digest')
                files.append({'path': rel, 'bytes': s.st_size, 'sha256': digest,
                              'stat_identity': identity(s), 'nlink': 1,
                              'mode': stat.S_IMODE(s.st_mode), 'role': role})
            for name in dirs:
                require(not (Path(base)/name).is_symlink(), 'symlink directory refused')
    require(seen == set(payloads), 'reviewed payload missing from actual inventory')
    require(sum(row['bytes'] for row in payloads.values()) == bodies['total_bytes'], 'body evidence total differs')
    # Explicit Root observation/outer controls are outside the original three payload roots.
    for rel in EXTRA_CONTROLS:
        path = canonical(root, rel); info = path.lstat()
        _, digest = metadata(root, rel, evidence[rel])
        files.append({'path': rel, 'bytes': info.st_size, 'sha256': digest,
                      'stat_identity': identity(info), 'nlink': 1,
                      'mode': stat.S_IMODE(info.st_mode), 'role': 'actual-failed-root-control-evidence'})
    parent = canonical(root, CALLER); info = parent.lstat()
    require(stat.S_ISDIR(info.st_mode), 'Root control directory type differs')
    directories.append({'path': CALLER, 'mode': stat.S_IMODE(info.st_mode)})
    files.sort(key=lambda x: x['path']); directories.sort(key=lambda x: x['path'])
    total = sum(row['bytes'] for row in files)
    require(files and total + 16*1024**2 < 5*GIB and 2*total + 16*1024**2 < 8*GIB,
            'unchanged finite preservation envelope cannot hold selected increment')
    return {'schema_version': 1, 'status': 'DRAFT_NOT_RELEASED', 'identity': ID,
            'graph_terminal_status': status, 'graph_terminal': {'path': terminal_path, 'sha256': evidence[terminal_path]},
            'graph_outcome_review': review_ref, 'independent_body_hash': bodies_ref,
            'graph_terminal_cells': cells, 'absent_original_roots': absent_roots,
            'files': files, 'directories': directories, 'count': len(files),
            'total_bytes': total, 'max_body_bytes': max(r['bytes'] for r in files),
            'disk_floor_bytes': 10*GIB, 'owned_tree_limit_bytes': 5*GIB,
            'transport_payload_budget_bytes': 8*GIB,
            'remote': 'research-backups/' + PROGRAM + '/' + ID,
            'qualification': 'Actual FAILED May30 increment only: source cell COMPLETE, graph UNAVAILABLE; three opaque bodies are ledger/two partial arrays, never a complete graph. Root1/native125/cleanup_stop0 and unknown lifetime PID history remain. No relaunch or refund. Failure and absent cells remain original. Payload hashes inherited from independent review with current stat joins; no payload read. All originals and successful fresh recoveries retained. Root must freeze exact envelope and independent release.'}


def envelope_template(baseline, selection_ref, entry_ref, helper_ref, review_ref, bodies_ref):
    """Reuse reviewed dependencies, but never silently adopt stale Main source pins."""
    result = json.loads(json.dumps(baseline))
    result['identity'] = ID
    old_helper = result['helper']['path']
    del result['source_files'][old_helper]
    result['helper'] = helper_ref
    result['source_files'][helper_ref['path']] = helper_ref['sha256']
    result['selection'] = selection_ref
    result['evidence'] = [review_ref, bodies_ref]
    old = [p for p in result['source_files'] if p == 'research/onchain-paper-replication-2026-09-24/storage/real-pilot-fourth-graph-preservation-20261006-01/entry01.py']
    require(len(old) == 1, 'exact old entry binding required')
    del result['source_files'][old[0]]
    result['source_files'][entry_ref['path']] = entry_ref['sha256']
    result['status'] = 'DRAFT_REQUIRES_CURRENT_SOURCE_BINDING_AND_RELEASE'
    result['qualification'] += ' Inherited source pins are not currentness approval; Root must bind reviewed current bytes before release.'
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--review', required=True); parser.add_argument('--review-sha256', required=True)
    parser.add_argument('--bodies', required=True); parser.add_argument('--bodies-sha256', required=True)
    args = parser.parse_args()
    print(json.dumps(select(args.root, {'path':args.review,'sha256':args.review_sha256},
                            {'path':args.bodies,'sha256':args.bodies_sha256}), sort_keys=True, indent=2))
