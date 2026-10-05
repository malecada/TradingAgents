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


REQUIRED = {'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-baseline-recovery-review02-2026-10-05/BASELINE_FULL_RECOVERY_PROOF01.json': {'bytes': 1343, 'sha256': '02900ae11c7053a5f691ef2838fa7427b5befd86778331c19b97143e1c6c2e48'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/CAPTURE01.json': {'bytes': 705237, 'sha256': 'ef82889318080bf2fec673d6c558c4afe3d95260c1a4d783c9b5eb16d8979442'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-000.json': {'bytes': 17420, 'sha256': 'c67add47833c41d258e9acafb62830e8d79910a5f5ecf1b528e7fb89f31b927b'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-000.tar.gz': {'bytes': 631275, 'sha256': 'df2c47de913293d4e9493b16837ea3b7a742dea93444bdb7d308a5f730d36bba'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-001.json': {'bytes': 22388, 'sha256': '9f3bb67ac5d83ed84f7f0284b0504f3055dab72483ee66972797ee25b084b8b5'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-001.tar.gz': {'bytes': 1030548, 'sha256': '09f71b873da53c75ba003524a3c4583196bcb7f9cbd9488c5252756c92fd23cb'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-002.json': {'bytes': 9307, 'sha256': 'f41a1c192f0aff4484144cca3e5ebf015a9951db67c5929dca22d48994f77a20'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-002.tar.gz': {'bytes': 1040759, 'sha256': 'ad1555e6d7e656fb48262777604524bd3ec3e505e764476b527831e435cfb53c'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-003.json': {'bytes': 2351, 'sha256': '44f38fe7788d025d6deab59c0b2041e4ec86d698171875f1c09375d61247dbcf'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-003.tar.gz': {'bytes': 2723665, 'sha256': '04a878b2f2b54f6b15f1a957d30510744de86de8098b514f92fe0c598c9f6ecc'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-004.json': {'bytes': 2351, 'sha256': '6f983f4270d36b39d98f8c9679c5b12a66b2b7182e3fa5a50800842dfc941ba0'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-004.tar.gz': {'bytes': 2724587, 'sha256': '0ce20f9704e6b375b7afc221713424d0b5f786f16733114c4cc5d2a56cb95af3'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-005.json': {'bytes': 2351, 'sha256': 'c0d75b67b72a3281a44184dda9fa18760bf5eade33ade0848cb999168591776c'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-005.tar.gz': {'bytes': 2722753, 'sha256': '9ec1580f660bb06a1878d98aac9c963c277abc45081a2722c45f1b6a358dfb30'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-006.json': {'bytes': 2351, 'sha256': 'cfef7aeb9be7b1b7556e80b9852df94710772dc4b0b42ebdb90f6dbd166c429d'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/piece-006.tar.gz': {'bytes': 2730465, 'sha256': '731f66fe7c671b7d7842c16683fef5c1156fd5718bf746435acbad0ef0f9bbdf'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-review01-2026-10-05/CLEANUP_PROOF01.json': {'bytes': 2968, 'sha256': '67d74e5ac68b9957f5e116753730eb698d6167141f0d61dfda558dd424e69e23'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-review01-2026-10-05/MACHINE01.json': {'bytes': 1459, 'sha256': '27e29cab0b784748bdd0fef2ca484215b39b2b025784a469de443f619ae9b124'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-recovery-review01-2026-10-05/ACTUAL_CAPTURE_REVIEW01.json': {'bytes': 1143, 'sha256': '5db589619e8df5cec1755ebc3a36bffa2d3a8cd3e4c66e41e8d68bc9befc7b18'}}
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
    repo = HERE / 'fresh-compatibility-complete100-outcome-lane01.git'
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
    receipt = {'whole_tree_policy':dict(W.POLICY),'initial_owned_allocation':BASELINE,'whole_tree_observations':list(WATCHES),'unique_selected_objects':len(wanted),'expected_operations':10+len(wanted)+2*len(rows),'schema_version': 1, 'status': 'fresh-actual-remote-compatibility-complete100-outcome-lane01-supervised-recovered',
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