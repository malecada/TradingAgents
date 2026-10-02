"""Preserve a compact exact reconstruction of an existing immutable source copy."""
import hashlib,json,subprocess,sys
from pathlib import Path
base=Path(__file__).resolve().parent;root=Path.cwd();name=sys.argv[1]
manifest=base/(name+'-manifest.json');raw=manifest.read_bytes();record=json.loads(raw)
commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
entries={}
for line in subprocess.check_output(['git','ls-tree','-r',commit],text=True).splitlines():
 metadata,path=line.split('\t',1);entries[path]=metadata.split()[2]
target=base/(name+'-delta');target.mkdir()
files={}
for relative,item in record['files'].items():
 data=(Path(record['source'])/relative).read_bytes();assert hashlib.sha256(data).hexdigest()==item['sha256']
 blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
 changed=entries.get(relative)!=blob
 if changed:
  path=target/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
 files[relative]=item|{'from':'delta' if changed else 'base_commit'}
result={'schema_version':1,'purpose':'exact source reconstruction only; no execution authorization',
 'base_commit':commit,'original_manifest_sha256':hashlib.sha256(raw).hexdigest(),'files':files}
(base/(name+'-replay.json')).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(name,commit,sum(x['from']=='delta' for x in files.values()),'changed files; full snapshot retained')
