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
            watch(owned_fetch_objects=Path(cwd)/'objects' if args and args[0]=='fetch' and Path(cwd)==HERE/'fresh-serialized-prediction-source01.git' and child.poll() is None else None)
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


REQUIRED = {'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/shards/piece-013.json': {'bytes': 2351, 'sha256': '76ac92b375533a472e1820f9a5af567dcd4f5753eb4c44433f745869ceaffc05'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/shards/piece-013.tar.gz': {'bytes': 2721956, 'sha256': '183b1f8c58654fd134b4272271651488bc06cdf2c423ed2ef4286dea2b03fdbc'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/shards/piece-014.json': {'bytes': 2351, 'sha256': '3bd41ba8fc8a0a63697e5693b351aa45e4da1220f6c4ff2acfeb767bdeb93d73'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/shards/piece-014.tar.gz': {'bytes': 2727138, 'sha256': 'b88238810d97b226190384f1af788d3b545fbdd56963050cdf75ea424c37045f'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/shards/piece-015.json': {'bytes': 2351, 'sha256': 'faa983dc6abab958cb9689aec4dbdca261757d871fff6f1c824c064033d87b64'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/shards/piece-015.tar.gz': {'bytes': 2727263, 'sha256': '268821ed9876c29cefeb1b7f34eec1a2a0a3b24a996d7ccad51bc5bd53905019'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/shards/piece-016.json': {'bytes': 2351, 'sha256': '85ceea02c9bf30babdb4fd3f2be9a7092dcbfd684f6625436b37a6ad669aa47c'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/shards/piece-016.tar.gz': {'bytes': 2728088, 'sha256': '0d98e06c1fe865f36c801ad084aee6780e77553826890bb44983b316d9a0087b'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/shards/piece-017.json': {'bytes': 2351, 'sha256': '556a7a19f5b6d2814b687ebc3b6833f209a965d98da5068ccf49cfdc4ca1dd14'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/shards/piece-017.tar.gz': {'bytes': 2724016, 'sha256': '135f1daee53dd87dcd88296db2a3983ee91152a65525df7036fe0213964d81a4'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/shards/piece-018.json': {'bytes': 34415, 'sha256': 'a05831b2d0fc31d18a06de20bfc3d180009617858a118b5f02c8e209ed296b0d'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/shards/piece-018.tar.gz': {'bytes': 544692, 'sha256': '0df02e16b1f0619f037e720b269a392a1e49f4ec49136cc8e847ea5a14e08789'}}
FINAL_POPULATION_COUNT = 11
REQUIRED = {'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-parent-preparation01-2026-10-05/PREPARATION01.json': {'bytes': 2347, 'sha256': '77358f64fd8bf4850a1493d3fc35f658e0255f03f83da8b3e9536861a2e8d253'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-parent-preparation01-2026-10-05/SOURCE_DELTA01.patch': {'bytes': 12201, 'sha256': 'b2393ea00dee97e6df32fa103709279349af18541d92e7718bc428b4692fb49d'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-parent-preparation01-2026-10-05/parent01.py': {'bytes': 26562, 'sha256': 'ca52dd65245754cf6ab84f9bea0e94dc7bf791de91124f0ef59d9dec971d512a'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-preparation01-2026-10-05/MANIFEST01.json': {'bytes': 3510, 'sha256': 'b7e5adfac87e0774f70c3b8181b06fceb77b59a65c0f6ebf937a20a871726017'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-preparation01-2026-10-05/evaluation.py': {'bytes': 16488, 'sha256': '9a7c4c2c3cb09c055752601414ee097bc79f2c254f8b2f524aea93023ed1621f'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-preparation01-2026-10-05/financial_wrapper_fixture.py': {'bytes': 43100, 'sha256': '52281e61b2ec47c629086240fab02bf80386f4916617696df364c25f2219ff9b'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-preparation01-2026-10-05/operational_source_compatibility.py': {'bytes': 68038, 'sha256': '8489823b7e4bd51e5c0ae28036f174ff14b2a85b034b338fc5ab8fbff61fc63d'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-preparation01-2026-10-05/preclaim01.py': {'bytes': 48154, 'sha256': '5f7ae415804cc482dbc5b3538160688d8f4e4fe494abb4696ca047da90a994c3'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-review01-2026-10-05/MANIFEST01.json': {'bytes': 815, 'sha256': '08fcfaf4a47be74447cddbc4dbee220f25cec15dcaa97135b053ba3a5dd39df7'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-review01-2026-10-05/SOURCE_DRAFT_REVIEW01.json': {'bytes': 3859, 'sha256': '052968fc85f123a7108351d2d7cfa1f675b82d0db09e3163e9e066defc076c01'}, 'research/onchain-paper-replication-2026-09-24/full_sources/heartbeat-root-checkpoint10-2026-10-04/SERIALIZED_PREDICTION_BOUND_PARENT_DRAFT01.json': {'bytes': 605994, 'sha256': '301d1b891e4f8807516a2cd6163cbbc6f4d51c61bf0121e54899715770447bf3'}}

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
    repo = HERE / 'fresh-serialized-prediction-source01.git'
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
    receipt = {'whole_tree_policy':dict(W.POLICY),'initial_owned_allocation':BASELINE,'whole_tree_observations':list(WATCHES),'unique_selected_objects':len(wanted),'expected_operations':10+len(wanted)+2*len(rows),'schema_version': 1, 'status': 'fresh-actual-serialized-prediction-source01-recovered',
               'remote_commit': COMMIT, 'origin': ORIGIN, 'branch': BRANCH,
               'selection_sha256': digest(selection_body), 'selected_blobs': recovered,
               'selected_count': len(recovered), 'selected_logical_bytes': sum(r['bytes'] for r in rows),
               'fresh_git_root': str(repo), 'operations': CALLS, 'elapsed_seconds': time.monotonic() - START,
               'free_bytes': shutil.disk_usage(HERE).free, 'genuine_run_or_native_started': False,
               'qualification': 'Actual fixed prospective prediction source/input/caller bytes recovered from the recorded Main commit. Five non-null new input bodies are embedded in the exact bound-parent draft; two pending policy proof bodies and final capsule/caller/envelope recovery are excluded. Reused installed-source recovery requires the independently accepted continuation basis. No numerical, admission, POSIX reconstruction, runtime body, writer-exclusion or whole capacity claim.'}
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