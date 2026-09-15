"""Archive only failed invented engineering fixtures; no execution, market I/O or extraction."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tarfile


def encoded(value):
    return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()


def file_hash(path):
    out=hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda:source.read(1024**2),b''):out.update(chunk)
    return out.hexdigest()


def inventory(root):
    root=root.resolve(strict=True)
    assignment=json.loads((root/'package/assignment.json').read_bytes())
    claim=json.loads((root/'package/claim.json').read_bytes())
    if claim.get('synthetic') is not True or assignment.get('target')!='options-timing-20260915':raise ValueError('invented successor fixture only')
    package=set(assignment['package_files'])|{'assignment.json','claim.json'}
    allowed_dirs={'package','data'}|{'data/'+g for g in ('bootstrap','known','selected','daily','final')}
    for name in package:
        allowed_dirs.update('package/'+str(p) for p in Path(name).parents if str(p)!='.')
    ids={g:{s['id'] for s in json.loads((root/'data'/g/'spec.json').read_bytes())['slots']} for g in ('bootstrap','known','selected','daily','final')}
    if sum(map(len,ids.values()))!=17144:raise ValueError('full calendar required')
    result={};seen_dirs=set()
    for current,dirs,files in os.walk(root,followlinks=False):
        for name in dirs:
            p=Path(current)/name;rel=p.relative_to(root).as_posix()
            if not stat.S_ISDIR(p.lstat().st_mode) or rel not in allowed_dirs:raise ValueError('unexpected/nonregular directory '+rel)
            seen_dirs.add(rel)
        for name in files:
            p=Path(current)/name;rel=p.relative_to(root).as_posix();info=p.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_size>32*1024**2:raise ValueError('nonregular/unbounded file '+rel)
            parts=Path(rel).parts
            if parts[0]=='package':
                if '/'.join(parts[1:]) not in package:raise ValueError('extra package member '+rel)
            elif len(parts)==2:
                if parts[1] not in {'selection.json','source-seal.json','worker.lock'}:raise ValueError('extra root data member '+rel)
            elif len(parts)==3 and parts[1] in ids:
                group=parts[1];valid=name in {'lock','spec.json','seal.json'}
                match=re.fullmatch(r'(?:intent|receipt)-([a-z0-9-]+)\.json',name)
                if match:valid=match[1] in ids[group]
                match=re.fullmatch(r'partial-([a-z0-9-]+)-([0-9]{6})\.bin',name)
                if match:valid=match[1] in ids[group] and int(match[2])<64
                valid=valid or re.fullmatch(r'recovery-[0-9]{6}\.json|pending-[0-9a-f]{32}',name) is not None
                if not valid:raise ValueError('extra journal member '+rel)
            else:raise ValueError('extra member '+rel)
            result[rel]={'bytes':info.st_size,'sha256':file_hash(p)}
    if seen_dirs!=allowed_dirs:raise ValueError('missing fixture directory')
    if {n.removeprefix('package/') for n in result if n.startswith('package/')}!=package:raise ValueError('missing package file')
    for name,sha in assignment['package_files'].items():
        if result['package/'+name]['sha256']!=sha:raise ValueError('frozen package hash '+name)
    if result['package/claim.json']['sha256']!=assignment['claim_sha256']:raise ValueError('claim anchor')
    for group,names in ids.items():
        if any('data/'+group+'/'+n not in result for n in ('lock','spec.json')):raise ValueError('missing journal core')
    if (root/'data/source-seal.json').exists():raise ValueError('expected unfinished failed proof fixture')
    if len(result)>1200258 or sum(v['bytes'] for k,v in result.items() if k.startswith('data/'))>2*1024**3:raise ValueError('fixture resource cap')
    return result


ROOT=Path(__file__).resolve().parents[2]
FAILED_SOURCE=Path('/tmp/options-timing-full-episode-kf1jnuy0')
FAILED_ENVELOPE=Path('/tmp/options-timing-envelope-pc318a7n')
REVIEWS=ROOT/'research/strategy-search-2026-09-11/reviews'
EVIDENCE=(
    'options-timing-episode-20260915-guard.json',
    'options-timing-episode-20260915.json.inventory-before.json',
    'options-timing-episode-20260915.json.progress.jsonl',
    'options-timing-episode-20260915.json.attempts.jsonl',
    'options-timing-history-output-envelope-20260915.progress.jsonl',
    'options-timing-history-output-envelope-20260915.guard.json',
)


def collect_inventory():
    values={}
    for name,item in inventory(FAILED_SOURCE).items():
        values['failed-source/'+name]={**item,'original_path':str(FAILED_SOURCE/name)}
    if FAILED_ENVELOPE.is_symlink() or {p.name for p in FAILED_ENVELOPE.iterdir()}!={'books.json','source-report.json'}:raise ValueError('unexpected envelope members')
    for name in ('books.json','source-report.json'):
        p=FAILED_ENVELOPE/name;info=p.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_size>16*1024**2:raise ValueError('envelope regular file/cap')
        values['failed-envelope/'+name]={'bytes':info.st_size,'sha256':file_hash(p),'original_path':str(p)}
    if json.loads((FAILED_ENVELOPE/'source-report.json').read_bytes())!={'synthetic_only':True}:raise ValueError('invented envelope authority')
    if values['failed-envelope/books.json']['sha256']!='43f5870a56b4c46a90fb06c1cb4ee435ee8deb865101edcd0c836b487d84d1a5':raise ValueError('retained failed synthetic book hash')
    for name in EVIDENCE:
        p=REVIEWS/name;info=p.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_size>8*1024**2:raise ValueError('evidence regular file/cap')
        values['retained-evidence/'+name]={'bytes':info.st_size,'sha256':file_hash(p),'original_path':str(p)}
    return values


def main(destination):
    destination=Path(destination)
    for p in (destination,*destination.parents):
        if p.is_symlink():raise ValueError('symlink archive destination')
    before=collect_inventory();destination.mkdir(parents=True,exist_ok=True)
    archive=destination/'options-timing-failed-engineering-20260915.tar.gz'
    with archive.open('xb') as output:
        with gzip.GzipFile(filename='',mode='wb',fileobj=output,mtime=0,compresslevel=6) as compressed:
            with tarfile.open(mode='w|',fileobj=compressed,format=tarfile.USTAR_FORMAT) as tar:
                for name,item in sorted(before.items()):
                    entry=tarfile.TarInfo(name);entry.size=item['bytes'];entry.mode=0o600;entry.mtime=0
                    with Path(item['original_path']).open('rb') as raw:tar.addfile(entry,raw)
        output.flush();os.fsync(output.fileno())
    after_archive={}
    with tarfile.open(archive,'r|gz') as tar:
        for member in tar:
            if not member.isfile() or member.name not in before or member.name in after_archive:raise ValueError('archive extra/nonregular/duplicate')
            digest=hashlib.sha256();size=0
            with tar.extractfile(member) as raw:
                for chunk in iter(lambda:raw.read(1024**2),b''):digest.update(chunk);size+=len(chunk)
            after_archive[member.name]={'bytes':size,'sha256':digest.hexdigest(),'original_path':before[member.name]['original_path']}
    if after_archive!=before or collect_inventory()!=before:raise ValueError('source/archive preservation mismatch')
    manifest={'schema_version':1,'scope':'Failed invented engineering preservation only; no real market data or deployment authority. No extraction/execution.',
        'source_roots':{'failed-source':str(FAILED_SOURCE),'failed-envelope':str(FAILED_ENVELOPE),'retained-evidence':str(REVIEWS)},
        'failure_qualifications':{'failed-source':'Compressed full-loop120s timeout; synthetic known/selected raw timestamps overlap. This remains uncorrected original evidence.',
                                'failed-envelope':'Doubled20-history validation envelope hit120s wall limit after publishing invented8book output; no real financial values included.'},
        'member_count':len(before),'total_member_bytes':sum(v['bytes'] for v in before.values()),'members':before,
        'source_preserved':True,'regular_file_members_only':True,'archive_name':archive.name,
        'archive_bytes':archive.stat().st_size,'archive_sha256':file_hash(archive)}
    target=destination/'options-timing-failed-engineering-20260915.members.json'
    with target.open('xb') as out:out.write(encoded(manifest));out.flush();os.fsync(out.fileno())
    fd=os.open(destination,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)
    result={k:v for k,v in manifest.items() if k!='members'}
    result.update(manifest_path=str(target),manifest_bytes=target.stat().st_size,manifest_sha256=file_hash(target))
    report=REVIEWS/'options-timing-failed-engineering-preservation-20260915.json'
    with report.open('xb') as out:out.write(encoded(result));out.flush();os.fsync(out.fileno())
    print(json.dumps(result))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--destination',required=True)
    main(parser.parse_args().destination)
