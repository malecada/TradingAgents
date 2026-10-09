"""Ordinary Git storage maintenance, retaining every loose/packed object."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path.cwd().resolve()
HERE=Path(__file__).resolve().parent

def inventory():
    raw=subprocess.check_output(['git','cat-file','--batch-all-objects',
        '--batch-check=%(objectname) %(objecttype) %(objectsize)'],cwd=ROOT)
    if len(raw)>32*1024**2:raise ValueError('bounded Git object metadata inventory exceeded')
    rows=sorted(raw.splitlines())
    if any(len(row.split())!=3 for row in rows):raise ValueError('invalid Git object metadata')
    body=b'\n'.join(rows)+b'\n'
    return {'objects':len(rows),'metadata_bytes':len(body),
            'metadata_sha256':hashlib.sha256(body).hexdigest()}

def save(name,value):
    with (HERE/name).open('x') as out:
        json.dump(value,out,sort_keys=True,indent=2);out.write('\n')

head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
refs=subprocess.check_output(['git','show-ref'],cwd=ROOT)
before=inventory()
save('GIT_COMPACTION_BEFORE01.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'head':head,'refs_sha256':hashlib.sha256(refs).hexdigest(),'inventory':before,
    'free_disk_bytes':shutil.disk_usage(ROOT).free,
    'qualification':'Metadata-only inventory of every loose/packed Git object, including unreachable objects. No research stores or object payloads decoded.'})
with (HERE/'GIT_COMPACTION01.stdout').open('xb') as out, (HERE/'GIT_COMPACTION01.stderr').open('xb') as err:
    result=subprocess.run(['git','repack','-a','-d','--keep-unreachable',
        '--threads=2','--window-memory=67108864'],cwd=ROOT,stdout=out,stderr=err)
after=inventory()
unchanged=(before==after and refs==subprocess.check_output(['git','show-ref'],cwd=ROOT)
    and head==subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
save('GIT_COMPACTION_AFTER01.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'actual_child_exit_code':result.returncode,'head':head,'inventory':after,
    'all_object_inventory_and_refs_unchanged':unchanged,'free_disk_bytes':shutil.disk_usage(ROOT).free,
    'qualification':'Standard Git repack retains unreachable objects and checks exact complete object-name/type/size inventory and refs. Research inputs, raw outputs, recovery trees and empirical identities untouched. No empirical/native job or deletion of scientific bodies.'})
if result.returncode or not unchanged:raise ValueError('Git compaction refused or object inventory changed')
print(json.dumps({'status':'GIT_OBJECTS_AND_REFS_PRESERVED',
                 'objects':after['objects'],'free_bytes':shutil.disk_usage(ROOT).free}))
