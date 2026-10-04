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
HERE = BASE / 'financial-genuine-wrapper-root-claimedrun-witness-tooling-capture01-2026-10-04'
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
 'tooling-preparation': BASE / 'financial-genuine-wrapper-claimedrun-sharded-witness-capture-preparation02-2026-10-04',
 'tooling-review': BASE / 'financial-genuine-wrapper-claimedrun-sharded-witness-capture-review02-2026-10-04',
}
SEALS = {'tooling-preparation':'97e91712054ba8af26302606e70c40577fc8059b8b10a1966d865d1806afe359', 'tooling-review':'d0bd935a4f693f56dd5b43a7a4b5f3f9463bdf7afee29995b61aa9ba44016c3f'}
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
    require(digest((BASE / 'financial-genuine-wrapper-claimedrun-actual-outcome-binding-review01-2026-10-04/MANIFEST01.json').read_bytes()) == '0c39988229162fd10b0d0df77f71163a4675a778251a8d75634283e40482bea2', 'actual independent binding review')
    require(digest((PARENT / 'proofs/FULL_SOURCE_RECOVERY01.json').read_bytes()) == '468dac2c06e570a89a30771c3f7e1b8e064e6f27e610acf01edcccf91c9a2825', 'actual Source339 recovery proof')
    for label, root in SCOPES.items():
        require(digest(r4.read(root, 'MANIFEST01.json')) == SEALS[label], 'exact frozen tooling seal')
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
    mapping = {'schema_version': 1, 'scope': 'complete two frozen witness-tooling source and review trees; links are literal metadata only; Source and final caller separately preserved', 'source_manifest_sha256': 'fdf77348b81a4d6df8b420b98530f5485900a0461636e1c201506106b036dfd8', 'source_archive_sha256': 'b5b6aad2f515447dc6566cfb716a20ef90031313d48f1ac903ab756735431e24', 'source_full_recovery_readback_sha256': '468dac2c06e570a89a30771c3f7e1b8e064e6f27e610acf01edcccf91c9a2825', 'source_commit': '0a2e7639b42b9423b90743feadcda4078aa21816', 'scope_trees': inventory, 'original_regular_logical_bytes': total, 'runtime_bodies_or_empirical_stores_recovered': False, 'links_followed_or_extracted': False, 'native_or_numerical_started': False}
    put(r4, union / 'ORIGINAL_TREES01.json', encoded(mapping))
    archives = {}
    for item in inventory:
        scope = item['scope']
        tree = union / scope
        metadata = {'schema_version':1, 'original_tree':item, 'source_commit':mapping['source_commit'], 'links_followed_or_extracted':False, 'research_authority':False}
        put(r4, tree / 'CAPTURE_ORIGINAL_TREE01.json', encoded(metadata))
        require(total + sum(len(encoded({'schema_version':1, 'original_tree':t, 'source_commit':mapping['source_commit'], 'links_followed_or_extracted':False, 'research_authority':False})) for t in inventory) + len(encoded(mapping)) <= LIMIT, 'whole originals plus metadata64MiB')
        require(time.monotonic()-start < 120 and shutil.disk_usage(HERE).free >= FLOOR, 'bounded per-scope pack')
        scope_manifest = r4.scan(tree)
        manifest_name = scope + '-manifest.json'
        archive_name = scope + '.tar.gz'
        put(r4, HERE / manifest_name, r4.encode(scope_manifest))
        archive = r4.pack(tree, scope_manifest, HERE / archive_name)
        archives[scope] = {'archive':dict(archive,path=archive_name), 'manifest':{'path':manifest_name,'bytes':len(r4.encode(scope_manifest)),'sha256':digest(r4.encode(scope_manifest))}, 'original_metadata_sha256':digest(encoded(metadata)), 'ordinary_members':len(scope_manifest['members'])}
    manifest = r4.scan(union)
    put(r4, HERE / 'union-manifest.json', r4.encode(manifest))
    r4.same(union, manifest)
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
    auth = {'schema_version': 1, 'status': 'complete-two-tooling-tree-byte-capture', 'archives': archives, 'union_mapping_sha256': digest(encoded(mapping)), 'ordinary_members': len(manifest['members']), 'original_trees': len(inventory), 'original_typed_members': sum(len(t['members']) for t in inventory), 'original_regular_members': sum(r['kind'] == 'file' for t in inventory for r in t['members']), 'original_lexical_links': sum(r['kind'] == 'lexical-symlink' for t in inventory for r in t['members']), 'source_capture_reused_unchanged': True, 'genuine_native_or_numerical_started': False, 'elapsed_seconds': time.monotonic() - start, 'free_bytes': shutil.disk_usage(HERE).free, 'qualification': 'Byte-only complete two-tooling-tree capture; both scope archives and original mapping metadata are required. Source339 and caller/witness captures remain separate scopes. No POSIX instantiation, installed-runtime recovery, empirical result or resource capacity follows.'}
    require(auth['free_bytes'] >= FLOOR, 'final10GiBfloor')
    put(r4, HERE / 'UNION_AUTHENTICATION01.json', encoded(auth))
    print(json.dumps({'status': auth['status'], 'archives': archives, 'original_trees': auth['original_trees'], 'original_regular_members': auth['original_regular_members'], 'original_lexical_links': auth['original_lexical_links']}))


if __name__ == '__main__':
    main()
