"""One-use external LOCAL6 parent. This file issues no research authority.

An exact independently reviewed request and actual recovery evidence must be
provided before reservation. Genuine job/Run/Owner/native authority stays in
the unchanged capsule controller. Default/check mode never starts a process.
"""
import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone

CAP = Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source')
PARENT = Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-root-launch-20261003-01')
SOURCE = 'd443208795f59292c156c5b81b687594efacea4d'
IDENTITY = 'original-import-held-success-20261003-01'
PARSER_SHA = '95affaa3867b0f50dedc706121b47304126c6def39715133414ef149b9eae153'
GIB = 1024 ** 3
FILE = 4 * 1024 ** 2
PARENT_LIMITS = dict(max_allocated_bytes=32*1024**2,
                     max_logical_bytes=16*1024**2, max_entries=1024,
                     max_depth=8, max_scan_seconds=5)
SELECTED_CLEANUP_TYPES = ()
PROOF_FIELDS = ('release_review_sha256', 'external_capsule_recovery_sha256',
                'external_recovery_review_sha256')

class ParentCleanupFailure(BaseException):
    pass

def require(value, message):
    if not value:
        raise ValueError(message)

def fatal(error):
    return isinstance(error, MemoryError) or (not isinstance(error, Exception)
            and not isinstance(error, (ParentCleanupFailure,)+SELECTED_CLEANUP_TYPES))

def select(primary, later):
    if primary is None:
        return later
    if fatal(primary):
        return primary
    if fatal(later) or isinstance(later, (ParentCleanupFailure,)+SELECTED_CLEANUP_TYPES):
        return later
    return primary

def cleanup(actions, primary=None):
    errors = []
    for action in actions:
        try:
            action()
        except BaseException as error:
            errors.append(error)
    first = next((e for e in ([primary] if primary is not None else [])+errors
                  if fatal(e)), None)
    if first is not None:
        raise first
    if errors:
        raise ParentCleanupFailure('parent owned cleanup uncertain') from (primary or errors[0])
    if primary is not None:
        raise primary

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode()

def parse(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, 'duplicate parent JSON key')
            value[key] = item
        return value
    def constant(value):
        raise ValueError('nonfinite parent JSON')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)

def signature(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns)

def bootstrap(root, name, expected):
    """Flat bootstrap only; after this, the exact reviewed Reader is used."""
    require(root.is_absolute() and root.resolve() == root and '/' not in name
            and name not in ('', '.', '..'), 'canonical flat bootstrap required')
    parent = child = None
    primary = None
    raw = None
    try:
        parent = os.open(root, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        held = signature(os.fstat(parent))
        before = os.stat(name, dir_fd=parent, follow_symlinks=False)
        pin = signature(before)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                and 0 <= before.st_size <= FILE, 'bootstrap type/link/extent')
        child = os.open(name, os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,
                        dir_fd=parent)
        require(signature(os.fstat(child)) == pin, 'bootstrap changed before read')
        parts = []
        size = 0
        while True:
            part = os.read(child, min(65536, before.st_size-size+1))
            if not part:
                break
            size += len(part)
            require(size <= before.st_size, 'bootstrap grew')
            parts.append(part)
        require(size == before.st_size and signature(os.fstat(child)) == pin
                and signature(os.stat(name, dir_fd=parent, follow_symlinks=False)) == pin
                and signature((root/name).lstat()) == pin
                and (root/name).resolve() == root/name, 'bootstrap member changed')
        require(signature(root.lstat()) == held == signature(os.fstat(parent)),
                'bootstrap parent changed')
        raw = b''.join(parts)
        require(sha(raw) == expected, 'bootstrap source hash differs')
    except BaseException as error:
        primary = error
    cleanup(([lambda: os.close(child)] if child is not None else [])+
            ([lambda: os.close(parent)] if parent is not None else []), primary)
    return raw

def module(path, name, raw):
    """Execute only bytes already read and hashed, not a second path lookup."""
    import types
    value = types.ModuleType(name)
    value.__file__ = str(path)
    sys.modules[name] = value
    exec(compile(raw, str(path), 'exec'), value.__dict__)
    return value

def contract(release):
    """Finite documentary contract excludes only its three later proof refs."""
    return sha(canonical({k:v for k,v in release.items() if k not in PROOF_FIELDS}))

def reference(reader, ref):
    require(type(ref) is dict and set(ref) == {'path', 'sha256'}
            and type(ref['sha256']) is str and len(ref['sha256']) == 64
            and all(c in '0123456789abcdef' for c in ref['sha256']),
            'exact authenticated parent reference required')
    raw = reader.body(ref['path'])
    require(sha(raw) == ref['sha256'], 'parent evidence bytes differ')
    return raw

def namespaces(root):
    return [root/'research_runs'/IDENTITY, root/'fixture_outer'/IDENTITY,
            root/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/IDENTITY]

def dedup(root, parent):
    require(not os.path.lexists(parent/'attempt'/IDENTITY), 'parent identity reserved')
    for path in namespaces(root):
        require(not os.path.lexists(path), 'original native identity reserved/spent')
    # Scan each already-existing owned artifact tree with finite sampled bounds.
    begin = time.monotonic()
    count = 0
    for tree in (root/'research_artifacts', root/'fixture_outer'):
        if not os.path.lexists(tree):
            continue
        require(tree.resolve() == tree and tree.is_dir(), 'artifact root redirected')
        for path in tree.rglob('*'):
            count += 1
            require(count <= 32768 and time.monotonic()-begin < 5, 'namespace scan bound')
            require(path.resolve() == path, 'namespace path redirected')
            require(IDENTITY not in path.relative_to(tree).parts,
                    'representation or native identity already reserved')
    selected = []
    for directory in Path('/proc').iterdir():
        if not directory.name.isdecimal() or int(directory.name) == os.getpid():
            continue
        try:
            args = (directory/'cmdline').read_bytes().split(b'\0')
            if b'tradingagents.research.onchain_replication.job' in args or any(
                Path(a.decode('utf-8', 'replace')).name in
                ('outer_controller01.py', 'launch_success01.py') for a in args if a):
                selected.append(int(directory.name))
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
    require(not selected, 'another selected numerical/controller process is active')

def mem_available():
    return int(next(line.split()[1] for line in Path('/proc/meminfo').read_text()
                    .splitlines() if line.startswith('MemAvailable:')))*1024

def prepared(request_path, expected, *, after=False):
    global SELECTED_CLEANUP_TYPES
    require(request_path.parent == PARENT and Path(__file__).resolve() == PARENT/'launch_success01.py'
            and Path.cwd() == CAP, 'caller origin/cwd differs')
    parser_raw = bootstrap(PARENT, 'held_outcome02.py', PARSER_SHA)
    semantic = module(PARENT/'held_outcome02.py', '_selected_local6_semantic', parser_raw)
    SELECTED_CLEANUP_TYPES = (semantic.CleanupFailure,)
    reader = semantic.Reader(PARENT)
    raw = reader.body(request_path.name)
    require(sha(raw) == expected, 'exact independently reviewed request differs')
    request = parse(raw)
    require(type(request.get('schema_version')) is int and request['schema_version'] == 1
            and request['kind'] == 'original-import-held-success-parent-v1'
            and request['status'] == 'released-one-use-native-parent'
            and request['remaining'] == [] and request['identity'] == IDENTITY
            and request['case'] == 'success' and request['capsule_root'] == str(CAP)
            and request['capsule_commit'] == SOURCE, 'unreleased or different finite parent')
    require(reference(reader, request['caller']) == reader.body('launch_success01.py')
            and request['caller']['path'] == 'launch_success01.py', 'actual caller source differs')
    require(request['semantic_parser'] == {'path':'held_outcome02.py', 'sha256':PARSER_SHA},
            'semantic supplement differs')
    require(canonical(request['parent_limits']) == canonical(PARENT_LIMITS), 'parent storage limits differ')
    release_raw = reference(reader, request['release'])
    release = parse(release_raw)
    release_sha = sha(release_raw)
    evidence = request['evidence']
    require(set(evidence) == {'release_review', 'external_recovery', 'external_recovery_review'},
            'complete finite release/recovery evidence required')
    bodies = {key:reference(reader, ref) for key,ref in evidence.items()}
    require(release['release_review_sha256'] == evidence['release_review']['sha256']
            and release['external_capsule_recovery_sha256'] == evidence['external_recovery']['sha256']
            and release['external_recovery_review_sha256'] == evidence['external_recovery_review']['sha256'],
            'original release proof/body joins differ')
    review = parse(bodies['release_review'])
    require(review == {'schema_version':1, 'decision':'accepted-native-parent-release',
                       'identity':IDENTITY, 'capsule_commit':SOURCE,
                       'caller_sha256':request['caller']['sha256'],
                       'semantic_parser_sha256':PARSER_SHA,
                       'release_contract_sha256':contract(release)},
            'independent exact release review differs')
    recovery_review = parse(bodies['external_recovery_review'])
    require(recovery_review['decision'] == 'accepted-external-final-baseline-recovery'
            and recovery_review['capsule_commit'] == SOURCE
            and recovery_review['caller_sha256'] == request['caller']['sha256']
            and recovery_review['semantic_parser_sha256'] == PARSER_SHA
            and recovery_review['release_contract_sha256'] == contract(release)
            and recovery_review['actual_external_recovery_sha256'] == evidence['external_recovery']['sha256'],
            'independent exact recovered final baseline differs')
    semantic.sources(semantic.Reader(CAP), release)
    tools = CAP/'fixture_tools'
    sys.path.insert(0, str(tools))
    outer_raw = semantic.Reader(CAP).body('fixture_tools/outer_controller01.py')
    require(sha(outer_raw) == release['source_files']['fixture_tools/outer_controller01.py'],
            'genuine outer source differs')
    outer = module(tools/'outer_controller01.py', '_selected_local6_outer', outer_raw)
    require(Path(sys.modules['raw_receipts01'].__file__).resolve() == tools/'raw_receipts01.py',
            'raw helper import outside capsule')
    if not after:
        outer.check_release(CAP, release, 'success')
    else:
        # The original preclaim checker refuses every spent namespace. Final
        # rereads authenticate the same sources without invoking that refusal.
        outer.source_envelope(CAP, release)
    require(not any(n in sys.modules for n in ('numpy', 'torch', 'scipy')),
            'numerical import before native guard')
    reader.recheck()
    return request, release, release_sha, semantic, outer

def directory_identity(directory):
    """Acquire a current IO anchor; no directory-birth capability is claimed."""
    directory = Path(directory)
    require(directory.is_absolute() and directory.resolve() == directory,
            'canonical receipt directory required')
    parent = fd = None
    primary = None
    result = None
    try:
        parent = os.open(directory.parent, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        before = directory.lstat()
        fd = os.open(directory.name, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,
                     dir_fd=parent)
        key = lambda info:(info.st_dev,info.st_ino,info.st_mode,info.st_uid,info.st_gid)
        require(stat.S_ISDIR(before.st_mode) and key(before) == key(os.fstat(fd))
                == key(os.stat(directory.name,dir_fd=parent,follow_symlinks=False))
                == key(directory.lstat()) and directory.resolve() == directory,
                'receipt directory acquisition changed')
        p = key(os.fstat(parent))
        require(p == key(directory.parent.lstat()) and directory.parent.resolve() == directory.parent,
                'receipt parent acquisition changed')
        # Both the acquired directory and its parent entry are durable before release.
        os.fsync(fd)
        os.fsync(parent)
        require(p == key(os.fstat(parent)) == key(directory.parent.lstat())
                and key(before) == key(os.fstat(fd)) == key(directory.lstat())
                and directory.resolve() == directory, 'reservation changed during fsync')
        result = (p, key(before))
    except BaseException as error:
        primary = error
    cleanup(([lambda:os.close(fd)] if fd is not None else [])+
            ([lambda:os.close(parent)] if parent is not None else []), primary)
    return result

def write(directory, name, value, expected_identity=None):
    require('/' not in name and name not in ('', '.', '..'), 'flat parent output')
    require(expected_identity is not None, 'authenticated IO directory anchor required')
    directory = Path(directory)
    raw = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n').encode()
    require(len(raw) <= 65536, 'parent receipt bound')
    parent = owned = fd = None
    primary = None
    key = lambda info:(info.st_dev,info.st_ino,info.st_mode,info.st_uid,info.st_gid)
    try:
        require(directory.is_absolute() and directory.resolve() == directory,
                'receipt directory redirected')
        parent = os.open(directory.parent, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        require(key(os.fstat(parent)) == expected_identity[0] == key(directory.parent.lstat()),
                'receipt parent differs from acquired anchor')
        owned = os.open(directory.name, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,
                        dir_fd=parent)
        def joined():
            require(directory.parent.resolve() == directory.parent and directory.resolve() == directory
                    and key(os.fstat(parent)) == expected_identity[0] == key(directory.parent.lstat())
                    and key(os.fstat(owned)) == expected_identity[1] == key(directory.lstat())
                    == key(os.stat(directory.name,dir_fd=parent,follow_symlinks=False)),
                    'original acquired receipt directory changed')
        joined()
        fd = os.open(name, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,
                     0o600, dir_fd=owned)
        created = key(os.fstat(fd))
        offset = 0
        while offset < len(raw):
            size = os.write(fd, raw[offset:])
            require(size > 0, 'parent receipt short write')
            offset += size
        os.fsync(fd)
        final = os.fstat(fd)
        require(stat.S_ISREG(final.st_mode) and final.st_nlink == 1
                and final.st_size == len(raw) and key(final) == created
                and signature(final) == signature(os.stat(name,dir_fd=owned,follow_symlinks=False))
                == signature((directory/name).lstat()) and (directory/name).resolve() == directory/name,
                'atomic owned receipt member changed')
        joined()
        os.fsync(owned)
        joined()
    except BaseException as error:
        primary = error
    cleanup(([lambda:os.close(fd)] if fd is not None else [])+
            ([lambda:os.close(owned)] if owned is not None else [])+
            ([lambda:os.close(parent)] if parent is not None else []), primary)

def open_log(directory, name, expected_identity):
    """Atomic nofollow log FD; its acquired parent anchor is mandatory."""
    require(name in ('stdout.log','stderr.log'), 'finite owned log name')
    directory = Path(directory)
    parent = owned = fd = None
    primary = None
    key = lambda info:(info.st_dev,info.st_ino,info.st_mode,info.st_uid,info.st_gid)
    try:
        require(directory.is_absolute() and directory.resolve() == directory,
                'log directory redirected')
        parent = os.open(directory.parent, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        require(key(os.fstat(parent)) == expected_identity[0] == key(directory.parent.lstat()),
                'log parent differs from acquired anchor')
        owned = os.open(directory.name, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,
                        dir_fd=parent)
        def joined():
            require(directory.parent.resolve() == directory.parent and directory.resolve() == directory
                    and key(os.fstat(parent)) == expected_identity[0] == key(directory.parent.lstat())
                    and key(os.fstat(owned)) == expected_identity[1] == key(directory.lstat())
                    == key(os.stat(directory.name,dir_fd=parent,follow_symlinks=False)),
                    'original acquired log directory changed')
        joined()
        fd = os.open(name, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,
                     0o600, dir_fd=owned)
        actual = os.fstat(fd)
        require(stat.S_ISREG(actual.st_mode) and actual.st_nlink == 1 and actual.st_size == 0
                and signature(actual) == signature(os.stat(name,dir_fd=owned,follow_symlinks=False))
                == signature((directory/name).lstat()), 'atomic owned log file changed')
        joined()
        os.fsync(fd)
        os.fsync(owned)
        joined()
    except BaseException as error:
        primary = error
    # A failed acquisition closes the new log FD as well as both directory FDs.
    try:
        cleanup(([lambda:os.close(owned)] if owned is not None else [])+
                ([lambda:os.close(parent)] if parent is not None else []), primary)
    except BaseException as error:
        cleanup(([lambda:os.close(fd)] if fd is not None else []), error)
    return fd

def log_join(directory, name, fd, expected_identity, *, final=False):
    """Current actual FD/path join; growing child logs are sampled by inode."""
    directory = Path(directory)
    key = lambda info:(info.st_dev,info.st_ino,info.st_mode,info.st_uid,info.st_gid)
    require(directory.resolve() == directory and directory.parent.resolve() == directory.parent
            and key(directory.parent.lstat()) == expected_identity[0]
            and key(directory.lstat()) == expected_identity[1], 'log directory anchor changed')
    actual = os.fstat(fd)
    path = directory/name
    current = path.lstat()
    require(stat.S_ISREG(actual.st_mode) and actual.st_nlink == current.st_nlink == 1
            and key(actual) == key(current) and path.resolve() == path
            and actual.st_size < FILE, 'original log FD/path/file bound differs')
    if final:
        require(signature(actual) == signature(current), 'final log member changed')
    return {'path':name, 'device':actual.st_dev, 'inode':actual.st_ino,
            'bytes':actual.st_size, 'mode':stat.S_IMODE(actual.st_mode), 'links':actual.st_nlink}

def ticks(pid):
    return Path('/proc', str(pid), 'stat').read_text().rsplit(')',1)[1].split()[19]

def reap_controller(process, recorded_ticks):
    """Independent TERM, first wait, conditional KILL, and final reap."""
    primary = None
    reaped = False
    def retain(error):
        nonlocal primary
        primary = select(primary, error)
    def joined_signal(number):
        require(recorded_ticks is not None and ticks(process.pid) == recorded_ticks,
                'cannot stop unjoined controller identity')
        os.killpg(process.pid, number)
    try:
        if process.poll() is None:
            joined_signal(signal.SIGTERM)
    except BaseException as error:
        retain(error)
    try:
        process.wait(timeout=60)
        reaped = True
    except BaseException as error:
        if not isinstance(error, subprocess.TimeoutExpired):
            retain(error)
    if not reaped:
        try:
            joined_signal(signal.SIGKILL)
        except BaseException as error:
            retain(error)
        try:
            process.wait(timeout=5)
            reaped = True
        except BaseException as error:
            retain(error)
    if primary is not None:
        raise primary
    require(reaped, 'controller final reap unresolved')

def finish_check(semantic, outer, release, release_path, release_sha):
    reader = semantic.Reader(CAP)
    prefix = 'fixture_outer/'+IDENTITY
    for name in ('post-terminal-failure.json',):
        require(not os.path.lexists(CAP/prefix/name), 'actual outer late failure')
    base = 'research_artifacts/onchain-paper-replication-2026-09-24/runs/'+IDENTITY
    require(not os.path.lexists(CAP/base/'guard/finalization-error.json'), 'native finalization error')
    terminal = reader.json(prefix+'/terminal.json')
    require(terminal['status'] == 'passed' and terminal['identity'] == IDENTITY
            and terminal['source_commit'] == SOURCE and terminal['case'] == 'success'
            and terminal['error_type'] is None, 'original outer final outcome failed')
    closed = reader.json(prefix+'/cleanup.json')
    require(closed['supervisor_reaped'] is True and closed['pid_absence_verified'] is True
            and closed['unresolved_pid_absence'] is False, 'outer cleanup unresolved')
    proof = semantic.authenticate(CAP, release_path, release_sha)
    # Exact original post-tail semantics, with the reviewed bounded reader.
    raw = reader.body('fixture_tools/raw_receipts01.py')
    require(sha(raw) == release['source_files']['fixture_tools/raw_receipts01.py'], 'post-tail source differs')
    ns = {'Path':Path, 'GIB':GIB, 'require':require, 'digest':sha,
          'body':lambda root,name:reader.body(name),
          'metadata':lambda root,name:reader.json(name)}
    definition = next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef)
                      and n.name == 'authenticate_post_tail')
    exec(compile(ast.Module([definition], type_ignores=[]), 'original-post-tail', 'exec'), ns)
    post = ns['authenticate_post_tail'](CAP, IDENTITY, release['cases']['success']['job_resources'])
    reader.recheck()
    return {'held_semantics':proof, 'original_post_tail':post,
            'outer_terminal_sha256':sha(reader.body(prefix+'/terminal.json')),
            'outer_cleanup_sha256':sha(reader.body(prefix+'/cleanup.json'))}

def launch(request_path, expected):
    request, release, release_sha, semantic, outer = prepared(request_path, expected)
    storage = outer.module('_parent_storage', CAP/'tradingagents/research/onchain_replication/workflow_storage.py',
                           release['source_files']['tradingagents/research/onchain_replication/workflow_storage.py'])
    watch = storage.StorageWatch(PARENT, PARENT_LIMITS)
    watch.check()
    dedup(CAP, PARENT)
    require(mem_available() >= 6*GIB and shutil.disk_usage(CAP).free >= 10*GIB,
            'fresh startup memory/disk unavailable')
    resource.setrlimit(resource.RLIMIT_FSIZE, (FILE, FILE))
    require(resource.getrlimit(resource.RLIMIT_FSIZE) == (FILE,FILE), 'parent file limit differs')
    attempt = PARENT/'attempt'
    attempt.mkdir(exist_ok=True)
    directory_identity(attempt)  # fsync PARENT's attempt entry before any release.
    require(attempt.resolve() == attempt and attempt.is_dir(), 'parent attempt root redirected')
    directory = attempt/IDENTITY
    directory.mkdir(exist_ok=False)  # Permanently reserved, including preclaim failure.
    directory_pin = directory_identity(directory)
    primary = None
    process = None
    fds = []
    handlers = {}
    started = time.monotonic()
    controller_ticks = None
    proof = None
    command = [sys.executable, '-B', 'fixture_tools/outer_controller01.py',
               '--release', str(PARENT/request['release']['path']), '--case', 'success']
    def retain(error):
        nonlocal primary
        primary = select(primary, error)
    def interrupted(number, frame):
        raise InterruptedError('parent interrupted by signal '+str(number))
    def receipt(name, value):
        write(directory, name, value, directory_pin)
    try:
        for number in (signal.SIGINT, signal.SIGTERM):
            handlers[number] = signal.signal(number, interrupted)
        receipt('intent.json', {'identity':IDENTITY, 'source_commit':SOURCE,
            'request_sha256':expected, 'release_sha256':release_sha,
            'parent_pid':os.getpid(), 'parent_start_ticks':ticks(os.getpid()),
            'command':command, 'cwd':str(CAP), 'started_utc':datetime.now(timezone.utc).isoformat(),
            'file_limit':list(resource.getrlimit(resource.RLIMIT_FSIZE)),
            'identity_reuse_forbidden':True})
        for name in ('stdout.log','stderr.log'):
            fds.append(open_log(directory, name, directory_pin))
        public = ('PATH','HOME','LANG','LC_ALL','DBUS_SESSION_BUS_ADDRESS','XDG_RUNTIME_DIR')
        env = {name:os.environ[name] for name in public if name in os.environ}
        env.update(release['native_environment'])
        process = subprocess.Popen(command, cwd=CAP, env=env, stdout=fds[0], stderr=fds[1],
                                   start_new_session=True)
        controller_ticks = ticks(process.pid)
        receipt('controller.json', {'pid':process.pid, 'start_ticks':controller_ticks})
        while process.poll() is None:
            watch.check()
            require(shutil.disk_usage(CAP).free >= 10*GIB, 'parent disk floor breached')
            require(time.monotonic()-started < 2000, 'parent controller active deadline')
            for name,fd in zip(('stdout.log','stderr.log'),fds,strict=True):
                log_join(directory,name,fd,directory_pin)
            time.sleep(.25)
        require(process.returncode == 0, 'actual outer controller exited nonzero')
    except BaseException as error:
        retain(error)
    finally:
        if process is not None:
            try:
                reap_controller(process, controller_ticks)
            except BaseException as error:
                retain(error)
            try:
                supervisor_path = CAP/'fixture_outer'/IDENTITY/'supervisor.json'
                if primary is None and process.returncode == 0:
                    receipt('native-stop.json', {'original_outer_cleanup_delegated':True,
                        'qualification':'Original native/PID/cgroup cleanup still requires final semantic authentication.'})
                elif os.path.lexists(supervisor_path):
                    supervisor = semantic.Reader(CAP).json(str(supervisor_path.relative_to(CAP)))
                    result = outer.stop_native(CAP,
                        'research_artifacts/onchain-paper-replication-2026-09-24/runs/'+IDENTITY,
                        supervisor['pid'], retain_observation=lambda x:receipt('native-stop.json',x))
                else:
                    receipt('native-stop.json', {'native_owner_observed':False,
                        'cleanup_verified':False, 'qualification':'No fabricated native absence proof.'})
            except BaseException as error:
                retain(error)
        final_logs = []
        for name,fd in zip(('stdout.log','stderr.log'),fds):
            try:
                final_logs.append(log_join(directory,name,fd,directory_pin,final=True))
            except BaseException as error:
                retain(error)
        try:
            receipt('log-fd-joins.json', {'actual_log_fd_path_joins':final_logs})
        except BaseException as error:
            retain(error)
        try:
            cleanup([lambda fd=fd:os.close(fd) for fd in fds], primary)
        except BaseException as error:
            retain(error)
        try:
            if process is not None:
                receipt('controller-exit.json', {'pid':process.pid, 'start_ticks':controller_ticks,
                    'actual_exit_code':process.returncode, 'elapsed_seconds':time.monotonic()-started})
            if primary is None:
                require(process is not None and not os.path.lexists(Path('/proc',str(process.pid))),
                        'actual controller process absence unresolved')
                proof = finish_check(semantic, outer, release, PARENT/request['release']['path'], release_sha)
                # Reauthenticate immutable source/review/request bodies after the job.
                prepared(request_path, expected, after=True)
        except BaseException as error:
            retain(error)
        try:
            watch.check()
            require(shutil.disk_usage(CAP).free >= 10*GIB, 'parent final disk floor breached')
        except BaseException as error:
            retain(error)
        for number, handler in handlers.items():
            try:
                signal.signal(number, handler)
            except BaseException as error:
                retain(error)
        try:
            receipt('terminal.json', {'identity':IDENTITY, 'source_commit':SOURCE,
                'status':'passed' if primary is None else 'failed',
                'error_type':None if primary is None else type(primary).__name__,
                'actual_controller_exit':None if process is None else process.returncode,
                'semantic_proof':proof, 'elapsed_seconds':time.monotonic()-started,
                'scientific_publication':False, 'whole_external_outcome_recovery':False})
            watch.check()
            require(shutil.disk_usage(CAP).free >= 10*GIB, 'post-terminal parent disk floor breached')
        except BaseException as error:
            retain(error)
            try:
                receipt('post-terminal-failure.json', {'identity':IDENTITY, 'status':'failed',
                    'error_type':type(primary).__name__})
            except BaseException as later:
                retain(later)
    if primary is not None:
        raise primary
    return proof

if __name__ == '__main__':
    arguments = argparse.ArgumentParser()
    arguments.add_argument('--request', type=Path, required=True)
    arguments.add_argument('--request-sha256', required=True)
    arguments.add_argument('--launch', action='store_true')
    selected = arguments.parse_args()
    if selected.launch:
        launch(selected.request, selected.request_sha256)
    else:
        prepared(selected.request, selected.request_sha256)
