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


REQUIRED={'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-baseline-capture01-2026-10-04/CAPSULE_MANIFEST01.json': {'bytes': 104055, 'sha256': '649fafe8544ec5822b5a26335feec0145059ea5e221ef79dc551a75b7e07f625'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-baseline-capture01-2026-10-04/CAPTURE01.json': {'bytes': 50918, 'sha256': '7d65c2bac832832df5d62d49a41b31b7d54b33b52a448d048cd94b9541f8a176'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-baseline-capture01-2026-10-04/GIT1_MANIFEST01.json': {'bytes': 45811, 'sha256': 'cc31d5f881ea2c94afa04b5173532f7fa86282973941638b549a4d53b7846bda'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-baseline-capture01-2026-10-04/GIT2_MANIFEST01.json': {'bytes': 11525, 'sha256': 'e4b4109700892a1ac38159b0ce44b28c4f08a743fb32596cd8bf08fa1685147d'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-baseline-capture01-2026-10-04/GIT3_MANIFEST01.json': {'bytes': 25967, 'sha256': 'abf2c8cc3e3951c20f9a012d84b344a1da984f6de2ac79ac688ccd11c9367a63'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-baseline-capture01-2026-10-04/GIT_CENSUS01.json': {'bytes': 46297, 'sha256': 'd91e0e417309bad0041a0bb2579942dbd832e1f02b0ab4e6327a905cc7f331eb'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-baseline-capture01-2026-10-04/GIT_OBJECTS01.json': {'bytes': 109621, 'sha256': '0c10274361016fb1ae03027e588d9b1eafdbdf4cb08e0ec3aef7793f66c77c62'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-baseline-capture01-2026-10-04/INTENT01.json': {'bytes': 597, 'sha256': '57f4d4c0e3e3f179128120354e7152e28603110e700ade73def60170987e1da7'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-baseline-capture01-2026-10-04/PARENT_MANIFEST01.json': {'bytes': 1795, 'sha256': '8e37e1d849970217609c0fa858e56a88470ec8d612fb9f0d97a487327c484663'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-baseline-capture01-2026-10-04/SUPPORT_MANIFEST01.json': {'bytes': 27981, 'sha256': '99b304be2234b028f0ceb74c7a0a2507a1c1cf84127b83f538bb315c3353f07a'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-baseline-capture01-2026-10-04/complete-capsule01.tar.gz': {'bytes': 2280729, 'sha256': 'bb9e1b75237b420dd7063c5c22ecb7d4ec81db40d6cda69f823fffba57129fe8'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-baseline-capture01-2026-10-04/complete-git101.tar.gz': {'bytes': 734842, 'sha256': '9b3d8676e64dacb917a9a18b4a18062d26139febbe2eacf0599b303e98307534'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-baseline-capture01-2026-10-04/complete-git201.tar.gz': {'bytes': 853857, 'sha256': '38238b26666084caff46aef1407c2e682ca6bab5471a73a97dba45103381d204'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-baseline-capture01-2026-10-04/complete-git301.tar.gz': {'bytes': 409688, 'sha256': '9039ad0fd6d5983b58dc96b3832fb15ec398c4941777b4ad54db39b1f35e23be'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-baseline-capture01-2026-10-04/complete-parent01.tar.gz': {'bytes': 52101, 'sha256': 'd5b083af39a34e9cb219e19f305db5a52316619c07162a3de5df126f267a6f43'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-baseline-capture01-2026-10-04/complete-support01.tar.gz': {'bytes': 561007, 'sha256': '0fbe00cf65408589821d4fc9597d643629ae079240398a33e9c39f19b6815f3a'}}

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
    repo = HERE / 'fresh-complete100-baseline-source339-01.git'
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
    receipt = {'schema_version': 1, 'status': 'fresh-actual-remote-complete100-baseline-source339-recovered',
               'remote_commit': COMMIT, 'origin': ORIGIN, 'branch': BRANCH,
               'selection_sha256': digest(selection_body), 'selected_blobs': recovered,
               'selected_count': len(recovered), 'selected_logical_bytes': sum(r['bytes'] for r in rows),
               'fresh_git_root': str(repo), 'operations': CALLS, 'elapsed_seconds': time.monotonic() - START,
               'free_bytes': shutil.disk_usage(HERE).free, 'genuine_run_or_native_started': False,
               'qualification': 'Complete current non-Git Source339 capsule, literal nine-file NEW Parent draft, supporting closed reviews/readbacks and ALL385 current reachable original Git object bodies in six canonical archives. These exact baseline bodies are recovered from external Git; full fresh flat and original Git reconstruction/independent acceptance remain separate. Final request/release are not captured and require a separate recovered supplement. Installed runtime bodies, POSIX instantiation, whole capacity and numerical authority are excluded.'}
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