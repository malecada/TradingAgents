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
HERE = BASE / 'financial-genuine-wrapper-root-claimedrun-sharded-witness-capture01-2026-10-04'
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
    'capture-preparation': BASE / 'financial-genuine-wrapper-claimedrun-final-capture-preparation02-2026-10-04',
    'capture-review': BASE / 'financial-genuine-wrapper-claimedrun-final-capture-review02-2026-10-04',
    'recovery-preparation': BASE / 'financial-genuine-wrapper-claimedrun-final-union-recovery-preparation02-2026-10-04',
    'recovery-review': BASE / 'financial-genuine-wrapper-claimedrun-final-union-recovery-review02-2026-10-04',
    'actual-capture-review': BASE / 'financial-genuine-wrapper-claimedrun-actual-final-capture-review02-2026-10-04',
}
SEALS = {'capture-preparation': 'a2b07ace33f3f6a1394e04949c5089a3552567573d858f76f5a5f1462bcb6ea3', 'capture-review': 'e2c313a07bb3051cd95d08931a626301b84c87e004425a33f8ef64e3a1ff5bc9', 'recovery-preparation': '6381d52f220a8a2669e8bb03a4614601e3a41ed916863a77a95bff78a3d4897a', 'recovery-review': '348a5c6a0b72fb62e989ff5cda2b3fab4ad13fcc9cd2c01487eefe1f885bfeb3', 'actual-capture-review': None}
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


def pack_shards(r4, planner, union, manifest, here, start):
    r4.validate(manifest)
    require(sum(r['bytes'] for r in manifest['members'] if r['kind']=='file') <= LIMIT, 'whole virtual logical limit')
    groups = planner.partition(manifest)
    trees = here / 'shard-trees'
    archives = here / 'shards'
    trees.mkdir(mode=0o700)
    archives.mkdir(mode=0o700)
    records = []
    for number, group in enumerate(groups):
        require(time.monotonic()-start < 120 and shutil.disk_usage(here).free >= FLOOR, 'bounded shard operation')
        name = 'shard-%04d' % number
        tree = trees / name
        tree.mkdir(mode=group['manifest']['root_mode'])
        for row in group['manifest']['members']:
            require(time.monotonic()-start < 120 and shutil.disk_usage(here).free >= FLOOR, 'bounded shard member')
            path = tree / row['path']
            if row['kind']=='directory':
                path.mkdir(mode=row['mode'])
            else:
                body = r4.read(union,row['path'])
                require(len(body)==row['bytes'] and digest(body)==row['sha256'], 'exact virtual body')
                put(r4,path,body)
            require(stat.S_IMODE(path.lstat().st_mode)==row['mode'], 'literal shard mode')
        require(r4.scan(tree)==group['manifest'], 'complete physical shard tree')
        manifest_path = 'shards/'+name+'-manifest.json'
        manifest_body = r4.encode(group['manifest'])
        put(r4,here/manifest_path,manifest_body)
        archive_path = 'shards/'+name+'.tar.gz'
        archive = r4.pack(tree,group['manifest'],here/archive_path)
        require(archive['bytes'] <= FILE, 'original physical archive cap')
        records.append({**{k:v for k,v in group.items() if k!='manifest'}, 'id':name,
            'manifest':{'path':manifest_path,'bytes':len(manifest_body),'sha256':digest(manifest_body)},
            'archive':{'path':archive_path,**archive}})
    r4.same(union,manifest)
    virtual = r4.encode(manifest)
    index = {'schema_version':1,'kind':'complete-final-union-shards-v1',
        'virtual_manifest':{'path':'union-manifest.json','bytes':len(virtual),'sha256':digest(virtual)},
        'limits':{'logical_bytes':planner.LOGICAL,'typed_members':planner.MEMBERS,'archive_bytes':FILE},
        'regular_bodies':sum(r['kind']=='file' for r in manifest['members']),'shards':records}
    body = encoded(index)
    put(r4,here/'SHARD_INDEX01.json',body)
    return {'path':'SHARD_INDEX01.json','bytes':len(body),'sha256':digest(body),'virtual_manifest_sha256':digest(virtual)},len(records)


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
    require(digest(r4.read(HERE, 'shards01.py')) == '9c38c0893790c22e3b0142a8ab175dceb9b14dd0aeeb80edc206e5329ffcbbba', 'exact shard planner')
    planner_spec = importlib.util.spec_from_file_location('final_union_shards', HERE / 'shards01.py')
    planner = importlib.util.module_from_spec(planner_spec)
    planner_spec.loader.exec_module(planner)
    source_manifest = json.loads((SOURCE_CAPTURE / 'source-manifest.json').read_bytes())
    require(digest((SOURCE_CAPTURE / 'source-manifest.json').read_bytes()) == 'fdf77348b81a4d6df8b420b98530f5485900a0461636e1c201506106b036dfd8', 'original Source manifest pin')
    require(digest((SOURCE_CAPTURE / 'source.tar.gz').read_bytes()) == 'b5b6aad2f515447dc6566cfb716a20ef90031313d48f1ac903ab756735431e24', 'original Source archive pin')
    r4.same(SOURCE, source_manifest)
    require(digest((PARENT / 'REQUEST_FINAL03.json').read_bytes()) == '529c9bf3c587e6160a217e8eb339882e59433b6fc0f759d0009d261f872b2bd8', 'actual final caller request')
    require(digest((BASE / 'financial-genuine-wrapper-claimedrun-actual-outcome-binding-review01-2026-10-04/MANIFEST01.json').read_bytes()) == '0c39988229162fd10b0d0df77f71163a4675a778251a8d75634283e40482bea2', 'actual independent binding review')
    for label, root in SCOPES.items():
        require(type(SEALS[label]) is str and len(SEALS[label]) == 64, 'genuine final witness seal unavailable')
        require(digest(r4.read(root, 'MANIFEST01.json')) == SEALS[label], 'exact frozen witness seal')
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
    mapping = {'schema_version': 1, 'scope': 'complete five sharded-capture and recovery source/review witness trees; original final caller union is separately preserved; links are literal metadata only', 'source_manifest_sha256': 'fdf77348b81a4d6df8b420b98530f5485900a0461636e1c201506106b036dfd8', 'source_archive_sha256': 'b5b6aad2f515447dc6566cfb716a20ef90031313d48f1ac903ab756735431e24', 'source_full_recovery_readback_sha256': '468dac2c06e570a89a30771c3f7e1b8e064e6f27e610acf01edcccf91c9a2825', 'source_commit': '0a2e7639b42b9423b90743feadcda4078aa21816', 'scope_trees': inventory, 'original_regular_logical_bytes': total, 'runtime_bodies_or_empirical_stores_recovered': False, 'links_followed_or_extracted': False, 'native_or_numerical_started': False}
    put(r4, union / 'ORIGINAL_TREES01.json', encoded(mapping))
    manifest = r4.scan(union)
    put(r4, HERE / 'union-manifest.json', r4.encode(manifest))
    index, shard_count = pack_shards(r4, planner, union, manifest, HERE, start)
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
    auth = {'schema_version': 1, 'status': 'complete-sharded-witness-review-byte-capture', 'index': index, 'shard_count': shard_count, 'union_mapping_sha256': digest(encoded(mapping)), 'ordinary_members': len(manifest['members']), 'original_trees': len(inventory), 'original_typed_members': sum(len(t['members']) for t in inventory), 'original_regular_members': sum(r['kind'] == 'file' for t in inventory for r in t['members']), 'original_lexical_links': sum(r['kind'] == 'lexical-symlink' for t in inventory for r in t['members']), 'source_capture_reused_unchanged': True, 'genuine_native_or_numerical_started': False, 'elapsed_seconds': time.monotonic() - start, 'free_bytes': shutil.disk_usage(HERE).free, 'qualification': 'Byte-only complete five-tree witness supplement; original Source339 and final caller union remain separate preservation scopes. No POSIX instantiation, installed-runtime recovery, empirical result or resource capacity follows.'}
    require(auth['free_bytes'] >= FLOOR, 'final10GiBfloor')
    put(r4, HERE / 'UNION_AUTHENTICATION01.json', encoded(auth))
    print(json.dumps({'status': auth['status'], 'index': index, 'shard_count': shard_count, 'original_trees': auth['original_trees'], 'original_regular_members': auth['original_regular_members'], 'original_lexical_links': auth['original_lexical_links']}))


if __name__ == '__main__':
    main()
