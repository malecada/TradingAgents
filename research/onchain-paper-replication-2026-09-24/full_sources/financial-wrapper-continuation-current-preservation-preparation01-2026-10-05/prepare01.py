"""One local preparation materialization; only this exclusive directory is writable."""
import json,hashlib,os
from pathlib import Path
import bind01 as B
H=Path(__file__).resolve().parent
result,bodies=B.collect()
out=H/'new-bytes';out.mkdir(mode=0o700)
selected=[]
for index,((root,name),raw) in enumerate(sorted(bodies.items())):
 role='git' if root=='git' else ('capsule' if root==str(B.CAP) else 'parent')
 local=f'new-bytes/{index:03d}-{role}.body';p=H/local
 with B.IO._opened(p,'xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
 mode=None if root=='git' else (B.CAP/name if role=='capsule' else B.PARENT/name).stat().st_mode&0o7777
 selected.append({'role':role,'original_root':root,'original_path':name,'original_mode':mode,'path':local,'bytes':len(raw),'sha256':B.sha(raw),'stored_mode':0o600})
for name,value in [('CURRENT_COMPOSITION01.json',result),('SELECTED_BODIES01.json',{'schema_version':1,'status':'LOCAL_BYTES_ONLY_FUTURE_EXTERNAL_RECOVERY_REQUIRED','bodies':selected,'count':len(selected),'bytes':sum(x['bytes'] for x in selected),'all_originals_retained':True})]:
 with B.IO._opened(H/name,'xb') as stream:stream.write(B.encode(value));stream.flush();os.fsync(stream.fileno())
print(json.dumps({'source':result['source'],'old_capsule_files_reused':result['old_capsule_files_reused'],'current_CAP_typed':len(result['capsule']['members']),'current_CAP_files':sum(r['kind']=='file' for r in result['capsule']['members']),'parent_files':len(result['parent']['members']),'new_Git_objects':len(result['git']['new_objects']),'selected_bodies':len(selected),'selected_bytes':sum(r['bytes'] for r in selected),'read_bytes':result['read_bytes'],'seconds':result['elapsed_seconds']}))
