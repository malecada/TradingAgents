import hashlib,json,os,stat,subprocess
from pathlib import Path
M=Path.cwd();B=M/'research/onchain-paper-replication-2026-09-24/full_sources';H='712fee46e11dece8138ab08778a1f9819a10cad3';D=B/'financial-genuine-wrapper-root-recordfix-final-remote01-2026-10-04';C=B/'heartbeat-root-checkpoint10-2026-10-04'
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==H
assert not (D/'SELECTED_BODIES01.json').exists() and not (D/'INTENT01.json').exists()
paths=[]
S=B/'financial-genuine-wrapper-root-recordfix-capture01-2026-10-04'
paths.extend(S/n for n in ['source.tar.gz','source-manifest.json','source-authentication.json','terminal.json','request.json','ACTUAL_TERMINAL02.json'])
for name in ['financial-genuine-wrapper-root-recordfix-final-union01-2026-10-04','financial-genuine-wrapper-root-recordfix-final-review-snapshot01-2026-10-04','financial-genuine-wrapper-recordfix-final-union-recovery-preparation01-2026-10-04','financial-genuine-wrapper-recordfix-final-union-recovery-review01-2026-10-04','financial-genuine-wrapper-root-recordfix-final-remote01-2026-10-04']:
 tree=B/name
 for root,dirs,files in os.walk(tree,followlinks=False):
  dirs[:]=[n for n in dirs if n not in ('union-bytes01','__pycache__')]
  assert not any((Path(root)/n).is_symlink() for n in dirs)
  paths.extend(Path(root)/n for n in files)
R=B/'financial-genuine-wrapper-recordfix-actual-recovery-review01-2026-10-04'
paths.extend(R/n for n in ['FLAT_READBACK02.json','MANIFEST02.json','MANIFEST01.json','REMOTE_READBACK01.json'])
paths.extend(C/n for n in ['READ_ONLY_OBSERVATION05.json','TOP17.json','COMMIT_CHECK15.json'])
rows=[]
for p in sorted(set(paths)):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2
 name=p.relative_to(M).as_posix();raw=p.read_bytes();actual=subprocess.check_output(['git','show',H+':'+name]);assert actual==raw
 rows.append({'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
assert len(rows)<=506 and sum(r['bytes'] for r in rows)<=64*1024**2
selection={'remote_commit':H,'rows':rows};body=(json.dumps(selection,sort_keys=True,indent=2)+'\n').encode();(D/'SELECTED_BODIES01.json').write_bytes(body)
tree=subprocess.check_output(['git','ls-tree','-r','-z',H,'--',*[r['path'] for r in rows]]);oids=[]
for line in tree.split(b'\0')[:-1]:
 left,name=line.split(b'\t',1);mode,kind,oid=left.decode().split();assert mode in ('100644','100755') and kind=='blob';oids.append(oid)
assert len(oids)==len(rows)
record={'schema_version':1,'selection_sha256':hashlib.sha256(body).hexdigest(),'remote_commit':H,'selected_count':len(rows),'logical_bytes':sum(r['bytes'] for r in rows),'unique_git_objects':len(set(oids)),'expected_git_operations':11+2*len(rows),'scope':'Complete Source325 original capture plus complete final caller11-tree ordinary union and whole capture-review opaque snapshot preserving all ten lexical links, full adapter/source-review bodies, actual Source recovery metadata and committed Root checkpoint. Negative links never followed/extracted.','excluded':'Installed runtime bodies, empirical stores, POSIX instantiation, numerical authority; postcommit selection construction and later operation records are separate local records.','native_or_network_started':False}
(D/'SELECTION_READBACK01.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n');(D/'SELECTION_BUILDER01.py').write_bytes(Path(__file__).read_bytes())
(C/'REMOTE_CONFIRMATION14.json').write_text(json.dumps({'actual_main_commit':H,'actual_remote_head':H,'actual_push_session':31145,'actual_push_start_tool':'684600','actual_push_completion_tool':'88f4ed','actual_push_exit':0,'actual_remote_readback_session':41380,'actual_remote_readback_start_tool':'fa8b88','actual_remote_readback_completion_tool':'40dfb2','actual_remote_readback_exit':0,'qualification':'Committed availability confirmed; not actual final union fresh byte recovery.'},sort_keys=True,indent=2)+'\n')
print(json.dumps(record))
