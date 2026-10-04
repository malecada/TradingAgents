import ast,hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;MAIN=H.parents[3];F=H.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def write(n,v):(H/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
cap=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
paths=[MAIN/'tradingagents/research/onchain_replication'/n for n in ('score_tail.py','score_batches.py','matching_owner.py','compact_owner.py','workflow_storage.py')]
paths += [cap/'tradingagents/research/onchain_replication'/n for n in ('financial_wrapper_fixture.py','imported_mcm_identity.py')]
paths += [F/'batch-output-produced-f32-adapter-preparation02-2026-10-03'/n for n in ('archive_non_tail.py','selected_non_tail_transport.py','compact_mcm.py')]
paths += [F/'batch-output-transport-context-preparation02-2026-10-03/non_tail_context.py',F/'financial-outcome-chunked-preservation-preparation02-2026-10-04/chunk_archive01.py']
rows=[]
for p in paths:
 b=p.read_bytes();rows.append(dict(path=str(p),bytes=len(b),sha256=sha(b),mode=stat.S_IMODE(p.lstat().st_mode)));ast.parse(b)
copies=[]
for n in ('recovery04.py','owned_io.py','bounded_git01.py'):
 p=F/'held-consumer-final-recovery-preparation04-2026-10-03'/n;b=p.read_bytes();assert b==(H/n).read_bytes();copies.append(dict(source=str(p),copy=n,sha256=sha(b)))
write('SOURCE_READBACK01.json',dict(schema_version=1,read_only_sources=rows,unchanged_copied_dependencies=copies,live_source_modified=False,authority=None))
for p in H.glob('*.py'):ast.parse(p.read_bytes())
write('MACHINE01.json',dict(schema_version=1,decision='SOURCE_CANDIDATE_AWAITING_DIFFERENT_AUTHOR_REVIEW',codec_sha256=sha((H/'codec01.py').read_bytes()),local_store_sha256=sha((H/'local_store01.py').read_bytes()),tests={'RED01':'expected missing implementation','GREEN01':3,'CHECK02':8,'CHECK03':5,'CHECK04':2},full_payload_bytes_measured=False,logical_descriptor_only=9239969792,live_publication='UNAVAILABLE',authority=None,representation_complete=False))
entries=[]
for p in sorted(H.rglob('*')):
 if p==H/'MANIFEST01.json':continue
 s=p.lstat();r={'path':str(p.relative_to(H)),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(p))
 elif stat.S_ISDIR(s.st_mode):r.update(kind='directory')
 else:
  b=p.read_bytes();r.update(kind='file',bytes=len(b),sha256=sha(b))
 entries.append(r)
write('MANIFEST01.json',dict(schema_version=1,members=entries))
print(json.dumps({'members':len(entries),'files':sum(r['kind']=='file' for r in entries),'codec':sha((H/'codec01.py').read_bytes()),'local':sha((H/'local_store01.py').read_bytes()),'manifest':sha((H/'MANIFEST01.json').read_bytes()),'machine':sha((H/'MACHINE01.json').read_bytes())}))
