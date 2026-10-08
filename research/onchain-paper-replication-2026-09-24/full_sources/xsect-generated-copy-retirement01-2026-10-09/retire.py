"""Retire only the fully recovered generated duplicate; originals stay put."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import types

ROOT = Path.cwd().resolve()
HERE = Path(__file__).resolve().parent
F = HERE.parent
ENTRY = F / 'xsect-posix-recovery-entry01-2026-10-09'
TARGET = ROOT.parent / 'onchain-pilot-recovery/xsect-posix-recovery-20261009-01'
ORIGINAL = ROOT.parent / 'TradingAgents/data/xsect'


def emit(name, value):
    with (HERE / name).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def load(path):
    return json.loads(path.read_bytes())


assert ROOT == Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2))
resource.setrlimit(resource.RLIMIT_FSIZE, (4 * 1024**2, 4 * 1024**2))
os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:2])
os.nice(10)
signal.alarm(180)
assert not (HERE / 'INTENT01.json').exists()
assert not Path('/proc/1081924').exists()
assert TARGET.resolve(strict=True) == TARGET and ORIGINAL.resolve(strict=True) == ORIGINAL
assert TARGET != ORIGINAL and ORIGINAL.is_dir()
terminal = load(ENTRY / 'ROOT_TERMINAL01.json')
assert terminal['actual_root_exit_code'] == 0 and terminal['completed_batches'] == 29
review = F / 'xsect-posix-recovery-outcome-review01-2026-10-09/returned-increment01/RECOVERY_REVIEW01.json'
assert hashlib.sha256(review.read_bytes()).hexdigest() == '7e4593c06dbe68bbf8bf97b5bdce7d9d72c5a0634cc994f7292d2270c6d9121f'
contract = load(ENTRY / 'CONTRACT_FINAL01.json')
assert contract['target_root'] == str(TARGET) and contract['original_root'] == str(ORIGINAL)
reader = types.ModuleType('accepted_recovery_reader')
reader.__file__ = str(ENTRY / 'restore.py')
body = (ENTRY / 'restore.py').read_bytes()
assert hashlib.sha256(body).hexdigest() == 'f3b1f132a9474c8e3f5df7eb30e885b465bd75e65930a063bfbd634d0da49dad'
exec(compile(body, reader.__file__, 'exec'), vars(reader))
rows, directories, batches = reader.validate_selection(contract)
helper = F / 'xsect-posix-recovery01-2026-10-08/recover.py'
body = helper.read_bytes()
assert hashlib.sha256(body).hexdigest() == 'dcd7e1ca1e7017541ad3635bc229d7bd9d6326ad819bb6762958f9e6df008d3a'
module = types.ModuleType('accepted_reconstruction_verifier')
module.__file__ = str(helper)
exec(compile(body, str(helper), 'exec'), vars(module))
pin = load(ENTRY / 'ROOT_PIN01.json')['root_pin']
verified = module.verify_new_tree(TARGET, rows, directories,
    original_root=ORIGINAL, root_pin=pin, max_files=contract['expected_files'],
    max_total_bytes=contract['expected_raw_bytes'], max_file_bytes=contract['max_file_bytes'])
before = shutil.disk_usage(ROOT).free
emit('INTENT01.json', {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'target': str(TARGET), 'root_pin': pin, 'verified': verified,
    'returned_metadata_review_sha256': hashlib.sha256(review.read_bytes()).hexdigest(),
    'original': str(ORIGINAL), 'original_retirement': False, 'automatic_retry': False,
    'qualification': 'Generated duplicate only; original xsect and verified remote raw backup remain. Single Root owner; no universal writer-exclusion claim.'})
deleted = 0
fd = os.open(TARGET, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
try:
    module._identity(fd, pin)
    for row in rows:
        name = Path(row['relative_path'])
        with module._walk(fd, name.parts[:-1]) as parent:
            info = os.stat(name.name, dir_fd=parent, follow_symlinks=False)
            assert info.st_nlink == 1 and info.st_mode == row['mode']
            assert info.st_size == row['bytes'] and info.st_mtime_ns == row['mtime_ns']
            os.unlink(name.name, dir_fd=parent)
            deleted += 1
    for row in sorted(directories, key=lambda row: len(Path(row['relative_path']).parts), reverse=True):
        if row['relative_path'] == '.':
            continue
        name = Path(row['relative_path'])
        with module._walk(fd, name.parts[:-1]) as parent:
            os.rmdir(name.name, dir_fd=parent)
    module._identity(fd, pin)
except BaseException as error:
    emit('FAILED01.json', {'deleted_generated_files': deleted,
        'error_type': type(error).__name__, 'reason': str(error),
        'original_retirement': False, 'automatic_retry': False})
    raise
finally:
    os.close(fd)
assert (TARGET.lstat().st_dev, TARGET.lstat().st_ino) == tuple(pin)
TARGET.rmdir()
assert ORIGINAL.resolve(strict=True) == ORIGINAL and ORIGINAL.is_dir()
emit('COMPLETE01.json', {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'deleted_generated_files': deleted, 'generated_target_absent': not TARGET.exists(),
    'original_retirement': False, 'original_path_preserved': str(ORIGINAL),
    'disk_free_before_bytes': before, 'disk_free_after_bytes': shutil.disk_usage(ROOT).free,
    'raw_backup_and_all_recovery_receipts_preserved': True})
print('Retired only verified generated duplicate; original xsect retained')
