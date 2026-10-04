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


REQUIRED = {'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-concrete-policy-review01-2026-10-04/MACHINE01.json': {'bytes': 2676, 'sha256': '27367565dc31fdbe190a80cfecca7f609ca9e2391c8335a3a85321669e794a6a'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-concrete-policy-review01-2026-10-04/MANIFEST01.json': {'bytes': 127520, 'sha256': '82b1066539316421d5d58ab43583ba2a5ac1fad065f5360cb12e1441b0832361'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-concrete-policy-review01-2026-10-04/READBACK01.json': {'bytes': 64208, 'sha256': '54f08e320c6671e6179b4a515d0e048672032a25711b286153e005af3889f4e6'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-concrete-policy-review01-2026-10-04/REPORT01.md': {'bytes': 5361, 'sha256': '03330ea8378429a7846a5826af75646aaac3b3daa581ea552bf404a651fa9835'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-concrete-policy-review01-2026-10-04/REVIEW_PROOF01.json': {'bytes': 466, 'sha256': '0a0db0cb8fafce00024aa25c048cb9efa27d1411e57586f7217b0bc209a41cd5'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-operational-delta-capture02-2026-10-04/CAPTURE01.json': {'bytes': 1249, 'sha256': '61f3560c6fc64b7122f12a690ab728407803c7bb3c3406fd1a754456e207f939'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-operational-delta-capture02-2026-10-04/ORIGIN_MAP01.json': {'bytes': 9451, 'sha256': '0f096484bb25ce6faf59edbc4a4af388ecb91d1a2687608cf8e1f252465c4bd1'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-operational-delta-capture02-2026-10-04/PAYLOAD_MANIFEST01.json': {'bytes': 8265, 'sha256': 'a04069280b7bf7b49fc075e640109f935f65b292fe69e1f4e96342bc08ad246e'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-operational-delta-capture02-2026-10-04/operational-delta01.tar.gz': {'bytes': 225862, 'sha256': 'a60e19140e04a6ec1877bf17134ee7b16d560068e1296b13c05535ea6212357e'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-operational-delta-capture02-2026-10-04/root_delta_capture05.py': {'bytes': 6633, 'sha256': '9e7ac229e24453ae1fc89b84c575cdfd8fc557ad2d8bd9576d7bac4f04770ad4'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-operational-delta-failed-remote-capture02-2026-10-04/CAPTURE01.json': {'bytes': 1875, 'sha256': '58d76ef3d7da87994ec7052e1d16c6facadcfd53535c15fe7532956515eab740'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-operational-delta-failed-remote-capture02-2026-10-04/FAILED_PAYLOAD_MANIFEST01.json': {'bytes': 8102, 'sha256': '9843ad4d50df192912c19920198da454a5e5f0f7515b407206a56ca5c4fc7e37'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-operational-delta-failed-remote-capture02-2026-10-04/ORIGINAL_FAILED_ROOT_SCOPE43.json': {'bytes': 9840, 'sha256': '7995f07ef7660d77a40fed81f9a7fc14054a5d1b609b6e81002332c8033b6a4b'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-operational-delta-failed-remote-capture02-2026-10-04/failed-remote02.tar.gz': {'bytes': 33372, 'sha256': '06c8a9cd583bebb3f03fe4800a6f17972b490cff552509097a1e1ed09695b1da'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-operational-delta-failed-remote-capture02-2026-10-04/root_remote_failure_capture02.py': {'bytes': 3066, 'sha256': '6f06bef1476024d01b730fb9f37add1ebe05b7913a549d80d8daed81415b1614'}}

def validate_fixed_selection(selection):
    require(type(selection) is dict and set(selection)=={'remote_commit','rows'}, 'exact selection schema')
    rows=selection['rows'];require(type(rows) is list and len(rows)==len(REQUIRED)==15, 'exact fifteen selected paths')
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
    repo = HERE / 'fresh-operational-source-policy02.git'
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
    receipt = {'whole_tree_policy':dict(W.POLICY),'initial_owned_allocation':BASELINE,'whole_tree_observations':list(WATCHES),'unique_selected_objects':len(wanted),'expected_operations':10+len(wanted)+2*len(rows),'schema_version': 1, 'status': 'fresh-actual-remote-operational-source-policy01-supervised-recovered',
               'remote_commit': COMMIT, 'origin': ORIGIN, 'branch': BRANCH,
               'selection_sha256': digest(selection_body), 'selected_blobs': recovered,
               'selected_count': len(recovered), 'selected_logical_bytes': sum(r['bytes'] for r in rows),
               'fresh_git_root': str(repo), 'operations': CALLS, 'elapsed_seconds': time.monotonic() - START,
               'free_bytes': shutil.disk_usage(HERE).free, 'genuine_run_or_native_started': False,
               'qualification': 'Exact frozen operational source/policy delta, genuine independent policy review and complete closed failed forensic Root02 scope recovered. Original failed histories remain spent; no claim is started. Old385 actual recovered Git plus nine new bodies form an explicitly checked394-object source basis; final registration/caller/runtime-body recovery remain separate. Every receiver child inherits actual-readback hard/soft4MiB FSIZE; entire owned tree including baseline sampled at fixed64MiB logical/96MiB allocated/32768members/depth32. Single-blob fetches and exact dynamic unique-object operation denominator; transient aggregate/physical wire not measured. No numerical/runtime/POSIX/capacity authority.'}
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
# opaque review edit, never executed
