"""Read-only evidence collector. Its author cannot grant independent acceptance.
Only stdlib; no helper entry, subprocess, network, extraction or scientific import.
Run from a separate review with genuine pinned receipt references; stdout is evidence.
"""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import tarfile
import time

MAIN = Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
BASE = MAIN / 'research/onchain-paper-replication-2026-09-24/full_sources'
CAP = BASE / 'financial-wrapper-complete100-final-supplement-capture01-2026-10-04'
CAP_SHA = '86b787a7a01f15a596f356c16b1c1b55060549159fb7a301cc173c814cfcb67e'
SOURCE = '9dc5c79f738920b52947b4e63fed0397f1b5b207'
IDENTITY = 'financial-wrapper-classification-eager-complete100-20261003-01'
FILE = 4194304
TOTAL = 67108864
FLOOR = 10 * 1024**3
CHECKS = 0
READ_BYTES = 0
START = time.monotonic()


def require(test, message):
    global CHECKS
    CHECKS += 1
    if not test:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def signature(s):
    return (s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns, s.st_nlink)


def read(path):
    """Anchored non-following ordinary read with finite size and sampled rejoin."""
    global READ_BYTES
    require(time.monotonic() - START < 180, 'reader finite deadline')
    path = Path(path)
    require(path.is_absolute() and path == path.resolve(), 'canonical absolute file required')
    fds = []
    primary = None
    errors = []
    try:
        fds.append(os.open('/', os.O_RDONLY | os.O_DIRECTORY))
        for part in path.parts[1:-1]:
            fds.append(os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fds[-1]))
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fds[-1])
        fds.append(fd)
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_size <= FILE, 'bounded regular body required')
        require(READ_BYTES + before.st_size <= TOTAL, 'whole reader64MiB cumulative bound')
        READ_BYTES += before.st_size
        chunks = []
        count = 0
        while True:
            block = os.read(fd, min(65536, FILE + 1 - count))
            if not block:
                break
            chunks.append(block)
            count += len(block)
            require(count <= FILE, 'reader extent exceeded')
        require(signature(before) == signature(os.fstat(fd)) == signature(path.lstat()), 'read changed')
        require(path.resolve() == path and count == before.st_size, 'namespace or extent changed')
        return b''.join(chunks)
    except BaseException as error:
        primary = error
        raise
    finally:
        for fd in reversed(fds):
            try:
                os.close(fd)
            except BaseException as error:
                errors.append(error)
        if errors:
            chosen = primary if primary is not None and not isinstance(primary, Exception) else next((e for e in errors if not isinstance(e, Exception)), primary or errors[0])
            # Retain actual exception objects without calling user-controlled str/repr/add_note.
            chosen.evidence_cleanup_errors = tuple(errors)
            if chosen is not primary:
                raise chosen


def pinned(ref):
    require(type(ref) is dict and set(ref) == {'path', 'sha256'} and digest(ref['sha256']), 'genuine receipt path/hash unavailable')
    raw = read(ref['path'])
    require(sha(raw) == ref['sha256'], 'pinned body mismatch')
    return json.loads(raw)


def boundary():
    require(time.monotonic() - START < 180, 'review finite time bound')
    require(shutil.disk_usage(MAIN).free >= FLOOR, 'current 10GiB floor')


def validate(m):
    require(set(m) == {'schema_version', 'root_mode', 'members'} and m['schema_version'] == 1, 'manifest schema')
    rows = m['members']
    require(type(rows) is list and len(rows) <= 32768, 'finite membership')
    seen = {}
    size = 0
    for row in rows:
        name = row['path']
        p = PurePosixPath(name)
        require(type(name) is str and not p.is_absolute() and str(p) == name and '..' not in p.parts and name != '.', 'contained canonical path')
        require(name not in seen and row['kind'] in ('file', 'directory'), 'unique ordinary member')
        require(type(row['mode']) is int and 0 <= row['mode'] <= 0o7777, 'literal mode')
        require(str(p.parent) == '.' or seen.get(str(p.parent)) == 'directory', 'parent directory present')
        seen[name] = row['kind']
        if row['kind'] == 'file':
            require(set(row) == {'path','kind','mode','bytes','sha256'} and type(row['bytes']) is int and 0 <= row['bytes'] <= FILE and digest(row['sha256']), 'exact file schema')
            size += row['bytes']
        else:
            require(set(row) == {'path','kind','mode'}, 'exact directory schema')
    require(list(seen) == sorted(seen) and size <= TOTAL, 'complete sorted bounded scope')
    return rows


def census(root):
    root = Path(root)
    require(root.resolve() == root and stat.S_ISDIR(root.lstat().st_mode), 'canonical tree')
    rows = []
    def visit(directory, prefix):
        before = directory.lstat()
        names = sorted(os.listdir(directory))
        for name in names:
            path = directory / name
            rel = prefix + name
            s = path.lstat()
            row = {'path': rel, 'mode': stat.S_IMODE(s.st_mode)}
            require(len(rows) < 32768, 'finite census')
            if stat.S_ISDIR(s.st_mode):
                row['kind'] = 'directory'; rows.append(row); visit(path, rel + '/')
            else:
                require(stat.S_ISREG(s.st_mode), 'no links or special originals in this scope')
                raw = read(path)
                row.update(kind='file', bytes=len(raw), sha256=sha(raw)); rows.append(row)
            require(signature(path.lstat()) == signature(s), 'census member changed')
        require(signature(before) == signature(directory.lstat()) and names == sorted(os.listdir(directory)), 'census namespace changed')
    visit(root, '')
    return {'schema_version': 1, 'root_mode': stat.S_IMODE(root.lstat().st_mode), 'members': sorted(rows, key=lambda r:r['path'])}


class LimitedBytes(io.BytesIO):
    def write(self, body):
        require(self.tell() + len(body) <= FILE, 'canonical compressed output exceeds4MiB')
        return super().write(body)


def canonical(manifest, body_reader):
    """Independent stdlib encoding; exact comparison authenticates footer/PAX bytes too."""
    sink = LimitedBytes()
    with gzip.GzipFile(filename='', mode='wb', fileobj=sink, mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode='w|', format=tarfile.PAX_FORMAT) as archive:
            for row in validate(manifest):
                t = tarfile.TarInfo(row['path'])
                t.mode=row['mode']; t.uid=t.gid=0; t.uname=t.gname=''; t.mtime=0
                if row['kind'] == 'directory':
                    t.type=tarfile.DIRTYPE; t.size=0; archive.addfile(t)
                else:
                    raw = body_reader(row['path'])
                    require(len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'canonical body mismatch')
                    t.size=len(raw); archive.addfile(t, io.BytesIO(raw))
    return sink.getvalue()


def compare_scope(label, capture, selected, output, result):
    row=capture['scopes'][label]
    raw=read(selected / (label.upper()+'_MANIFEST01.json'))
    require(sha(raw)==row['manifest_sha256']==row['archive']['manifest_sha256'], 'manifest pin')
    manifest=json.loads(raw); rows=validate(manifest)
    archive=read(selected / ('complete-'+label+'01.tar.gz'))
    require(sha(archive)==row['archive']['sha256'] and len(archive)==row['archive']['bytes'], 'archive pin')
    dest=output / ('flat-'+label+'01')
    require(dest.resolve()==dest and stat.S_IMODE(dest.lstat().st_mode)==0o700, 'private actual flat directory')
    require(result['metadata_file']=='body-metadata.json', 'exact metadata filename')
    rawmeta=read(dest/'body-metadata.json'); require(sha(rawmeta)==result['metadata_sha256'], 'metadata hash')
    metadata=json.loads(rawmeta)
    require(metadata=={'schema_version':1, 'manifest':manifest, 'archive':row['archive'], 'flat_members':metadata['flat_members']}, 'exact flat metadata schema')
    mapping=metadata['flat_members']; files={r['path']:r for r in rows if r['kind']=='file'}
    require(set(mapping)==set(files) and len(set(mapping.values()))==len(files), 'complete one-to-one mapping')
    require(all(type(p) is str and PurePosixPath(p).name==p and p not in ('','.','..','body-metadata.json') for p in mapping.values()), 'flat contained file names')
    require(set(os.listdir(dest))==set(mapping.values())|{'body-metadata.json'}, 'complete flat namespace')
    for path in mapping.values():
        require(stat.S_IMODE((dest/path).lstat().st_mode)==0o600, 'private flat body mode')
    require(canonical(manifest, lambda n:read(dest/mapping[n]))==archive, 'whole canonical archive reconstruction')
    require(len(rows)==row['members']==result['members'] and len(files)==row['files']==result['regular_bodies'], 'actual scope denominators')
    require(sum(r['bytes'] for r in files.values())==row['logical_bytes'], 'logical denominator')
    require(result['archive_sha256']==sha(archive) and result['manifest_sha256']==sha(raw) and result['root_mode']==manifest['root_mode'], 'result archive/mode joins')
    for key in ('instantiated_posix_tree','recovered_tree_git_join','runtime_package_bodies_recovered','outside_stores_recovered','research_authority'):
        require(result[key] is False, 'no inferred authority')
    require(census(Path(row['snapshot']))==manifest, 'current complete immutable snapshot')
    return manifest, metadata, dest


def verify(config):
    # Validate all future pins before touching receipt paths or actual outputs.
    require(set(config)=={'remote','flat','terminal','root_output','actual_commit'}, 'configuration exact fields')
    for key in ('remote','flat','terminal'):
        ref=config[key]
        require(type(ref) is dict and set(ref)=={'path','sha256'} and digest(ref['sha256']) and type(ref['path']) is str and Path(ref['path']).is_absolute(), 'actual '+key+' unavailable')
    require(type(config['actual_commit']) is str and len(config['actual_commit'])==40 and all(c in '0123456789abcdef' for c in config['actual_commit']), 'actual commit unavailable')
    output=Path(config['root_output']); require(output.is_absolute() and output.resolve()==output, 'actual output root unavailable')
    boundary()
    remote=pinned(config['remote']); flat=pinned(config['flat']); terminal=pinned(config['terminal'])
    required=json.loads(read(CAP/'REQUIRED_BODIES01.json'))
    # The local fixed map has a descriptive envelope in some preparations: no discovery.
    if 'required' in required: required=required['required']
    require(type(required) is dict and len(required)==7 and sum(x['bytes'] for x in required.values())==1063336, 'exact fixed seven body map')
    rows=remote['selected_blobs']
    require([r['path'] for r in rows]==sorted(required), 'exact sorted selected scope')
    selected=output/'selected'
    for row in rows:
        raw=read(selected/row['path']); original=read(MAIN/row['path'])
        require(raw==original and len(raw)==row['bytes']==required[row['path']]['bytes'] and sha(raw)==row['sha256']==required[row['path']]['sha256'], 'actual recovered selected bytes')
        require(row['git_mode'] in ('100644','100755') and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_object'], 'actual blob identity')
    require(remote['remote_commit']==config['actual_commit'] and remote['selected_count']==7 and remote['selected_logical_bytes']==1063336, 'actual remote counts/commit')
    require(len(remote['operations'])==25 and all(r['exit']==0 and r['cleanup_failures']==[] for r in remote['operations']), 'actual operation cleanup')
    require(remote['status']=='fresh-actual-remote-complete100-final-supplement-recovered' and remote['genuine_run_or_native_started'] is False, 'actual byte recovery status')
    bundle=selected/CAP.relative_to(MAIN)
    raw=read(bundle/'CAPTURE01.json'); require(sha(raw)==CAP_SHA, 'immutable capture')
    capture=json.loads(raw)
    require(capture['source']==SOURCE and capture['identity']==IDENTITY and set(capture['scopes'])=={'contract','support'}, 'capture context')
    require(flat['status']=='COMPLETE_FINAL_SUPPLEMENT_CONTRACT_SUPPORT_BYTES_RECOVERED' and flat['capture_sha256']==CAP_SHA and flat['source']==SOURCE and flat['identity']==IDENTITY, 'actual flat context')
    require(flat['remote_receipt_sha256']==config['remote']['sha256'] and flat['remote_commit']==config['actual_commit'], 'actual remote-flat joins')
    for key in ('native_or_claim_started','original_git_reconstruction_performed_here','posix_tree_restored','installed_runtime_bodies'):
        require(flat[key] is False, 'flat scope boundary')
    require(flat['numerical_release'] is None and flat['whole_fit_capacity'] is None, 'no numerical authority')
    require(0<len(flat['floor_observations'])<=32 and all(r['free_bytes']>=FLOOR and 0<=r['seconds']<180 for r in flat['floor_observations']), 'recorded floor/time observations')
    scopes={label:compare_scope(label,capture,bundle,output,flat['scopes'][label]) for label in ('contract','support')}
    require(sum(len(x[0]['members']) for x in scopes.values())==290 and sum(len(x[1]['flat_members']) for x in scopes.values())==245, 'whole exact denominator')
    support, smeta, sdest=scopes['support']; roots=json.loads(read(bundle/'SUPPORT_ROOTS01.json'))
    require(len(roots)==9, 'all nine support roots')
    for name, ref in roots.items():
        actual=census(Path(ref['original']))
        wanted=[dict(r,path=r['path'][len(name)+1:]) for r in support['members'] if r['path'].startswith(name+'/')]
        require(actual['root_mode']==ref['original_root_mode'] and actual['members']==wanted, 'complete original support tree '+name)
    def support_read(name): return read(sdest/smeta['flat_members'][name])
    side=json.loads(support_read('CUMULATIVE_ORIGINAL_PATH01.json'))
    orig=read(side['original']); require(orig==support_read('CUMULATIVE19_REVIEW01.json') and sha(orig)==side['sha256'] and len(orig)==side['bytes'] and stat.S_IMODE(Path(side['original']).lstat().st_mode)==side['mode'], 'literal cumulative original')
    cm,cmeta,cdest=scopes['contract']
    qraw=read(cdest/cmeta['flat_members']['REQUEST_RELEASED01.json']); require(sha(qraw)==capture['request_sha256'], 'final actual request pin')
    q=json.loads(qraw); require(q['source']==q['design_source']==SOURCE and q['identity']==IDENTITY and len(q['source_files'])==338 and len(q['input_hashes'])==8, 'final request exact source/roles')
    contract={k:v for k,v in q.items() if k!='final_review'}
    encoded=(json.dumps(contract,sort_keys=True,indent=2)+'\n').encode()
    require(sha(encoded)==capture['contract_sha256'], 'immutable contract hash')
    for ref in list(q['proofs'].values())+[q['final_review']]: pinned(ref)
    require(q['proofs']['full_recovery']['sha256']==capture['baseline_full_recovery_sha256'] and q['final_review']['sha256']==capture['release_sha256'], 'actual baseline and release unchanged')
    src=Path(q['capsule_root'])
    for path,pin in q['source_files'].items(): require(sha(read(src/path))==pin, 'current source body '+path)
    require(sha(read(src/q['registration']))==q['registration_sha256'], 'current gate')
    parent=Path(q['parent_root'])
    require(sha(read(parent/'parent01.py'))==q['caller_sha256'], 'parent source')
    for path,pin in q['helper_hashes'].items(): require(sha(read(parent/path))==pin, 'parent helper '+path)
    # Terminal is pinned raw data. Tool-call provenance and historical process absence
    # cannot be established merely by parsing its self-report; different reviewer must join it.
    boundary()
    return {'status':'EVIDENCE_ONLY_REQUIRES_DIFFERENT_AUTHOR_ACCEPTANCE','checks':CHECKS,'source':SOURCE,'identity':IDENTITY,'capture_sha256':CAP_SHA,'remote_receipt_sha256':config['remote']['sha256'],'flat_receipt_sha256':config['flat']['sha256'],'terminal_sha256':config['terminal']['sha256'],'actual_commit':config['actual_commit'],'members':290,'files':245,'body_bytes':5262175,'acceptance':None,'numerical_release':None,'tool_provenance_independently_verified':False,'limitations':['Author of restoration tooling prepared this checker; final independent reviewer must inspect and run it or reconstruct evidence separately.','Terminal tool provenance, actual process absence, source Git HEAD/tree and current full CAP census need separate independent joins.','Sampled filesystem readback is not continuous writer exclusion, POSIX restoration, package-body recovery or capacity proof.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('config'); args=parser.parse_args()
    print(json.dumps(verify(json.loads(read(Path(args.config).absolute()))),sort_keys=True,indent=2))
