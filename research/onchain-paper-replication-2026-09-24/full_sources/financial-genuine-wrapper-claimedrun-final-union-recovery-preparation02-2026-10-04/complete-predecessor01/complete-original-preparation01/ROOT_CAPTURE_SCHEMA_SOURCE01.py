"""Capture final released caller and complete witnesses as ordinary opaque bytes."""
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import sys
import time
from pathlib import Path

MAIN = Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
BASE = MAIN / 'research/onchain-paper-replication-2026-09-24/full_sources'
HERE = Path(__file__).resolve().parent
PARENT = Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-root-launch-20261004-01')
SOURCE = Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-native-20261004-01/source')
SOURCE_CAPTURE = BASE / 'financial-genuine-wrapper-root-recordfix-capture01-2026-10-04'
PRIMITIVES = BASE / 'held-consumer-final-recovery-preparation04-2026-10-03'
PINS = {
    'recovery04.py': 'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a',
    'owned_io.py': '09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb',
    'bounded_git01.py': 'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f',
}
SCOPES = {
    'actual-parent': PARENT,
    'root-parent-adoption': BASE / 'financial-genuine-wrapper-root-recordfix-parent-adoption01-2026-10-04',
    'final-parent-review': BASE / 'financial-genuine-wrapper-recordfix-final-parent-review01-2026-10-04',
    'root-verifier-binding': BASE / 'financial-genuine-wrapper-root-recordfix-verifier-binding01-2026-10-04',
    'actual-verifier-review': BASE / 'financial-genuine-wrapper-recordfix-generated-verifier-review01-2026-10-04',
    'binder-preparation': BASE / 'financial-genuine-wrapper-recordfix-outcome-verifier-preparation01-2026-10-04',
    'binder-review': BASE / 'financial-genuine-wrapper-recordfix-outcome-verifier-review01-2026-10-04',
    'caller-preparation': BASE / 'financial-genuine-wrapper-recordfix-parent-preparation01-2026-10-04',
    'caller-review': BASE / 'financial-genuine-wrapper-recordfix-parent-review01-2026-10-04',
    'verifier-preparation': BASE / 'financial-genuine-wrapper-first-outcome-verifier-preparation03-2026-10-04',
    'verifier-review': BASE / 'financial-genuine-wrapper-first-outcome-verifier-review03-2026-10-04',
}
FILE = 4 * 1024**2
LIMIT = 64 * 1024**2
FLOOR = 10 * 1024**3


def digest(body):
    return hashlib.sha256(body).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def require(value, message):
    if not value:
        raise ValueError(message)


def put(path, body):
    require(len(body) <= FILE, 'bounded output body')
    with path.open('xb') as output:
        output.write(body)
        output.flush()
        os.fsync(output.fileno())
    require(path.read_bytes() == body, 'saved body readback')


def main():
    start = time.monotonic()
    require(not os.path.lexists(HERE / 'union-bytes01'), 'one-use union namespace')
    require(shutil.disk_usage(HERE).free >= FLOOR, 'initial10GiBfloor')
    for name, pin in PINS.items():
        require(digest((PRIMITIVES / name).read_bytes()) == pin, 'original primitive changed')
    sys.path.insert(0, str(PRIMITIVES))
    spec = importlib.util.spec_from_file_location('final_union_r4', PRIMITIVES / 'recovery04.py')
    r4 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(r4)
    source_manifest = json.loads((SOURCE_CAPTURE / 'source-manifest.json').read_bytes())
    require(digest((SOURCE_CAPTURE / 'source-manifest.json').read_bytes()) == '26c67e9c9b28dd4cd607ab3833fa14143d6e8e4c7c3617024275294940ffbc53', 'original Source manifest pin')
    require(digest((SOURCE_CAPTURE / 'source.tar.gz').read_bytes()) == '8d49d60b509bc9c95cd04274127b12387b8070295499dad3d24db63b9a376efb', 'original Source archive pin')
    r4.same(SOURCE, source_manifest)
    require(digest((PARENT / 'REQUEST_FINAL02.json').read_bytes()) == '28f2ae5340d38ac71450c8947c5b1ad30ac4192481da81596684445c9cf9b52e', 'actual final caller request')
    require(digest((SCOPES['actual-verifier-review'] / 'MANIFEST01.json').read_bytes()) == 'c856494d3c46b5f26241a72e66219adf35d79905b1117291cdc5b22e1601814a', 'actual independent binding review')
    union = HERE / 'union-bytes01'
    union.mkdir(mode=0o700)
    inventory = []
    total = 0
    for scope, original in sorted(SCOPES.items()):
        require(original.is_absolute() and original.resolve() == original, 'canonical original scope')
        destination = union / scope
        destination.mkdir(mode=0o700)
        members = []
        def visit(path, relative):
            nonlocal total
            require(time.monotonic() - start < 120 and len(inventory) + len(members) < 32768, 'finite capture')
            r4.path_name(relative) if relative != '.' else None
            info = path.lstat()
            before = r4.sig(info)
            row = {'path': relative, 'mode': stat.S_IMODE(info.st_mode)}
            if stat.S_ISLNK(info.st_mode):
                row.update(kind='lexical-symlink', target=os.readlink(path))
            elif stat.S_ISDIR(info.st_mode):
                row['kind'] = 'directory'
                if relative != '.':
                    (destination / relative).mkdir(mode=0o700)
                members.append(row)
                for child in sorted(path.iterdir(), key=lambda p: p.name):
                    visit(child, child.name if relative == '.' else relative + '/' + child.name)
                require(r4.sig(path.lstat()) == before, 'original directory changed')
                return
            else:
                require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size <= FILE, 'original file type/link/extent')
                body = r4.read(original, relative)
                total += len(body)
                require(total <= LIMIT and shutil.disk_usage(HERE).free >= FLOOR, 'whole logical and disk limits')
                row.update(kind='file', bytes=len(body), sha256=digest(body), union_path=scope + '/' + relative)
                put(destination / relative, body)
            require(r4.sig(path.lstat()) == before, 'original member changed')
            members.append(row)
        visit(original, '.')
        members.sort(key=lambda row: row['path'])
        inventory.append({'scope': scope, 'original_root': str(original), 'members': members})
    mapping = {'schema_version': 1, 'scope': 'complete actual final caller, concrete verifier, source preparations and independent full witness trees; links are literal metadata only', 'source_manifest_sha256': '26c67e9c9b28dd4cd607ab3833fa14143d6e8e4c7c3617024275294940ffbc53', 'source_archive_sha256': '8d49d60b509bc9c95cd04274127b12387b8070295499dad3d24db63b9a376efb', 'source_full_recovery_readback_sha256': 'f86497ee97d6b5d91066db1aa2520d1bed844165b4e08d7169a5917c5bfda4df', 'source_commit': '649fb8a11089524aaef7843dffeeb90a3a55ca17', 'scope_trees': inventory, 'original_regular_logical_bytes': total, 'runtime_bodies_or_empirical_stores_recovered': False, 'links_followed_or_extracted': False, 'native_or_numerical_started': False}
    put(union / 'ORIGINAL_TREES01.json', encoded(mapping))
    manifest = r4.scan(union)
    put(HERE / 'union-manifest.json', r4.encode(manifest))
    archive = r4.pack(union, manifest, HERE / 'union.tar.gz')
    r4.same(SOURCE, source_manifest)
    # Every original scope is reauthenticated after archive creation.
    for item in inventory:
        original = Path(item['original_root'])
        for row in item['members']:
            path = original if row['path'] == '.' else original / row['path']
            info = path.lstat()
            require(stat.S_IMODE(info.st_mode) == row['mode'], 'original mode changed')
            if row['kind'] == 'file':
                require(digest(r4.read(original, row['path'])) == row['sha256'], 'original final body changed')
            elif row['kind'] == 'lexical-symlink':
                require(stat.S_ISLNK(info.st_mode) and os.readlink(path) == row['target'], 'original lexical link changed')
            else:
                require(stat.S_ISDIR(info.st_mode), 'original directory changed type')
    auth = {'schema_version': 1, 'status': 'complete-final-caller-review-byte-capture', 'archive': archive, 'union_mapping_sha256': digest(encoded(mapping)), 'ordinary_members': len(manifest['members']), 'original_trees': len(inventory), 'original_typed_members': sum(len(t['members']) for t in inventory), 'original_regular_members': sum(r['kind'] == 'file' for t in inventory for r in t['members']), 'original_lexical_links': sum(r['kind'] == 'lexical-symlink' for t in inventory for r in t['members']), 'source_capture_reused_unchanged': True, 'genuine_native_or_numerical_started': False, 'elapsed_seconds': time.monotonic() - start, 'free_bytes': shutil.disk_usage(HERE).free, 'qualification': 'Byte-only complete final-caller supplement; original Source325 remains separately completely recovered. No POSIX instantiation, installed-runtime recovery, empirical result or resource capacity follows.'}
    require(auth['free_bytes'] >= FLOOR, 'final10GiBfloor')
    put(HERE / 'UNION_AUTHENTICATION01.json', encoded(auth))
    print(json.dumps({'status': auth['status'], 'archive': archive, 'original_trees': auth['original_trees'], 'original_regular_members': auth['original_regular_members'], 'original_lexical_links': auth['original_lexical_links']}))


if __name__ == '__main__':
    main()
