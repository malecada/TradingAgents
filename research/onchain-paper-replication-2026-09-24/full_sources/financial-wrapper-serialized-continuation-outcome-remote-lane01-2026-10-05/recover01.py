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
            watch(owned_fetch_objects=Path(cwd)/'objects' if args and args[0]=='fetch' and Path(cwd)==HERE/'fresh-serialized-continuation-outcome-lane01.git' and child.poll() is None else None)
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


REQUIRED = {'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/INCREMENT01.json': {'bytes': 1540, 'sha256': '06bcb379ed9a97e669d4c39c54a00e8562c13181e388ac1690915f34d906d521'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/shards/CAPTURE01.json': {'bytes': 195064, 'sha256': 'b1bcc9afbc3ce2516eaec8f182d726e975de90b1ee0e96f050846e32d14713fb'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/shards/piece-000.json': {'bytes': 1015, 'sha256': 'cac5e8f3b777054eed693926b7cc57c9ffda649d2e7036b583e7e9fc82268a42'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/shards/piece-000.tar.gz': {'bytes': 620888, 'sha256': '4a1f0b59e935ff7605ee34d583bd6dfdd24c022bd5bd87669c25a11d42483ab7'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/shards/piece-001.json': {'bytes': 3848, 'sha256': '648170b77e9afa248289a6443065db3a323cc9ef884be0610a330bedbe76258f'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/shards/piece-001.tar.gz': {'bytes': 1489328, 'sha256': 'd3ee240a3d8b72291fa2f8c866d487b885b0fafa177d972b913ce7a1d70336a2'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/shards/piece-002.json': {'bytes': 2351, 'sha256': 'fad4738d64ef2fac5bb52142218fa20f9efccccc650ffaf0951123d720b793f1'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/shards/piece-002.tar.gz': {'bytes': 2720876, 'sha256': '7cc0d177f26b014b003cd8f9df273151bec32cb696b5da3a8c7d1025287710dc'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/shards/piece-003.json': {'bytes': 2351, 'sha256': 'b2cb19a7b4090e7aab3229b37d537acfb2357157eebee49a2c3963c1380d005f'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/shards/piece-003.tar.gz': {'bytes': 2727359, 'sha256': '07a24b34e469867fa29eb341cda3919358cbc819460699f6cc8a9859d988fa5a'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/shards/piece-004.json': {'bytes': 2351, 'sha256': '1a7807f2027b417056d545588e97856fcacf24b43bfe18e9dd9631828fc285b8'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/shards/piece-004.tar.gz': {'bytes': 2725606, 'sha256': 'dade44c1e49f950ee6d9e575368cd6b07d54c4e224e2cc09fe367ea589d5f5bd'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/shards/piece-005.json': {'bytes': 2351, 'sha256': '37fbb958901d6cad52eb25bb0b3886620dafaa8261baf870a7a29800a239117f'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/shards/piece-005.tar.gz': {'bytes': 2729639, 'sha256': 'c2994ee20778d1015fd8d55a0485b8574b52f2949ff4c4085180013deaf117fd'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-review01-2026-10-05/CAPTURE_CHECK01.json': {'bytes': 3503, 'sha256': 'd77363ac5fe542438406ac6f87944f1ea0f0749f59e9bd882a4b9e44369ac2ee'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-review01-2026-10-05/CAPTURE_ENTRY_RELEASE01.json': {'bytes': 4804, 'sha256': '608c4abe57471df7d476b99d28254e86ba2617969f282ce84eec26049ac7fefa'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-review01-2026-10-05/CAPTURE_FINDING01.json': {'bytes': 924, 'sha256': '66726447932c7d43527fb9aeb77861a40ba09401d07003b882b73b211019397b'}, 'research/onchain-paper-replication-2026-09-24/full_sources/heartbeat-root-checkpoint10-2026-10-04/SERIALIZED_OUTCOME_CAPTURE01.py': {'bytes': 10396, 'sha256': 'fb17fe36e7ce5d64813b1fa9098de36262f8174838d16781d09746d0a2af2d5b'}, 'research/onchain-paper-replication-2026-09-24/full_sources/heartbeat-root-checkpoint10-2026-10-04/SERIALIZED_OUTCOME_CAPTURE01_WITHHELD.json': {'bytes': 291, 'sha256': '7d1b25c578afae78eafda5d9ee44428384214a8a8955f3fd18a8403f312fdce0'}, 'research/onchain-paper-replication-2026-09-24/full_sources/heartbeat-root-checkpoint10-2026-10-04/SERIALIZED_OUTCOME_CAPTURE02.patch': {'bytes': 6934, 'sha256': '9a9bee60e31f5e157b1d8544cd5b449aeb55742350e962da12fbd3c008f7d6cb'}, 'research/onchain-paper-replication-2026-09-24/full_sources/heartbeat-root-checkpoint10-2026-10-04/SERIALIZED_OUTCOME_CAPTURE02.py': {'bytes': 10817, 'sha256': 'd33ec54b7c8ea4dc2dc6b6ae8a839c9d87d523296c598a7da2004a17399cdec4'}, 'research/onchain-paper-replication-2026-09-24/full_sources/heartbeat-root-checkpoint10-2026-10-04/SERIALIZED_OUTCOME_CAPTURE_ROOT_EXIT01.json': {'bytes': 499, 'sha256': '0878b3c44c728b30bf024c3f7276be2f8eef0aea3c9aaf2645cd609d2b01d507'}}
FINAL_POPULATION_COUNT = 22

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
    repo = HERE / 'fresh-serialized-continuation-outcome-lane01.git'
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
    receipt = {'whole_tree_policy':dict(W.POLICY),'initial_owned_allocation':BASELINE,'whole_tree_observations':list(WATCHES),'unique_selected_objects':len(wanted),'expected_operations':10+len(wanted)+2*len(rows),'schema_version': 1, 'status': 'fresh-actual-serialized-continuation-outcome-lane01-recovered',
               'remote_commit': COMMIT, 'origin': ORIGIN, 'branch': BRANCH,
               'selection_sha256': digest(selection_body), 'selected_blobs': recovered,
               'selected_count': len(recovered), 'selected_logical_bytes': sum(r['bytes'] for r in rows),
               'fresh_git_root': str(repo), 'operations': CALLS, 'elapsed_seconds': time.monotonic() - START,
               'free_bytes': shutil.disk_usage(HERE).free, 'genuine_run_or_native_started': False,
               'qualification': 'Actual one finite new continuation-outcome shard lane; all three lanes and fresh opaque R4 recovery plus accepted historical/current bases are required for complete outcome bytes. No numerical rerun, POSIX reconstruction, installed runtime body recovery, immutable writer exclusion or paper-fit capacity claim.'}
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