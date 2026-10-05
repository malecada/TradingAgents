"""One fresh actual remote byte recovery; no native/research authority."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import selectors
import shutil
import signal
import subprocess
import time
import resource
import watch01 as W

ROOT = Path.cwd().resolve()
HERE = Path(__file__).resolve().parent
COMMIT = None
BRANCH = 'refs/heads/research/onchain-paper-replication-2026-09-24'
ORIGIN = 'git@github.com:malecada/TradingAgents.git'
FLOOR = 10 * 1024**3
FILE = 4 * 1024**2
START = time.monotonic()
CALLS = []
WATCHES = []
BASELINE = None

def watch(owned_fetch_objects=None):
    global BASELINE
    require(len(WATCHES) < W.POLICY['samples'] and time.monotonic()-START < 600, 'finite whole-tree supervision')
    row = W.census(HERE, owned_fetch_objects=owned_fetch_objects)
    if BASELINE is None: BASELINE = dict(row)
    WATCHES.append(row)
    return row


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(body):
    return hashlib.sha256(body).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def _raise_retained(primary, secondary):
    errors = ([primary] if primary is not None else []) + secondary
    fatal = next((e for e in errors if isinstance(e, MemoryError) or not isinstance(e, Exception)), None)
    if fatal is not None:
        raise fatal
    if primary is not None:
        raise primary
    if secondary:
        raise secondary[0]


def write(path, body):
    watch()
    require(len(body) <= FILE, 'per selected body bound')
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    primary = None
    secondary = []
    try:
        offset = 0
        while offset < len(body):
            n = os.write(fd, body[offset:])
            require(n > 0, 'short write')
            offset += n
        os.fsync(fd)
    except BaseException as error:
        primary = error
    try:
        os.close(fd)
    except BaseException as error:
        secondary.append(error)
    _raise_retained(primary, secondary)
    require(path.read_bytes() == body, 'actual saved-byte readback')
    watch()

def git(args, cwd=ROOT, cap=FILE):
    """Bounded actual Git/SSH group, streaming pipes and independent cleanup."""
    require(time.monotonic() - START < 600 and len(CALLS) < 1024, 'finite recovery budget')
    child = poller = None
    ready_read = ready_write = None
    ready = None
    first = None
    out, err = bytearray(), bytearray()
    begun = time.monotonic()
    code = None
    reaped_exit = None
    env = dict(os.environ)
    env.update({'GIT_TERMINAL_PROMPT': '0', 'GIT_NO_REPLACE_OBJECTS': '1'})
    try:
        watch()
        ready_read, ready_write = os.pipe()
        def limits():
            resource.setrlimit(resource.RLIMIT_FSIZE, (FILE, FILE))
            actual = resource.getrlimit(resource.RLIMIT_FSIZE)
            require(actual == (FILE, FILE), 'actual child hard/soft FSIZE')
            os.write(ready_write, encode({'pid':os.getpid(),'fsize':list(actual)}))
            os.close(ready_write)
        child = subprocess.Popen(['git', *args], cwd=cwd, env=env,
                                 stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, start_new_session=True, preexec_fn=limits, pass_fds=(ready_write,))
        os.close(ready_write); ready_write = None
        ready_raw = os.read(ready_read, 512)
        os.close(ready_read); ready_read = None
        ready = json.loads(ready_raw)
        require(ready == {'pid':child.pid,'fsize':[FILE, FILE]}, 'genuine child OS limit readback')
        poller = selectors.DefaultSelector()
        for stream in (child.stdout, child.stderr):
            os.set_blocking(stream.fileno(), False)
            poller.register(stream, selectors.EVENT_READ)
        while poller.get_map():
            watch(owned_fetch_objects=Path(cwd)/'objects' if args and args[0]=='fetch' and Path(cwd)==HERE/'fresh-serialized-prediction-final-direct01.git' and child.poll() is None else None)
            require(time.monotonic() - begun < 60, '60-second per-operation deadline')
            require(shutil.disk_usage(HERE).free >= FLOOR, '10GiB observed free-space floor')
            for key, event in poller.select(.1):
                body = os.read(key.fileobj.fileno(), 65536)
                if not body:
                    poller.unregister(key.fileobj)
                else:
                    target = out if key.fileobj is child.stdout else err
                    target.extend(body)
                    require(len(target) <= (cap if target is out else 65536), 'streaming response bound')
        code = child.wait(timeout=1)
        require(code == 0, 'actual Git operation failed')
        watch()
    except BaseException as error:
        first = error
    actions = []
    if child is not None:
        def stop_group():
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        def reap():
            nonlocal reaped_exit
            reaped_exit = child.wait(timeout=5)
        actions.extend((stop_group, reap,
                        child.stdout.close, child.stderr.close))
    if poller is not None:
        actions.append(poller.close)
    if ready_read is not None: actions.append(lambda: os.close(ready_read))
    if ready_write is not None: actions.append(lambda: os.close(ready_write))
    actions.append(watch)
    failures = []
    for action in actions:
        try:
            action()
        except BaseException as error:
            failures.append(error)
    CALLS.append({'operation': args[0], 'pid': None if child is None else child.pid,
                  'exit': code, 'actual_reaped_exit': reaped_exit, 'seconds': time.monotonic() - begun, 'actual_child_limits':ready,
                  'stdout_bytes': len(out), 'stderr_bytes': len(err),
                  'stdout_sha256': digest(out), 'stderr_sha256': digest(err),
                  'cleanup_failures': [type(e).__name__ for e in failures]})
    errors = ([first] if first is not None else []) + failures
    fatal = next((e for e in errors if isinstance(e, MemoryError) or not isinstance(e, Exception)), None)
    if fatal is not None:
        raise fatal
    if failures:
        raise RuntimeError('actual owned process cleanup uncertain') from (first or failures[0])
    if first is not None:
        raise first
    return bytes(out)


REQUIRED = {'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-binding-review01-2026-10-05/CURRENT_FLAT_CHECK01.json': {'bytes': 3311, 'sha256': '98a15cb8fb65b958d051e4ee9b6ffee55b59a9136cd49ef174ae109fe6f4ed77'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-binding-review01-2026-10-05/CURRENT_FLAT_ENTRY_RELEASE01.json': {'bytes': 2399, 'sha256': '0acdf6a7ee78d02bf8c6b89be5b4bf92c4782b18ae23da015bcacd42319ea95b'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-binding-review01-2026-10-05/CURRENT_FLAT_SOURCE_CHECK01.json': {'bytes': 3480, 'sha256': '097f84f3d3d9f9c372807c6edc5b4b3fbd6b50f85b2263e97eb133a0bab779b4'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-binding-review01-2026-10-05/CURRENT_REMOTE_CHECK01.json': {'bytes': 1729, 'sha256': '910cf023f1b94823065cb0b03196fd201c27d948c2f52e95b5ddda87622b5c80'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-binding-review01-2026-10-05/CURRENT_REMOTE_ENTRY_RELEASE01.json': {'bytes': 2488, 'sha256': 'f97b80e731d271f47a5d5a1f17b9a67211bb1896d743e1a1b6f90e1ec13d8e5d'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-binding-review01-2026-10-05/CURRENT_REMOTE_SOURCE_CHECK01.json': {'bytes': 2269, 'sha256': '399c0c250ae05052f2c1e0dfbeb033e9c8f614f472185a4c20b4c688d7dd984f'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-binding-review01-2026-10-05/FINAL_METADATA_BUDGET01.json': {'bytes': 99882, 'sha256': 'adbb18d52321eb696f301bd201eeced5df0a51d722e1493dc269c8d948107c3f'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-binding-review01-2026-10-05/FINAL_PARENT_CHECK01.json': {'bytes': 2779, 'sha256': 'c186ed386076698a96eef11768371566151a263908bc45f4315131e12f84bb38'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-binding-review01-2026-10-05/FINAL_PARENT_REVIEW01.json': {'bytes': 677, 'sha256': '6eacb9aad21d7f1de9f0b377dc035ad14b7d9a64e9b5ced68432d99bf25e2b9c'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-binding-review01-2026-10-05/FULL_CURRENT_RECOVERY_PROOF01.json': {'bytes': 2804, 'sha256': '105330459532576a56dc3aee8b035ca411bd058385c2b441f15b705cb431da41'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-current-flat01-2026-10-05/ACTUAL_ROOT_EXIT01.json': {'bytes': 257, 'sha256': 'e845c1adb519d7293563ac0344d7bf87701484f37ae0471ef959a0a550bbe39e'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-current-flat01-2026-10-05/RECOVERY01.json': {'bytes': 1829, 'sha256': 'c1044170db742f5cf7ce7e4be43fa0ddd6c0a701c4f7b020cef920fecc455d8e'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-current-flat01-2026-10-05/flat/body-metadata.json': {'bytes': 26193, 'sha256': '413f183f3fbda824b1fb5733f28eed235644fcf7489cd080569f85bccc35f814'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-current-remote01-2026-10-05/ACTUAL_ROOT_EXIT01.json': {'bytes': 332, 'sha256': '57a5d74dac1a7b9aee93fecd143c0ac2c4dbc8ac9c2a285ab735ee4d5e3ca8e6'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-current-remote01-2026-10-05/REMOTE_RECOVERY01.json': {'bytes': 129529, 'sha256': 'dd8d8265be9b810ccc0a296b7d32f385ef52d83b32277cf4fe524fbceb8237f7'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-current-remote01-2026-10-05/SELECTED_BODIES01.json': {'bytes': 2379, 'sha256': '5af58ad1c97d4ddf3dcf47d421d69078415fd9e1da891544af8a4ddb58efecf6'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-final-direct01-2026-10-05/FINAL_TYPED_SCOPE02.json': {'bytes': 14379, 'sha256': '0ace87f6df2270e8cb7fda94d64d19245a7805df5151b72ab109e3f694f305c0'}, 'research/onchain-paper-replication-2026-09-24/full_sources/heartbeat-root-checkpoint10-2026-10-04/REMOTE_CONFIRMATION78.json': {'bytes': 572, 'sha256': '12f113369fa74dd7e6778ef8e6539af298e09ab7cfa337bde2c45e5035a20f76'}, 'research/onchain-paper-replication-2026-09-24/full_sources/heartbeat-root-checkpoint10-2026-10-04/SERIALIZED_PREDICTION_CURRENT_FLAT01.py': {'bytes': 3297, 'sha256': 'e809b3c71bbf46e7c0f2c92f7798a2dd196aab2649bba9ab2d6850acf34deb01'}, 'research/onchain-paper-replication-2026-09-24/full_sources/heartbeat-root-checkpoint10-2026-10-04/SERIALIZED_PREDICTION_FINAL_BOUND01.json': {'bytes': 1035, 'sha256': '8f99eea196af741c99647ac86e9f7b40dc0dc72f0ba2843f416422af732c3abe'}, 'research/onchain-paper-replication-2026-09-24/full_sources/heartbeat-root-checkpoint10-2026-10-04/SERIALIZED_PREDICTION_FINAL_CANDIDATE01.json': {'bytes': 1069, 'sha256': '7557db36635c5d0742b11ab4996baf6816297e642c65b70c19cd0e64716d0b96'}, 'research/onchain-paper-replication-2026-09-24/full_sources/heartbeat-root-checkpoint10-2026-10-04/SERIALIZED_PREDICTION_REQUEST_FINAL_COPY01.json': {'bytes': 140444, 'sha256': 'a1bb2267b835a36117f67422a3451da99e0b740e8e41911d2fc63a8e8e270bc2'}, 'research/onchain-paper-replication-2026-09-24/full_sources/heartbeat-root-checkpoint10-2026-10-04/SERIALIZED_PREDICTION_REQUEST_RELEASE_CANDIDATE_COPY01.json': {'bytes': 140138, 'sha256': '31473cd5079466d458292249b4f88c479377cec944f9648c18465756d8e9075f'}}
FINAL_POPULATION_COUNT = 23

def validate_fixed_selection(selection):
    require(type(selection) is dict and set(selection)=={'remote_commit','rows'}, 'exact selection schema')
    require(type(REQUIRED) is dict and type(FINAL_POPULATION_COUNT) is int, 'unreleased final population')
    rows=selection['rows'];require(type(rows) is list and len(rows)==len(REQUIRED)==FINAL_POPULATION_COUNT, 'exact fixed final selected paths')
    by={}
    for row in rows:
        require(type(row) is dict and set(row)=={'path','bytes','sha256'}, 'selected row schema')
        n=row['path'];require(type(n)is str and n.startswith('research/') and Path(n).as_posix()==n and '..' not in Path(n).parts and n not in by, 'selected safe unique path')
        require(type(row['bytes'])is int and 0<=row['bytes']<=FILE and type(row['sha256'])is str and len(row['sha256'])==64 and all(c in '0123456789abcdef' for c in row['sha256']), 'exact selected body pin')
        by[n]=row
    for n,pin in REQUIRED.items():require(by.get(n)==dict(path=n,**pin), 'current capture selection absent/changed')

def main():
    global COMMIT
    parser = argparse.ArgumentParser()
    parser.add_argument('--selection-sha256', required=True)
    args = parser.parse_args()
    selection_body = (HERE / 'SELECTED_BODIES01.json').read_bytes()
    require(digest(selection_body) == args.selection_sha256, 'explicit frozen selection pin')
    selection = json.loads(selection_body)
    COMMIT = selection['remote_commit']
    require(type(COMMIT) is str and len(COMMIT) == 40 and all(c in '0123456789abcdef' for c in COMMIT), 'commit pin')
    require(encode(selection) == selection_body, 'frozen canonical selection')
    validate_fixed_selection(selection)
    rows = selection['rows']
    require(1 <= len(rows) <= 506 and sum(r['bytes'] for r in rows) <= 64 * 1024**2, 'selected logical bound')
    require([r['path'] for r in rows] == sorted(set(r['path'] for r in rows)), 'selected unique sorted scope')
    require(git(['remote', 'get-url', 'origin']).decode().strip() == ORIGIN, 'actual configured origin join')
    actual = git(['ls-remote', 'origin', BRANCH]).decode().split()
    require(actual == [COMMIT, BRANCH], 'actual remote HEAD join')
    repo = HERE / 'fresh-serialized-prediction-final-direct01.git'
    require(not os.path.lexists(repo), 'fresh Git namespace absent')
    git(['init', '--bare', str(repo)])
    git(['remote', 'add', 'origin', ORIGIN], repo)
    git(['config', 'remote.origin.promisor', 'true'], repo)
    git(['config', 'remote.origin.partialclonefilter', 'blob:none'], repo)
    git(['fetch', '--depth=1', '--filter=blob:none', '--no-tags', 'origin', COMMIT], repo)
    require(git(['rev-parse', 'FETCH_HEAD'], repo).decode().strip() == COMMIT, 'fresh fetched commit join')
    tree = git(['ls-tree', '-r', '-z', COMMIT, '--', *[r['path'] for r in rows]], repo, cap=FILE)
    objects = {}
    for item in tree.split(b'\0')[:-1]:
        left, name = item.split(b'\t', 1)
        mode, kind, oid = left.decode().split()
        objects[name.decode()] = (mode, kind, oid)
    wanted = sorted(set(objects[r['path']][2] for r in rows))
    require(len(wanted) <= 506, 'finite selected Git object union')
    for oid in wanted:
        git(['fetch', '--no-tags', 'origin', oid], repo)
    recovered = []
    for row in rows:
        name = row['path']
        require(name.startswith('research/') and Path(name).as_posix() == name and '..' not in Path(name).parts, 'selected path scope')
        mode, kind, oid = objects[name]
        require(mode in ('100644', '100755') and kind == 'blob', 'selected actual Git file')
        require(0 <= row['bytes'] <= FILE, 'selected size pin')
        size = int(git(['cat-file', '-s', oid], repo).decode())
        require(size == row['bytes'], 'actual immutable object size before body read')
        body = git(['cat-file', 'blob', oid], repo, cap=FILE)
        require(len(body) == size and digest(body) == row['sha256'], 'actual remote selected body pins')
        require(hashlib.sha1(b'blob ' + str(size).encode() + b'\0' + body).hexdigest() == oid, 'actual Git blob OID')
        require((ROOT / name).read_bytes() == body, 'original-to-remote exact body join')
        write(HERE / 'selected' / name, body)
        recovered.append(dict(row, git_mode=mode, git_object=oid))
    final = git(['ls-remote', 'origin', BRANCH]).decode().split()
    require(final == [COMMIT, BRANCH], 'final actual remote HEAD join')
    require(shutil.disk_usage(HERE).free >= FLOOR, 'final10GiBfloor')
    require(len(CALLS) == 10 + len(wanted) + 2*len(rows), 'exact finite operation denominator')
    watch()
    receipt = {'whole_tree_policy':dict(W.POLICY),'initial_owned_allocation':BASELINE,'whole_tree_observations':list(WATCHES),'unique_selected_objects':len(wanted),'expected_operations':10+len(wanted)+2*len(rows),'schema_version': 1, 'status': 'fresh-actual-serialized-prediction-final-direct01-recovered',
               'remote_commit': COMMIT, 'origin': ORIGIN, 'branch': BRANCH,
               'selection_sha256': digest(selection_body), 'selected_blobs': recovered,
               'selected_count': len(recovered), 'selected_logical_bytes': sum(r['bytes'] for r in rows),
               'fresh_git_root': str(repo), 'operations': CALLS, 'elapsed_seconds': time.monotonic() - START,
               'free_bytes': shutil.disk_usage(HERE).free, 'genuine_run_or_native_started': False,
               'qualification': 'Actual complete released-envelope direct byte supplement, exact final request/review/fullcurrent proof and every new referenced receipt/check, with explicit original typed path/mode metadata. Accepted current CAP/Git/Parent and recovered historical byte bases remain pinned. No second archive/flat or unchanged-body recopy. Fresh actual selected-body recovery plus independent joins is required. No POSIX reconstruction, installed runtime package recovery, immutable writer exclusion or numerical/paper-fit capacity claim.'}
    write(HERE / 'REMOTE_RECOVERY01.json', encode(receipt))
    print(json.dumps({k: receipt[k] for k in ('status', 'remote_commit', 'selected_count', 'selected_logical_bytes', 'elapsed_seconds')}))


def entry():
    try:
        main()
    except BaseException as error:
        primary = error
        secondary = []
        try:
            write(HERE / 'FAILED01.json', encode({'status': 'failed-original-attempt', 'error_type': type(primary).__name__,
                  'error': str(primary), 'operations': CALLS, 'initial_owned_allocation': BASELINE,
                  'whole_tree_observations': list(WATCHES), 'whole_tree_policy': dict(W.POLICY),
                  'genuine_run_or_native_started': False}))
        except BaseException as journal_error:
            secondary.append(journal_error)
        _raise_retained(primary, secondary)


if __name__ == '__main__':
    entry()