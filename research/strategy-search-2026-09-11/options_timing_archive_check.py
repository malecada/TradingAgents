"""Archive only a sealed invented fixture; no execution, market I/O or extraction."""
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
        if any('data/'+group+'/receipt-'+n+'.json' not in result for n in names):raise ValueError('missing receipt')
        if any('data/'+group+'/'+n not in result for n in ('lock','spec.json','seal.json')):raise ValueError('missing journal core')
    source=json.loads((root/'data/source-seal.json').read_bytes())
    if source['status']!='complete' or source['intended_slot_count']!=17144:raise ValueError('complete synthetic source seal required')
    if source['assignment_sha256']!=result['package/assignment.json']['sha256']:raise ValueError('source assignment anchor')
    if len(result)>1200258 or sum(v['bytes'] for k,v in result.items() if k.startswith('data/'))>2*1024**3:raise ValueError('fixture resource cap')
    return result


def main(root,destination):
    root=Path(root);destination=Path(destination)
    if root.is_symlink():raise ValueError('symlink fixture root')
    before=inventory(root)
    destination.mkdir(parents=True,exist_ok=True)
    archive=destination/'options-timing-synthetic-20260915.tar.gz'
    with archive.open('xb') as output:
        with gzip.GzipFile(filename='',mode='wb',fileobj=output,mtime=0,compresslevel=6) as compressed:
            with tarfile.open(mode='w|',fileobj=compressed,format=tarfile.USTAR_FORMAT) as tar:
                for name,item in sorted(before.items()):
                    entry=tarfile.TarInfo(name);entry.size=item['bytes'];entry.mode=0o600;entry.mtime=0
                    with (root/name).open('rb') as raw:tar.addfile(entry,raw)
        output.flush();os.fsync(output.fileno())
    # Stream verification rejects links, directories, duplicate/extra members and
    # content changes. Nothing is extracted or executed.
    archive_inventory={}
    with tarfile.open(archive,'r|gz') as tar:
        for member in tar:
            if not member.isfile() or member.name not in before or member.name in archive_inventory:raise ValueError('nonregular/extra/duplicate archive member')
            digest=hashlib.sha256();count=0
            with tar.extractfile(member) as raw:
                for chunk in iter(lambda:raw.read(1024**2),b''):digest.update(chunk);count+=len(chunk)
            archive_inventory[member.name]={'bytes':count,'sha256':digest.hexdigest()}
    if archive_inventory!=before or inventory(root)!=before:raise ValueError('source/archive preservation mismatch')
    manifest={'schema_version':1,'scope':'Inert invented engineering fixture only; no real market data, admission or executable launch authority.',
        'source_root':str(root),'source_preserved':True,'regular_file_members_only':True,'member_count':len(before),
        'total_member_bytes':sum(x['bytes'] for x in before.values()),'members':before,
        'assignment_sha256':before['package/assignment.json']['sha256'],'source_seal_sha256':before['data/source-seal.json']['sha256'],
        'archive_name':archive.name,'archive_bytes':archive.stat().st_size,'archive_sha256':file_hash(archive)}
    target=destination/'options-timing-synthetic-20260915.members.json'
    with target.open('xb') as out:out.write(encoded(manifest));out.flush();os.fsync(out.fileno())
    parent=os.open(destination,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(parent)
    finally:os.close(parent)
    print(json.dumps({k:v for k,v in manifest.items() if k!='members'}))
    print(json.dumps({'manifest_path':str(target),'manifest_sha256':file_hash(target)}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--destination',required=True)
    args=parser.parse_args();main(args.source,args.destination)
