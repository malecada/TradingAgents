from pathlib import Path
import difflib,hashlib,json
D=Path(__file__).resolve().parent;F=D.parent;M=F.parents[2];BASE=F/'real-data-pilot-fifth-graph-preservation-preparation01-2026-10-06';oldid='real-pilot-fifth-graph-preservation-20261006-01';newid='real-pilot-fifth-graph-failed-preservation-20261006-01'
for name in ('entry01.py','keep.py','prepare01.py'):
 s=(BASE/name).read_text();s=s.replace(oldid,newid)
 if name=='prepare01.py':
  s=s.replace('May30 preservation selection','FAILED May30 preservation selection')
  s=s.replace("MAX_META = 4 * 1024**2", """MAX_META = 4 * 1024**2
CALLER = 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-fifth-graph01-2026-10-06'
EXTRA_CONTROLS = (CALLER + '/ROOT_TERMINAL01.json', CALLER + '/outer-exit01.json')
FAILED_ROOT_SHA = '498bee3919eee4a79d3b983746cd5f0090963780b58e272128b5a70f3548cc1a'
OPAQUE_BYTES = {
    ROOTS[2] + '/aggregation/ledger.sqlite': 3189231616,
    ROOTS[2] + '/graph-2022-05-30/edge_index.npy': 38817824,
    ROOTS[2] + '/graph-2022-05-30/node_features.npy': 50606240,
}
""")
  s=s.replace("terminals[0].name == 'complete.json',\n            'genuine COMPLETE original required; active/failed is unavailable'", "terminals[0].name == 'failed.json',\n            'genuine FAILED original required; active/complete is unavailable'")
  s=s.replace("    review = json.loads(metadata(root, review_ref['path'], review_ref['sha256'])[0])", """    require(all(type(ref) is dict and set(ref) == {'path', 'sha256'}
                and type(ref['path']) is str and type(ref['sha256']) is str
                and len(ref['sha256']) == 64 for ref in (review_ref, bodies_ref)),
            'actual independent outcome and body references required; draft nulls refuse')
    review = json.loads(metadata(root, review_ref['path'], review_ref['sha256'])[0])""")
  s=s.replace("review['root_actual_exit']['exit_code'] == 0", "review['root_actual_exit']['exit_code'] == 1")
  s=s.replace('independent exact completed outcome and actual Root zero required','independent exact failed outcome and actual Root one required')
  s=s.replace("terminal['experiment_id'] == GRAPH and terminal['source'] == SOURCE\n            and terminal['claim_sha256'] == claim_sha and terminal['status'] == status,", "terminal['experiment_id'] == GRAPH and terminal['claim_sha256'] == claim_sha\n            and terminal['status'] == status == 'failed' and terminal['output_sha256'] == {},")
  a=s.index("    if status == 'complete':");b=s.index("    payloads = {}",a)
  s=s[:a]+"""    require(guard['phase'] == 'failed' and guard['child_exit_code'] == 125
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
"""+s[b:]
  s=s.replace("    files, directories, seen, absent_roots = [], [], set(), []", """    require(set(payloads) == set(OPAQUE_BYTES)
            and all(payloads[path]['bytes'] == size for path, size in OPAQUE_BYTES.items()),
            'exact ledger and two partial-array body proof required')
    files, directories, seen, absent_roots = [], [], set(), []""")
  s=s.replace("                    _, digest = metadata(root, rel, evidence.get(rel))", "                    require(rel in evidence, 'actual failed control not independently reviewed: ' + rel)\n                    _, digest = metadata(root, rel, evidence[rel])")
  s=s.replace("    files.sort(key=lambda x: x['path']); directories.sort(key=lambda x: x['path'])", """    # Explicit Root observation/outer controls are outside the original three payload roots.
    for rel in EXTRA_CONTROLS:
        path = canonical(root, rel); info = path.lstat()
        _, digest = metadata(root, rel, evidence[rel])
        files.append({'path': rel, 'bytes': info.st_size, 'sha256': digest,
                      'stat_identity': identity(info), 'nlink': 1,
                      'mode': stat.S_IMODE(info.st_mode), 'role': 'actual-failed-root-control-evidence'})
    parent = canonical(root, CALLER); info = parent.lstat()
    require(stat.S_ISDIR(info.st_mode), 'Root control directory type differs')
    directories.append({'path': CALLER, 'mode': stat.S_IMODE(info.st_mode)})
    files.sort(key=lambda x: x['path']); directories.sort(key=lambda x: x['path'])""")
  s=s.replace("'graph_terminal_cells': terminal.get('cells')", "'graph_terminal_cells': cells")
  s=s.replace("'qualification': 'Closed actual increment only.", "'qualification': 'Actual FAILED May30 increment only: source cell COMPLETE, graph UNAVAILABLE; three opaque bodies are ledger/two partial arrays, never a complete graph. Root1/native125/cleanup_stop0 and unknown lifetime PID history remain. No relaunch or refund.")
 (D/name).write_text(s)
inverses={}
for name in ('entry01.py','keep.py','prepare01.py'):
 before=(BASE/name).read_text().splitlines(True);after=(D/name).read_text().splitlines(True);ops=[]
 for tag,a,b,c,d in difflib.SequenceMatcher(a=before,b=after,autojunk=False).get_opcodes():
  if tag!='equal':ops.append({'original_start':a,'original_end':b,'candidate_start':c,'candidate_end':d,'original':before[a:b],'candidate':after[c:d]})
 inverse=after[:]
 for o in reversed(ops):assert inverse[o['candidate_start']:o['candidate_end']]==o['candidate'];inverse[o['candidate_start']:o['candidate_end']]=o['original']
 assert inverse==before
 inverses[name]={'baseline':str((BASE/name).relative_to(M)),'baseline_sha256':hashlib.sha256(''.join(before).encode()).hexdigest(),'candidate_sha256':hashlib.sha256(''.join(after).encode()).hexdigest(),'exact_inverse':True,'hunks':ops}
 (D/(name+'.patch')).write_text(''.join(difflib.unified_diff(before,after,fromfile=str((BASE/name).relative_to(M)),tofile=name)))
(D/'INVERSE01.json').write_text(json.dumps(inverses,indent=2)+'\n')
