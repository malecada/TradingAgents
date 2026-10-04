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


REQUIRED = {'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-baseline-review-capture01-2026-10-05/CAPTURE01.json': {'bytes': 705, 'sha256': '4a05bc36d05d133955cde1398930d75aed5a1ec7e16338e81544fc193f943ed7'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-baseline-review-capture01-2026-10-05/MANIFEST01.json': {'bytes': 3031, 'sha256': 'e80a63cfd84873ff3db080154b24eaa384a5b331990e46871b3737adeabf042a'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-baseline-review-capture01-2026-10-05/review01.tar.gz': {'bytes': 15935, 'sha256': '55a5bfb1b21c4201ad31fc696e948afe551102dacee9cfc780f63ddd236b1372'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-coalesced-evidence-outcome-review04-2026-10-04/MACHINE01.json': {'bytes': 3818, 'sha256': 'e267987ec088fcde40936aad9275967131521aa94b7db19fc3237409e629b6a6'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-coalesced-postinstall-review04-2026-10-04/MACHINE01.json': {'bytes': 1468, 'sha256': '9a08cc6f2f44505cbf0ec459d5d957139ccd9b55a7b52a7bb9776cf26369818b'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-composed-recovery-review02-2026-10-04/MACHINE01.json': {'bytes': 15541, 'sha256': 'aae1d255e54bf8fb52a82c7c7dff6495df16e1c82b71d448828e28f841db116f'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-current-source-parent-capture03-2026-10-04/FAILED_LOCAL_CAPTURE01.json': {'bytes': 13580, 'sha256': '07838977e0d6ec5e2e88c35cdd860d8c478c581ba09ccc9772470b5a618829d0'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-current-source-parent-capture03-2026-10-04/MANIFEST01.json': {'bytes': 11982, 'sha256': '49df5d5e80f307948b32bb6a3eb1a2234f8bbd8ffb2c5592700b69828caaa913'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-current-source-parent-capture03-2026-10-04/source-parent-delta03.tar.gz': {'bytes': 553764, 'sha256': 'd90353cb0d72df5fca6ed2479f2ea6b28400a9dcdc6bc1143a8973665ca1d8b1'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-current-source-parent-capture04-2026-10-04/ACTUAL_ROOT_EXIT01.json': {'bytes': 586, 'sha256': '115c0a7eed1057c940788835031a750c31c0bb86e62b2b5a4f5696ed9110967a'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-current-source-parent-capture04-2026-10-04/CAPTURE01.json': {'bytes': 3286, 'sha256': '5a44a5f98f70c23fa059054c24014d7921f86a992671700801ea857a95813b66'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-current-source-parent-capture04-2026-10-04/MANIFEST01.json': {'bytes': 11982, 'sha256': '49df5d5e80f307948b32bb6a3eb1a2234f8bbd8ffb2c5592700b69828caaa913'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-current-source-parent-capture04-2026-10-04/source-parent-delta04.tar.gz': {'bytes': 553764, 'sha256': 'd90353cb0d72df5fca6ed2479f2ea6b28400a9dcdc6bc1143a8973665ca1d8b1'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-final-source-runtime-bridge02-2026-10-04/SOURCE_INPUT_RUNTIME_PROOF01.json': {'bytes': 5500, 'sha256': 'ac1ed8a157d7ec113ebe1a8e2eb71a917f46572d0cc8b035c1ee850d9b10730c'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-preclaim-baseline-capture-review01-2026-10-05/MACHINE01.json': {'bytes': 4107, 'sha256': '2b30c80aa254687fa8a6e48c6a9b8129e2bba5fc17c6c953000e454649538bf6'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-preclaim-baseline-capture01-2026-10-05/CAPTURE01.json': {'bytes': 3021, 'sha256': '27f7929e32708c013dfa56b00f4092ce46076baef5f8ee0135cbfd4621ac828c'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-preclaim-baseline-capture01-2026-10-05/MANIFEST01.json': {'bytes': 63730, 'sha256': '6048eadcb4841a816a884eebe16b66fa5d3c4e50ff61ee80df55e43ec44957f9'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-preclaim-baseline-capture01-2026-10-05/baseline01.tar.gz': {'bytes': 3052678, 'sha256': 'b47c7201a023e8b08fd90e8f8fc228751608b30cf6d25077373e7f797db1178c'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-preclaim-baseline-envelope01-2026-10-05/ENVELOPE01.json': {'bytes': 4582, 'sha256': '5523f659a7e5636aa986094651031073b54b6f4d8788507d0317997ca209c6c0'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-source-parent-capture-review04-2026-10-04/CHECKS01.json': {'bytes': 1543043, 'sha256': 'ba694414e461cccb3357698de1d19ebaa526a5b1b9115d8c0bd3386014d899ad'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-source-parent-capture-review04-2026-10-04/MACHINE01.json': {'bytes': 1732, 'sha256': '435b69706a78e785d939311c269357e74f45cfa211c198750eb12f7dd2925429'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-source-parent-capture-review04-2026-10-04/MANIFEST01.json': {'bytes': 5014, 'sha256': '4a21d4a7853e8386e72b700bca5243415caef1d4c0914c008547977e835ded84'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-source-parent-capture-review04-2026-10-04/READBACK01.json': {'bytes': 2688, 'sha256': '1f2c5adc362586c9c806b1bab675157c23081538c07100c28aeff86fbb324d8b'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-source-parent-capture-review04-2026-10-04/REPORT01.md': {'bytes': 4752, 'sha256': '01b02140efa2ed11b926a5ed992c2f9f40ff5386dc12f6c6aed1e66762938c1f'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-source-parent-capture-review04-2026-10-04/SUPPLEMENT01.json': {'bytes': 60957, 'sha256': '29a0ba41ab3401d68adddb0fa921e42c538e63b3900be6b0a1924bb22f58b728'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-source-parent-capture-review04-2026-10-04/SUPPLEMENT01.stderr': {'bytes': 0, 'sha256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-source-parent-capture-review04-2026-10-04/SUPPLEMENT01.stdout': {'bytes': 94, 'sha256': '31f63fcedf78d4d0a3a1846d8de60b20be51095bfebc9528bc4180919b545fd3'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-source-parent-capture-review04-2026-10-04/VERIFY01.stderr': {'bytes': 0, 'sha256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-source-parent-capture-review04-2026-10-04/VERIFY01.stdout': {'bytes': 2394, 'sha256': 'd068f615391cc4d1223471d8c3b6ea1a7f01a4e3528ae74fca309e86a96ddec5'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-source-parent-capture-review04-2026-10-04/evidence/00-CAPTURE01.json': {'bytes': 3286, 'sha256': '5a44a5f98f70c23fa059054c24014d7921f86a992671700801ea857a95813b66'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-source-parent-capture-review04-2026-10-04/evidence/01-MANIFEST01.json': {'bytes': 11982, 'sha256': '49df5d5e80f307948b32bb6a3eb1a2234f8bbd8ffb2c5592700b69828caaa913'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-source-parent-capture-review04-2026-10-04/evidence/02-ACTUAL_ROOT_EXIT01.json': {'bytes': 586, 'sha256': '115c0a7eed1057c940788835031a750c31c0bb86e62b2b5a4f5696ed9110967a'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-source-parent-capture-review04-2026-10-04/evidence/03-root_source_parent_capture03.py': {'bytes': 18003, 'sha256': '368d77b3c2bf5e6850d1de6d22f9ced8c51f3521309d87e7021da712f6d510c8'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-source-parent-capture-review04-2026-10-04/evidence/04-root_source_parent_capture04.py': {'bytes': 18278, 'sha256': 'f55ce818ef7999195c88d872c983a568861d5d45d2970af61b539979faf27cdf'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-source-parent-capture-review04-2026-10-04/evidence/05-CAPTURE04_SOURCE_INVERSE01.json': {'bytes': 1125, 'sha256': '618dde6ea04847208f296092d4ccf16d644273528106c95a79ac02047cf818e1'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-source-parent-capture-review04-2026-10-04/evidence/06-FAILED_LOCAL_CAPTURE01.json': {'bytes': 13580, 'sha256': '07838977e0d6ec5e2e88c35cdd860d8c478c581ba09ccc9772470b5a618829d0'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-source-parent-capture-review04-2026-10-04/owned01/03/level1/level2/body': {'bytes': 6, 'sha256': '6d229884c1268bb0ab32d8da315d0fe52f9147228bd830a37bc9fb28a954940d'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-source-parent-capture-review04-2026-10-04/owned01/04/level1/level2/body': {'bytes': 6, 'sha256': '6d229884c1268bb0ab32d8da315d0fe52f9147228bd830a37bc9fb28a954940d'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-source-parent-capture-review04-2026-10-04/supplement01.py': {'bytes': 5610, 'sha256': '81795cb8c60f5aa73e26b737535db4e2243f7b56c85592bf4d378be27d636284'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-source-parent-capture-review04-2026-10-04/verify01.py': {'bytes': 17823, 'sha256': '1d89e758735a95baf445cd4da3c08fb8af18659229973b3fe157f8d3d8dc1ca9'}, 'research/onchain-paper-replication-2026-09-24/full_sources/heartbeat-root-checkpoint10-2026-10-04/PRECLAIM_BASELINE_CAPTURE01_ACTUAL_TOOL_EXIT01.json': {'bytes': 943, 'sha256': '751254ba24a44ab6f917a0692a2af9bd2a7d3dea8cfbbf83bdba0f1400b7ae69'}, 'research/onchain-paper-replication-2026-09-24/full_sources/heartbeat-root-checkpoint10-2026-10-04/root_preclaim_baseline_capture01.py': {'bytes': 18230, 'sha256': '64c969a7d4f3558466633ba3eb027def12b10318e9d2c9e0c618efac50fdc078'}, 'research/onchain-paper-replication-2026-09-24/full_sources/heartbeat-root-checkpoint10-2026-10-04/root_source_parent_capture03.py': {'bytes': 18003, 'sha256': '368d77b3c2bf5e6850d1de6d22f9ced8c51f3521309d87e7021da712f6d510c8'}, 'research/onchain-paper-replication-2026-09-24/full_sources/heartbeat-root-checkpoint10-2026-10-04/root_source_parent_capture04.py': {'bytes': 18278, 'sha256': 'f55ce818ef7999195c88d872c983a568861d5d45d2970af61b539979faf27cdf'}}
FINAL_POPULATION_COUNT = 44

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
    repo = HERE / 'fresh-compatibility-baseline02.git'
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
    receipt = {'whole_tree_policy':dict(W.POLICY),'initial_owned_allocation':BASELINE,'whole_tree_observations':list(WATCHES),'unique_selected_objects':len(wanted),'expected_operations':10+len(wanted)+2*len(rows),'schema_version': 1, 'status': 'fresh-actual-remote-compatibility-baseline02-supervised-recovered',
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