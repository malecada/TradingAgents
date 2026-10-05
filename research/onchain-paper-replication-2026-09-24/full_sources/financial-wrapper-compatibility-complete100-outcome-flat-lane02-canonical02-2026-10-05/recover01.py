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


REQUIRED = {'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-baseline-recovery-review02-2026-10-05/BASELINE_FULL_RECOVERY_PROOF01.json': {'bytes': 1343, 'sha256': '02900ae11c7053a5f691ef2838fa7427b5befd86778331c19b97143e1c6c2e48'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/CAPTURE01.json': {'bytes': 705237, 'sha256': 'ef82889318080bf2fec673d6c558c4afe3d95260c1a4d783c9b5eb16d8979442'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-007.json': {'bytes': 2351, 'sha256': '333e09517742c2eedf9360b76040c3fe0b6e4c78f990bfe1eb0c957180339d67'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-007.tar.gz': {'bytes': 2723528, 'sha256': '4fa82e3c49918ed21cf038f50b06eadf29c767d9230c124dd4e1edd352e9b023'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-008.json': {'bytes': 2351, 'sha256': '1c8992babae5687154d9e43144e41a737d749f19ae4a2b04590a4cf5c45ed7bb'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-008.tar.gz': {'bytes': 2729464, 'sha256': 'e8619a6f2195bdadeee9a81cd2134b917e1804fdc476ca5164017eac1645eb78'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-009.json': {'bytes': 2351, 'sha256': 'b49b737d56f260231c4a3028ec6167d3d30dc74429e314a304c193c098ed5d83'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-009.tar.gz': {'bytes': 2721250, 'sha256': 'e9923e89f8d4a57c5fca7c613378ceea9622893603e49a3b170fa90c9e635616'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-010.json': {'bytes': 2351, 'sha256': '547fe7d4925fa355a06894da52a8e15126f70f6a56167a89f57efa9f00f1cc28'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-010.tar.gz': {'bytes': 2723413, 'sha256': 'b4a23de7bb44e813437f6a14269d74bef2734da07a056c5849a8206d21cc8ee7'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-011.json': {'bytes': 2351, 'sha256': 'c467422eae74c47e7049b81c8c1ba759c8055f4d429dfcab140a81133797b051'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-011.tar.gz': {'bytes': 2727564, 'sha256': '0b7cbb3926f720a936991c567663b44e92b189c738691b1a9ea50de17ffc7be7'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-012.json': {'bytes': 2351, 'sha256': '8004c6d0acd2d7336564b1e36554c2d4ca7547754a2d83f2220e4d1609b278e7'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-012.tar.gz': {'bytes': 2727497, 'sha256': '09cde0aa36cf6ee2c6e89bef1c1ae91e301dcb9ef38fbc322c585805bc0d432f'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-013.json': {'bytes': 2351, 'sha256': 'cce77341b4dcc1029132299e84272e09b3b1f545d52d9d6b8ce3f2b8a10eed1c'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-013.tar.gz': {'bytes': 2730811, 'sha256': '60d7206b3eeedec844fbf6e63ef69524cdd3dea8496414098a201f38b123a1a0'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-review01-2026-10-05/CLEANUP_PROOF01.json': {'bytes': 2968, 'sha256': '67d74e5ac68b9957f5e116753730eb698d6167141f0d61dfda558dd424e69e23'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-review01-2026-10-05/MACHINE01.json': {'bytes': 1459, 'sha256': '27e29cab0b784748bdd0fef2ca484215b39b2b025784a469de443f619ae9b124'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-recovery-outcome-review02-2026-10-05/ACTUAL_CAPTURE_REVIEW02.json': {'bytes': 333797, 'sha256': '55539547260a1d8cbbd22bcbd2a60d27cd00a4392ea95f627efda965c1c0e2e0'}}
FINAL_POPULATION_COUNT = 19

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
    repo = HERE / 'fresh-compatibility-complete100-outcome-lane02-canonical02.git'
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
    receipt = {'whole_tree_policy':dict(W.POLICY),'initial_owned_allocation':BASELINE,'whole_tree_observations':list(WATCHES),'unique_selected_objects':len(wanted),'expected_operations':10+len(wanted)+2*len(rows),'schema_version': 1, 'status': 'fresh-actual-remote-compatibility-complete100-outcome-lane02-canonical02-supervised-recovered',
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