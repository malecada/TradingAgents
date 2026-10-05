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
            watch(owned_fetch_objects=Path(cwd)/'objects' if args and args[0]=='fetch' and Path(cwd)==HERE/'fresh-serialized-storage-source01.git' and child.poll() is None else None)
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


REQUIRED = {'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-review01-2026-10-05/BUDGET_CHECK01.json': {'bytes': 757, 'sha256': 'd62f84759613c5ae8aff0016f2e02947d896fc4831629f16a4da997baeb543f4'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-review01-2026-10-05/REPORT01.md': {'bytes': 1815, 'sha256': '5a9280c5973c93a0f6add9deb396f960ac4877e486f0ab11264cd7fc8888f571'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-review01-2026-10-05/SOURCE_CHECK01.json': {'bytes': 3006, 'sha256': 'b9e35ba2ba1a98d219f5a55bba24648df03cfa668dcd002033eb1c274398731c'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-review01-2026-10-05/SOURCE_REVIEW_PROOF01.json': {'bytes': 610, 'sha256': 'a6e7e6ce57d2b8efb7098a64a9d8bc7a24cb007cb8d1754c3423ea5478398bc3'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-review01-2026-10-05/check_source01.py': {'bytes': 9051, 'sha256': 'e2c43b76513150b924378e2cb8c96353b608a85c539d7d4c2813299aef2ef0e8'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-source01-2026-10-05/MACHINE01.json': {'bytes': 1466, 'sha256': 'bb855f45597e0436bf1b2bac90a9111bd387a58aee76a03eebaf46758fb26508'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-source01-2026-10-05/MANIFEST01.json': {'bytes': 2542, 'sha256': 'e97d4e2b00e73165cf35d29d0fd9669f2be73c8bb0af227b118b449c236660b0'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-source01-2026-10-05/REPORT01.md': {'bytes': 5080, 'sha256': 'e7d35c5f6f539f18ad944c78e1475d43ceb9f1ba3ff92999572a24c5cd7204b3'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-source01-2026-10-05/SOURCE_DELTA01.json': {'bytes': 731, 'sha256': '2a2f15a08ba957cb66637fafd3cff607947ba1e6b73dfaf7dcb27c08d85586f2'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-source01-2026-10-05/TEST_OUTPUT01.txt': {'bytes': 1375, 'sha256': '26fe2793af87cd72ce7c5174481bacd8f5ab7123d48f18b516eca9ec09752dd3'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-source01-2026-10-05/financial_wrapper_fixture.py': {'bytes': 42812, 'sha256': '4453e2acf216b056b429cab3cf25901594c08cf8ccf62b551ef80717a248bc45'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-source01-2026-10-05/operational_source_compatibility.py': {'bytes': 59320, 'sha256': 'a775caf89d19c881824e02915b07f1cfa045c1818d3ea927698b24c86159e93e'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-source01-2026-10-05/operational_source_compatibility.py.ndiff': {'bytes': 61056, 'sha256': '7722f7a669cda7e120c1935ff4c13e9f4f7fd3dab34fd1ec353745d176272412'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-source01-2026-10-05/operational_source_compatibility.py.patch': {'bytes': 6997, 'sha256': '8cf6a3be1c6d581ed0c5b1142d732c270700989798df1b6b0eac23f46d0ef44d'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-source01-2026-10-05/preclaim01.py': {'bytes': 46663, 'sha256': 'a3a22e972c182251f23d1f8d1261380973b34a7cc689cf6902511adb8d9a7c6e'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-source01-2026-10-05/preclaim01.py.ndiff': {'bytes': 47764, 'sha256': '1d50fee577cbd6034f9df437246dccb028cd4998f367d66bcc2cfa19a788caa5'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-source01-2026-10-05/preclaim01.py.patch': {'bytes': 408, 'sha256': '95ad0e1ace33ef16cccf564d3cb4c67a2ff418fd1b70e051c007ff213223b112'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-binding-source01-2026-10-05/test_successor.py': {'bytes': 11586, 'sha256': '4370056a6e16d2c8c9cf918472ee98e3b4dbb3750ace90beb431589fbce06cf5'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-root-preparation01-2026-10-05/GATES_UNBOUND_DRAFT01.json': {'bytes': 284481, 'sha256': '40475410050d9b2b489274b0cb4806d1c486f3a7082318a7b8c246a8b8fbc240'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-root-preparation01-2026-10-05/INPUT_BINDINGS01.json': {'bytes': 883, 'sha256': '2cf064bea843c5a255a06865d5b992fc0517d597193f8f8edd6f32869ffb5fbf'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-root-preparation01-2026-10-05/PREPARATION01.json': {'bytes': 1276, 'sha256': 'f5edfcb12e0b263fca9595bc05b54f7b6bd0b62853d913ce1f562ea57b8be229'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-root-preparation01-2026-10-05/REQUEST_UNBOUND_DRAFT01.json': {'bytes': 80189, 'sha256': 'b32894c2ef8123adb90f3c3414ee519a6ecec8ca317cd31e812e1817ea3209be'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-root-preparation01-2026-10-05/continue-plan.json': {'bytes': 701, 'sha256': 'cdbf717bde5910291ff0afda0b20243778f89f9439f0ec213ddbeaaf5f63f2e3'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-root-preparation01-2026-10-05/fixture_inputs/financial_wrapper_serialized_storage01/continue-plan.json': {'bytes': 701, 'sha256': 'cdbf717bde5910291ff0afda0b20243778f89f9439f0ec213ddbeaaf5f63f2e3'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-root-preparation01-2026-10-05/fixture_inputs/financial_wrapper_serialized_storage01/previous-recovery.json': {'bytes': 3104, 'sha256': 'bdf0f39710054d34f2274eec35a192dc13200ff146b4a79d3f4822235efba7df'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-root-preparation01-2026-10-05/fixture_inputs/financial_wrapper_serialized_storage01/refusal.json': {'bytes': 7210, 'sha256': '2263ea2cd9f6e6b2fe6100498a917fb971328d9e4ae3478e4f544a07f93d908b'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-root-preparation01-2026-10-05/fixture_inputs/financial_wrapper_serialized_storage01/source_closure.json': {'bytes': 26554, 'sha256': '16f05d94c9419aad6072a68da78eb0a305e87c3757e8517aae7da46a10a5b610'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-root-preparation01-2026-10-05/fixture_inputs/financial_wrapper_serialized_storage01/successor.json': {'bytes': 27238, 'sha256': 'f5b6521770ba21dc33c42816093e97739dca51b3abc7e53c4b5c48630fe9ec28'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-storage-root-preparation01-2026-10-05/parent-unbound01.py': {'bytes': 26151, 'sha256': '57c61bbdc298e7a98e1366ead1b014106d32cf7ec9a6600596fa8d2b66a49a49'}}
FINAL_POPULATION_COUNT = 29

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
    repo = HERE / 'fresh-serialized-storage-source01.git'
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
               'qualification': 'Actual fresh serialized-storage source/preparation/review bytes only. Original195 installed source map ancestry and terminal2263/bdf/a535 remain separately authenticated. Null unbound drafts confer no current-source/native/claim/financial/paper-fit or complete-capsule recovery authority. Receiver guards unchanged.'}
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