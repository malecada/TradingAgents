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
import space01 as W

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

def watch():
    global BASELINE
    require(len(WATCHES) < W.POLICY['samples'] and time.monotonic()-START < 600, 'finite whole-tree supervision')
    row = W.census(HERE)
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
            watch()
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


REQUIRED = {'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-baseline-recovery-review02-2026-10-05/BASELINE_FULL_RECOVERY_PROOF01.json': {'bytes': 1343, 'sha256': '02900ae11c7053a5f691ef2838fa7427b5befd86778331c19b97143e1c6c2e48'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/CAPTURE01.json': {'bytes': 705237, 'sha256': 'ef82889318080bf2fec673d6c558c4afe3d95260c1a4d783c9b5eb16d8979442'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-020.json': {'bytes': 2351, 'sha256': '576d3c2712cd7feaf361e987f4526cda0c668e650cba6fa4759889d9e6e2d0c9'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-020.tar.gz': {'bytes': 2737342, 'sha256': '1c8f36102143c5ac3403ecb7126505fedcc23e2065a0527a523898bc3b721e97'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-021.json': {'bytes': 2351, 'sha256': '144e88fd3b009236f1207bd56ee2bcbebf88f7fbc65ecc6b239dcb2a51b27be1'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-021.tar.gz': {'bytes': 2735079, 'sha256': '1fe11ade1ec145f99728a67b9f1f3a6224526e0267fec43a46da66693ab1e1d9'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-022.json': {'bytes': 2351, 'sha256': 'dff0d5a9fff4c681d2396dd9f61a262ac6697cc308e490062f29b482b178f372'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-022.tar.gz': {'bytes': 2736449, 'sha256': '30cd41010838072462a2420685be64d921eec3368a53ebec842fbb054afc43c6'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-023.json': {'bytes': 2351, 'sha256': '28100396a9491d7cea0b95acb339b5e391b45192b903539fbe7beb3dd0218cce'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-023.tar.gz': {'bytes': 2732907, 'sha256': 'e34b24062bfb53d9e7fd748b107b629ae48cddd779a73a5f216afb7049e6144e'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-024.json': {'bytes': 33887, 'sha256': 'fc0cc100573faaa9fc5fd1ba844e52f8595f570ebbe86eebee124bb0ffae94b2'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-024.tar.gz': {'bytes': 1780020, 'sha256': 'e3286dbb2ca6c510ce0ccf9910f212de3ae08acf11ca1dff94d85b30f5bb8c88'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-025.json': {'bytes': 9134, 'sha256': 'b6e0e4a29f6e69b9cbedb574625a9b02c25973cdcbd42f39c713726d65b1eb81'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-025.tar.gz': {'bytes': 592252, 'sha256': '08b10c003084f67f6939851c73a2af7b188a87ec940f702e4fc05ec69c05fc43'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-review01-2026-10-05/CLEANUP_PROOF01.json': {'bytes': 2968, 'sha256': '67d74e5ac68b9957f5e116753730eb698d6167141f0d61dfda558dd424e69e23'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-review01-2026-10-05/MACHINE01.json': {'bytes': 1459, 'sha256': '27e29cab0b784748bdd0fef2ca484215b39b2b025784a469de443f619ae9b124'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-recovery-outcome-review02-2026-10-05/ACTUAL_CAPTURE_REVIEW02.json': {'bytes': 333797, 'sha256': '55539547260a1d8cbbd22bcbd2a60d27cd00a4392ea95f627efda965c1c0e2e0'}}
FINAL_POPULATION_COUNT = 17

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
    repo = HERE / 'fresh-compatibility-complete100-outcome-lane04-canonical02.git'
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
    receipt = {'whole_tree_policy':dict(W.POLICY),'initial_owned_allocation':BASELINE,'whole_tree_observations':list(WATCHES),'unique_selected_objects':len(wanted),'expected_operations':10+len(wanted)+2*len(rows),'schema_version': 1, 'status': 'fresh-actual-remote-compatibility-complete100-outcome-lane04-canonical02-supervised-recovered',
               'remote_commit': COMMIT, 'origin': ORIGIN, 'branch': BRANCH,
               'selection_sha256': digest(selection_body), 'selected_blobs': recovered,
               'selected_count': len(recovered), 'selected_logical_bytes': sum(r['bytes'] for r in rows),
               'fresh_git_root': str(repo), 'operations': CALLS, 'elapsed_seconds': time.monotonic() - START,
               'free_bytes': shutil.disk_usage(HERE).free, 'genuine_run_or_native_started': False,
               'qualification': 'Exact one of four disjoint complete100 outcome archive lanes; common complete capture and original outcome proofs retained. Separate accepted605/407 source basis is referenced, not reconstructed here. No claim is started and no scientific completion follows. Every receiver child inherits actual-readback hard/soft4MiB FSIZE; entire owned tree including baseline sampled at fixed64MiB logical/96MiB allocated/32768members/depth32. Single-blob fetches and exact dynamic unique-object operation denominator; transient aggregate/physical wire not measured. No numerical/runtime/POSIX/capacity authority.'}
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