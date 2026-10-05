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
            watch(owned_fetch_objects=Path(cwd)/'objects' if args and args[0]=='fetch' and Path(cwd)==HERE/'fresh-serialized-storage-final-direct01.git' and child.poll() is None else None)
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


REQUIRED = {'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-review01-2026-10-05/CURRENT_FLAT_CHECK01.json': {'bytes': 4060, 'sha256': 'f3088b940798c4c341bab94de9002b4d50e6e67853ff841c9b2af88ab0a16e58'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-review01-2026-10-05/CURRENT_FLAT_ENTRY_RELEASE01.json': {'bytes': 2356, 'sha256': '4b8cee12c66588b34c1e22e6938604bfbd2f7f7a52df88d70029807f5115eb3f'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-review01-2026-10-05/CURRENT_FLAT_SOURCE_CHECK01.json': {'bytes': 1066, 'sha256': '00180f880962e6133f6e724dbc99301a996dd34be328450dfc2eaba0da8fbef5'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-review01-2026-10-05/CURRENT_REMOTE_CHECK01.json': {'bytes': 1376, 'sha256': 'd8f95fd1173bc569c411f096e06bc726d6f97e26161bc107c30b1b38b95b93b9'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-review01-2026-10-05/CURRENT_REMOTE_ENTRY_RELEASE01.json': {'bytes': 2251, 'sha256': '97409568c86ea04a2282a26abe5d441666aaf9dc7aaa83b9ba743061798bdc6d'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-review01-2026-10-05/CURRENT_REMOTE_SOURCE_CHECK01.json': {'bytes': 1212, 'sha256': 'db7aeef37fd0a41cdd88f85ba8d5735adb41c74bc8cb4c4983072dedb3a5939d'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-review01-2026-10-05/FINAL_PARENT_CHECK01.json': {'bytes': 2909, 'sha256': 'addb9722d5290bedcfb9f8be41918967256136f8e572f2439d907eded189a281'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-review01-2026-10-05/FINAL_PARENT_REVIEW01.json': {'bytes': 681, 'sha256': 'ec19a68e546fda0bb9010a055798408a9605c619ba0edf9af1bbb657e41d8f9f'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-review01-2026-10-05/FULL_CURRENT_RECOVERY_PROOF01.json': {'bytes': 2656, 'sha256': '3aef2b627c679d753a43b7055ea412fcf55a34b3e51d82afbe666c6c45a245b9'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-current-flat01-2026-10-05/ACTUAL_ROOT_EXIT01.json': {'bytes': 280, 'sha256': '3b19cb8332c2d1ca3f2e126a0e873c4043e672a1b3b739367029efd40c03ca97'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-current-flat01-2026-10-05/RECOVERY01.json': {'bytes': 1822, 'sha256': '25d7a7d2672124ae882135f9444b25b15d0b0966389e01357d6da9754f1f78e7'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-current-flat01-2026-10-05/flat/body-metadata.json': {'bytes': 22437, 'sha256': '571e0d121a152cb1ecbbd97dafaaca43134dd49fb23d7c0ad92d4273c071c77c'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-current-remote01-2026-10-05/ACTUAL_ROOT_EXIT01.json': {'bytes': 342, 'sha256': '8063a6e37f13838dcd621cc05e4fc4c8b0c879cd3765c69cf2ec52827031b6e4'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-current-remote01-2026-10-05/REMOTE_RECOVERY01.json': {'bytes': 138344, 'sha256': '396905dc9906c6c136ec1ce9e2eaa6a6a3bd78e1262d215c47c67024a1ac6aad'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-current-remote01-2026-10-05/SELECTED_BODIES01.json': {'bytes': 2329, 'sha256': '5fae617cf7acc5b35224b7c3c0444960d5bc30e252d705963c5a513f1bebe012'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-final-direct01-2026-10-05/FINAL_TYPED_SCOPE01.json': {'bytes': 11883, 'sha256': '49d562d38330b03ab512b34c34fb31518a4a0cc5252242bb4938ffca9b485f18'}, 'research/onchain-paper-replication-2026-09-24/full_sources/heartbeat-root-checkpoint10-2026-10-04/REMOTE_CONFIRMATION73.json': {'bytes': 586, 'sha256': 'df8ea791a246f30db53b022632652f98880d3d0b69ef565f3be9fabc8a4ac521'}, 'research/onchain-paper-replication-2026-09-24/full_sources/heartbeat-root-checkpoint10-2026-10-04/SERIALIZED_CURRENT_FLAT01.py': {'bytes': 3282, 'sha256': '9fe78b0f9420768082b746f11fe7bfb6938c5f8485669ecce6cfb8f75505f76c'}, 'research/onchain-paper-replication-2026-09-24/full_sources/heartbeat-root-checkpoint10-2026-10-04/SERIALIZED_FINAL_REQUEST_REVIEW_DRAFT01.json': {'bytes': 123371, 'sha256': 'ba6b330ba941f0cb5414439056896c6e3fa5ded86bb77e25c9297e9d65529afc'}, 'research/onchain-paper-replication-2026-09-24/full_sources/heartbeat-root-checkpoint10-2026-10-04/SERIALIZED_REQUEST_FINAL_COPY01.json': {'bytes': 123659, 'sha256': '832336399cb52e595022c190f6564aba63197d8ce93a4aa67e8f7a4af5039a4e'}}
FINAL_POPULATION_COUNT = 20

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
    repo = HERE / 'fresh-serialized-storage-final-direct01.git'
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
    receipt = {'whole_tree_policy':dict(W.POLICY),'initial_owned_allocation':BASELINE,'whole_tree_observations':list(WATCHES),'unique_selected_objects':len(wanted),'expected_operations':10+len(wanted)+2*len(rows),'schema_version': 1, 'status': 'fresh-actual-remote-compatibility-final-bundle01-supervised-recovered',
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