"""Check SQLite temporary-file candidates inside the actual resource guard."""
import json
import os
from pathlib import Path
import sqlite3

root=Path.cwd()
env={k:os.environ.get(k) for k in ('SQLITE_TMPDIR','TMPDIR')}
db=sqlite3.connect(':memory:')
override=db.execute('PRAGMA temp_store_directory').fetchall()
assert not override, 'unexpected SQLite global temporary-directory override'
paths=list(dict.fromkeys([p for p in env.values() if p]+['/var/tmp','/usr/tmp','/tmp',str(root)]))
candidates=[]
for value in paths:
    p=Path(value).resolve()
    exists=p.is_dir()
    writable=exists and os.access(p,os.W_OK|os.X_OK)
    candidates.append({'path':value,'resolved':str(p),'exists':exists,'writable':writable,
                       'device':p.stat().st_dev if exists else None})
assert all(c['device']==root.stat().st_dev for c in candidates if c['writable'])
value={'environment':env,'pragma_temp_store_directory':override,'sqlite_version':sqlite3.sqlite_version,
       'workspace_device':root.stat().st_dev,'candidates':candidates,'all_writable_candidates_on_guarded_volume':True,
       'reference':'https://www.sqlite.org/tempfiles.html#temporary_file_storage_locations',
       'scope':'Observed service environment and built-in Unix VFS directory candidates; repeat fresh before empirical launch; no empirical database opened.'}
print(json.dumps(value,indent=2))
