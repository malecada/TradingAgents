"""Fingerprint a dedicated interpreter tree without following symlink members."""
import hashlib
import json
import os
from pathlib import Path
import ssl
import stat
import sys

root=Path(sys.argv[1]);rows=[]
for current,dirs,names in os.walk(root,followlinks=False):
    for name in sorted(dirs+names):
        path=Path(current)/name;info=path.lstat();rel=path.relative_to(root).as_posix()
        if stat.S_ISLNK(info.st_mode):rows.append([rel,'symlink',os.readlink(path)])
        elif stat.S_ISDIR(info.st_mode):rows.append([rel,'directory'])
        elif stat.S_ISREG(info.st_mode):
            h=hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda:stream.read(1024**2),b''):h.update(chunk)
            rows.append([rel,'file',info.st_size,h.hexdigest()])
        else:raise ValueError('unexpected runtime member')
rows.sort();raw=json.dumps(rows,separators=(',',':')).encode()
assert sys.version_info[:3]==(3,13,13) and sys.flags.isolated and sys.dont_write_bytecode
print(json.dumps({'inventory_sha256':hashlib.sha256(raw).hexdigest(),'members':len(rows),'python':sys.version.split()[0],'openssl':ssl.OPENSSL_VERSION,'isolated':sys.flags.isolated,'bytecode_writes':not sys.dont_write_bytecode},sort_keys=True))
