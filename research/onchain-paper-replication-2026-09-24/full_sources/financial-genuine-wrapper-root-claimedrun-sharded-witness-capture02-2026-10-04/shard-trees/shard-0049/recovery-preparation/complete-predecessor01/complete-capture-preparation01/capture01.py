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
HERE = BASE / 'financial-genuine-wrapper-root-claimedrun-final-capture01-2026-10-04'
PARENT = Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-root-launch-20261004-01')
SOURCE = Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
SOURCE_CAPTURE = BASE / 'financial-genuine-wrapper-root-claimedrun-source339-capture01-2026-10-04'
PRIMITIVES = BASE / 'held-consumer-final-recovery-preparation04-2026-10-03'
PINS = {
    'recovery04.py': 'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a',
    'owned_io.py': '09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb',
    'bounded_git01.py': 'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f',
}
SCOPES = {
    'actual-parent': PARENT,
    'root-parent-adoption': BASE / 'financial-genuine-wrapper-root-claimedrun-parent-adoption01-2026-10-04',
    'root-parent-final-contract': BASE / 'financial-genuine-wrapper-root-claimedrun-parent-final-contract01-2026-10-04',
    'caller-preparation': BASE / 'financial-genuine-wrapper-claimedrun-parent-preparation01-2026-10-04',
    'caller-review': BASE / 'financial-genuine-wrapper-claimedrun-parent-review01-2026-10-04',
    'final-parent-review': BASE / 'financial-genuine-wrapper-claimedrun-parent-final-release-review01-2026-10-04',
    'binder-preparation01': BASE / 'financial-genuine-wrapper-claimedrun-outcome-binding-preparation01-2026-10-04',
    'binder-preparation02': BASE / 'financial-genuine-wrapper-claimedrun-outcome-binding-preparation02-2026-10-04',
    'binder-review': BASE / 'financial-genuine-wrapper-claimedrun-outcome-binding-review02-2026-10-04',
    'root-verifier-binding': BASE / 'financial-genuine-wrapper-root-claimedrun-outcome-binding-generation01-2026-10-04',
    'actual-verifier-review': BASE / 'financial-genuine-wrapper-claimedrun-actual-outcome-binding-review01-2026-10-04',
    'claim-window-review': BASE / 'financial-genuine-wrapper-claimedrun-claim-window-review01-2026-10-04',
    'withheld-source-recovery-preparation': BASE / 'financial-genuine-wrapper-claimedrun-source-recovery-preparation01-2026-10-04',
    'withheld-source-recovery-review': BASE / 'financial-genuine-wrapper-claimedrun-source-recovery-review01-2026-10-04',
    'witness-capture-preparation': BASE / 'financial-genuine-wrapper-claimedrun-witness-capture-preparation01-2026-10-04',
    'witness-capture-review': BASE / 'financial-genuine-wrapper-claimedrun-witness-capture-review01-2026-10-04',
    'original-verifier-preparation': BASE / 'financial-genuine-wrapper-first-outcome-verifier-preparation03-2026-10-04',
    'original-verifier-review': BASE / 'financial-genuine-wrapper-first-outcome-verifier-review03-2026-10-04',
    'original-binder-preparation': BASE / 'financial-genuine-wrapper-recordfix-outcome-verifier-preparation01-2026-10-04',
    'original-binder-review': BASE / 'financial-genuine-wrapper-recordfix-outcome-verifier-review01-2026-10-04',
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


def put(r4, path, body):
    require(len(body) <= FILE, 'bounded output body')
    with r4.new_file(path) as fd:
        offset = 0
        while offset < len(body):
            written = os.write(fd, body[offset:])
            require(written > 0, 'short output write')
            offset += written
        os.fsync(fd)
    require(r4.read(path.parent, path.name) == body, 'saved body readback')


def main():
    start = time.monotonic()
    require(Path(__file__).resolve().parent == HERE, 'fixed Root-installed final capture')
    require(not os.path.lexists(PARENT / 'attempt'), 'prelaunch final caller only')
    require(not os.path.lexists(HERE / 'union-bytes01'), 'one-use union namespace')
    require(shutil.disk_usage(HERE).free >= FLOOR, 'initial10GiBfloor')
    for name, pin in PINS.items():
        require(digest((PRIMITIVES / name).read_bytes()) == pin, 'original primitive changed')
    sys.path.insert(0, str(PRIMITIVES))
    spec = importlib.util.spec_from_file_location('final_union_r4', PRIMITIVES / 'recovery04.py')
    r4 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(r4)
    source_manifest = json.loads((SOURCE_CAPTURE / 'source-manifest.json').read_bytes())
    require(digest((SOURCE_CAPTURE / 'source-manifest.json').read_bytes()) == 'fdf77348b81a4d6df8b420b98530f5485900a0461636e1c201506106b036dfd8', 'original Source manifest pin')
    require(digest((SOURCE_CAPTURE / 'source.tar.gz').read_bytes()) == 'b5b6aad2f515447dc6566cfb716a20ef90031313d48f1ac903ab756735431e24', 'original Source archive pin')
    r4.same(SOURCE, source_manifest)
    require(digest((PARENT / 'REQUEST_FINAL03.json').read_bytes()) == '529c9bf3c587e6160a217e8eb339882e59433b6fc0f759d0009d261f872b2bd8', 'actual final caller request')
    require(digest((SCOPES['actual-verifier-review'] / 'MANIFEST01.json').read_bytes()) == '0c39988229162fd10b0d0df77f71163a4675a778251a8d75634283e40482bea2', 'actual independent binding review')
    require(digest((PARENT / 'proofs/FULL_SOURCE_RECOVERY01.json').read_bytes()) == '468dac2c06e570a89a30771c3f7e1b8e064e6f27e610acf01edcccf91c9a2825', 'actual Source339 recovery proof')
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
                put(r4, destination / relative, body)
            require(r4.sig(path.lstat()) == before, 'original member changed')
            members.append(row)
        visit(original, '.')
        members.sort(key=lambda row: row['path'])
        inventory.append({'scope': scope, 'original_root': str(original), 'members': members})
    mapping = {'schema_version': 1, 'scope': 'complete actual final caller, concrete verifier, source preparations and independent full witness trees; links are literal metadata only', 'source_manifest_sha256': 'fdf77348b81a4d6df8b420b98530f5485900a0461636e1c201506106b036dfd8', 'source_archive_sha256': 'b5b6aad2f515447dc6566cfb716a20ef90031313d48f1ac903ab756735431e24', 'source_full_recovery_readback_sha256': '468dac2c06e570a89a30771c3f7e1b8e064e6f27e610acf01edcccf91c9a2825', 'source_commit': '0a2e7639b42b9423b90743feadcda4078aa21816', 'scope_trees': inventory, 'original_regular_logical_bytes': total, 'runtime_bodies_or_empirical_stores_recovered': False, 'links_followed_or_extracted': False, 'native_or_numerical_started': False}
    put(r4, union / 'ORIGINAL_TREES01.json', encoded(mapping))
    manifest = r4.scan(union)
    put(r4, HERE / 'union-manifest.json', r4.encode(manifest))
    archive = r4.pack(union, manifest, HERE / 'union.tar.gz')
    r4.same(SOURCE, source_manifest)
    # Re-enumerate complete originals; a late extra member must not be omitted.
    for item in inventory:
        original = Path(item['original_root'])
        require(original.resolve() == original, 'final original root redirected')
        observed = []
        def authenticate(path, relative):
            require(time.monotonic() - start < 120 and len(observed) < 32768, 'finite final original scan')
            info = path.lstat()
            before = r4.sig(info)
            row = {'path': relative, 'mode': stat.S_IMODE(info.st_mode)}
            if stat.S_ISLNK(info.st_mode):
                row.update(kind='lexical-symlink', target=os.readlink(path))
            elif stat.S_ISDIR(info.st_mode):
                row['kind'] = 'directory'
                observed.append(row)
                for child in sorted(path.iterdir(), key=lambda p: p.name):
                    authenticate(child, child.name if relative == '.' else relative + '/' + child.name)
                require(r4.sig(path.lstat()) == before, 'final original directory changed')
                return
            else:
                require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size <= FILE, 'final original file type/link/extent')
                body = r4.read(original, relative)
                row.update(kind='file', bytes=len(body), sha256=digest(body), union_path=item['scope'] + '/' + relative)
            require(r4.sig(path.lstat()) == before, 'final original member changed')
            observed.append(row)
        authenticate(original, '.')
        observed.sort(key=lambda row: row['path'])
        require(observed == item['members'], 'complete original membership/body/mode/literal-link differs')
    auth = {'schema_version': 1, 'status': 'complete-final-caller-review-byte-capture', 'archive': archive, 'union_mapping_sha256': digest(encoded(mapping)), 'ordinary_members': len(manifest['members']), 'original_trees': len(inventory), 'original_typed_members': sum(len(t['members']) for t in inventory), 'original_regular_members': sum(r['kind'] == 'file' for t in inventory for r in t['members']), 'original_lexical_links': sum(r['kind'] == 'lexical-symlink' for t in inventory for r in t['members']), 'source_capture_reused_unchanged': True, 'genuine_native_or_numerical_started': False, 'elapsed_seconds': time.monotonic() - start, 'free_bytes': shutil.disk_usage(HERE).free, 'qualification': 'Byte-only complete final-caller supplement; original Source339 remains separately completely recovered. No POSIX instantiation, installed-runtime recovery, empirical result or resource capacity follows.'}
    require(auth['free_bytes'] >= FLOOR, 'final10GiBfloor')
    put(r4, HERE / 'UNION_AUTHENTICATION01.json', encoded(auth))
    print(json.dumps({'status': auth['status'], 'archive': archive, 'original_trees': auth['original_trees'], 'original_regular_members': auth['original_regular_members'], 'original_lexical_links': auth['original_lexical_links']}))


if __name__ == '__main__':
    main()
