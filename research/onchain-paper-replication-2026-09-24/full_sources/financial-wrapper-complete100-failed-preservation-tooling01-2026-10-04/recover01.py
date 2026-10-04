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

ROOT = Path.cwd().resolve()
HERE = Path(__file__).resolve().parent
COMMIT = None
BRANCH = 'refs/heads/research/onchain-paper-replication-2026-09-24'
ORIGIN = 'git@github.com:malecada/TradingAgents.git'
FLOOR = 10 * 1024**3
FILE = 4 * 1024**2
START = time.monotonic()
CALLS = []


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

def git(args, cwd=ROOT, cap=FILE):
    """Bounded actual Git/SSH group, streaming pipes and independent cleanup."""
    require(time.monotonic() - START < 600 and len(CALLS) < 1024, 'finite recovery budget')
    child = poller = None
    first = None
    out, err = bytearray(), bytearray()
    begun = time.monotonic()
    code = None
    env = dict(os.environ)
    env.update({'GIT_TERMINAL_PROMPT': '0', 'GIT_NO_REPLACE_OBJECTS': '1'})
    try:
        child = subprocess.Popen(['git', *args], cwd=cwd, env=env,
                                 stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, start_new_session=True)
        poller = selectors.DefaultSelector()
        for stream in (child.stdout, child.stderr):
            os.set_blocking(stream.fileno(), False)
            poller.register(stream, selectors.EVENT_READ)
        while poller.get_map():
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
    except BaseException as error:
        first = error
    actions = []
    if child is not None:
        def stop_group():
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        actions.extend((stop_group, lambda: child.wait(timeout=5),
                        child.stdout.close, child.stderr.close))
    if poller is not None:
        actions.append(poller.close)
    failures = []
    for action in actions:
        try:
            action()
        except BaseException as error:
            failures.append(error)
    CALLS.append({'operation': args[0], 'pid': None if child is None else child.pid,
                  'exit': code, 'seconds': time.monotonic() - begun,
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


REQUIRED = {'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture01-2026-10-04/CAPSULE_MASTER_MANIFEST01.json': {'bytes': 63, 'sha256': '87ef8249ef9652f98d57b4d5e885dbf3b5e5e0773987b8cab08eb23bc2176904'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture01-2026-10-04/CAPSULE_SHARD_INDEX01.json': {'bytes': 465, 'sha256': 'a9039426a5e30c4a7e7339fcff426d32669f507f4963175a8239bec57d954bfb'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture01-2026-10-04/CAPTURE01.json': {'bytes': 6615, 'sha256': '8b991df1466cf12f7812396b5b6afde3776edf684f1af12f9fa6e4454bf5dce1'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture01-2026-10-04/PARENT_MANIFEST01.json': {'bytes': 5112, 'sha256': '0e37c659c36f9918f6fcf643a51b2784c44b4891d3afacc5314ade0dc9401916'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture01-2026-10-04/ROOT_EVIDENCE_PATHS01.json': {'bytes': 3707, 'sha256': '3f4988561721c2bf208ebd1050dfb6eced16d1dec0ab9812da52d1ed40ad29b2'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture01-2026-10-04/SUPPORT_MANIFEST01.json': {'bytes': 5965, 'sha256': '37a0ff3e70003d50bf0128eb40dc53718e75833ff86cc32b5096de2455dba896'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture01-2026-10-04/SUPPORT_ROOTS01.json': {'bytes': 410, 'sha256': 'c7a7ff931db5efd369aec97919e015c7ff69d9357707ffad9fd523f5bb428425'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture01-2026-10-04/complete-parent01.tar.gz': {'bytes': 53889, 'sha256': '62272f91bd416dc094063902f972a2c3965db0b2e2a44f332f2f3c7dfc7b62aa'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture01-2026-10-04/complete-support01.tar.gz': {'bytes': 124284, 'sha256': '5d04fc75c2c82a9bc6959b0d534367be4885685d67fb2292a4c0c754b0b0acbc'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/CAPSULE01_MANIFEST01.json': {'bytes': 53083, 'sha256': '96d00adfa68490694e69c521396ae601ca80ea28f282934e112df302e5afe8aa'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/CAPSULE02_MANIFEST01.json': {'bytes': 41376, 'sha256': '14f80e2c44f29c9eb93abc1cc2f9086a9a977c0f9a59fabfd938843ee4d1824d'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/CAPSULE03_MANIFEST01.json': {'bytes': 8751, 'sha256': '5b0c807f62ae5376709f7b8b5c637fdaf0b66a5b39f0729b9752ba2d542073c9'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/CAPSULE04_MANIFEST01.json': {'bytes': 8319, 'sha256': '6b2e0757b177b3f710196355884aa1fe3505d8ebcc8969b837420a675f37080e'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/CAPSULE05_MANIFEST01.json': {'bytes': 8319, 'sha256': '64c44e349b2cf8e16224a216b1b897389e45ce7fe8c554b5d18db0afa7e28710'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/CAPSULE06_MANIFEST01.json': {'bytes': 8319, 'sha256': '56f7edc355855cb0a1b2a3229b0a7f39fd78205b924fba1fb4971cdae22bba48'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/CAPSULE07_MANIFEST01.json': {'bytes': 50772, 'sha256': '23e5fcc4a0103932264ab6e2469e3e26d7b32bef8e1663436317b2aed41d5cff'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/CAPSULE08_MANIFEST01.json': {'bytes': 2872, 'sha256': '7efc7bb9c9e4226586fe4e375c8499a77bee5499b1c3994750e9486c56da4d24'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/CAPSULE_MASTER_MANIFEST01.json': {'bytes': 156650, 'sha256': '537a6553912d10ce59a411e01438499a7a04e07c7929b7c68e8e0cbb033dfec1'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/CAPSULE_SHARD_INDEX01.json': {'bytes': 128243, 'sha256': '3a157938a90bb8f985f6623a6126ade33b2ffc74e1211fded8e9fc0d24b3043b'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/CAPTURE01.json': {'bytes': 69134, 'sha256': 'e9e78f1cc4f33d51ddca968bc80170e83e1a12b6ff2bff9cf301ab25e280fce8'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/PARENT_MANIFEST01.json': {'bytes': 5112, 'sha256': '0e37c659c36f9918f6fcf643a51b2784c44b4891d3afacc5314ade0dc9401916'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/PRIOR_FAILED_CAPTURE_ERRATA01.json': {'bytes': 813, 'sha256': 'ce15a2a946af54290aee4040b70d9e18738637d822b8c9551edd9d287cc77e65'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/ROOT_EVIDENCE_PATHS01.json': {'bytes': 3707, 'sha256': '3f4988561721c2bf208ebd1050dfb6eced16d1dec0ab9812da52d1ed40ad29b2'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/SUPPORT_MANIFEST01.json': {'bytes': 5965, 'sha256': '37a0ff3e70003d50bf0128eb40dc53718e75833ff86cc32b5096de2455dba896'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/SUPPORT_ROOTS01.json': {'bytes': 410, 'sha256': 'c7a7ff931db5efd369aec97919e015c7ff69d9357707ffad9fd523f5bb428425'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/complete-capsule0101.tar.gz': {'bytes': 663185, 'sha256': '2288fd7d16883c4fda74c7dd84728fe724a49546c50ae7ab07f8bc9ee37d643e'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/complete-capsule0201.tar.gz': {'bytes': 1724365, 'sha256': 'eb7d3d55fb1d62ee37beb3d3ce0c7dfcfa0661421152c9b1b4c4e6e8ab59973b'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/complete-capsule0301.tar.gz': {'bytes': 2747900, 'sha256': '63ffffadc257f0bbea32738d48ad92a00c3efbe94d2456c24ad465393028f548'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/complete-capsule0401.tar.gz': {'bytes': 2737208, 'sha256': '8e6d2c208e566ef39921548105b4d0e8a035f102e71fa69a0fd9a1367ab8fda4'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/complete-capsule0501.tar.gz': {'bytes': 2738391, 'sha256': '7b9ba899fc9c9cde51be4f4de6bdb786737ed0f818feec32030865ea586c04dc'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/complete-capsule0601.tar.gz': {'bytes': 2734920, 'sha256': 'de51e82005665950cf2c0945ddb46260ceb9922b2ee059548e0e9a74a9aacf25'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/complete-capsule0701.tar.gz': {'bytes': 1780860, 'sha256': '30fc8b2e4e1e75188d8ceb3b593243a4f0f72808477c7f5cc7ed779e7095f4dd'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/complete-capsule0801.tar.gz': {'bytes': 423945, 'sha256': '1f28552b811e5a7f362045e4575ed25007abeced2c8a316532756d1bde7b4b57'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/complete-parent01.tar.gz': {'bytes': 53889, 'sha256': '62272f91bd416dc094063902f972a2c3965db0b2e2a44f332f2f3c7dfc7b62aa'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/complete-support01.tar.gz': {'bytes': 124284, 'sha256': '5d04fc75c2c82a9bc6959b0d534367be4885685d67fb2292a4c0c754b0b0acbc'}}

def validate_fixed_selection(selection):
    require(type(selection) is dict and set(selection)=={'remote_commit','rows'}, 'exact selection schema')
    rows=selection['rows'];require(type(rows) is list and 1<=len(rows)<=506, 'finite selected paths')
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
    repo = HERE / 'fresh-complete100-failed-outcome02-01.git'
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
    git(['fetch', '--no-tags', 'origin', *wanted], repo)
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
    require(len(CALLS) == 11 + 2*len(rows), 'exact finite operation denominator')
    receipt = {'schema_version': 1, 'status': 'fresh-actual-remote-complete100-failed-outcome02-recovered',
               'remote_commit': COMMIT, 'origin': ORIGIN, 'branch': BRANCH,
               'selection_sha256': digest(selection_body), 'selected_blobs': recovered,
               'selected_count': len(recovered), 'selected_logical_bytes': sum(r['bytes'] for r in rows),
               'fresh_git_root': str(repo), 'operations': CALLS, 'elapsed_seconds': time.monotonic() - START,
               'free_bytes': shutil.disk_usage(HERE).free, 'genuine_run_or_native_started': False,
               'qualification': 'Exact corrected failed-outcome02 and retained withheld-capture01 bytes recovered. Historical native attempt remains FAILED/spent; remote retrieval starts no claim. Baseline385 Git remains separate. Selected bodies are bounded4MiB; writable Git pack extents are not universally bounded4MiB and require separate actual readback. No numerical/runtime/POSIX/capacity authority.'}
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
                  'error': str(primary), 'operations': CALLS, 'genuine_run_or_native_started': False}))
        except BaseException as journal_error:
            secondary.append(journal_error)
        _raise_retained(primary, secondary)


if __name__ == '__main__':
    entry()