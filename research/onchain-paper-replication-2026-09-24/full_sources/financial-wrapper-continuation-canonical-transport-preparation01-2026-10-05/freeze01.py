"""Seal this source preparation only; never materialize or execute Root routes."""
import ast,difflib,hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent
T=H.parent/'financial-wrapper-continuation-current-transport-preparation01-2026-10-05'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,v):
 b=(json.dumps(v,sort_keys=True,indent=2)+'\n').encode() if not isinstance(v,str) else v.encode()
 with (H/n).open('xb') as f:f.write(b)
def pin(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':sha(b)}
changes={}
for n in ('outcome01.py','space01.py','bind_entry01.py'):
 old=(T/n).read_text();new=(H/n).read_text();segments=[];rebuilt=[]
 for tag,a,b,c,d in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
  if tag=='equal':rebuilt.append(new[c:d])
  else:segments.append({'old_offset':[a,b],'new_offset':[c,d],'old':old[a:b],'new':new[c:d]});rebuilt.append(old[a:b])
 restored=''.join(rebuilt)
 assert restored==old and ast.dump(ast.parse(restored))==ast.dump(ast.parse(old))
 oldfunc={n.name:ast.dump(n) for n in ast.parse(old).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 newfunc={n.name:ast.dump(n) for n in ast.parse(new).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 changes[n]={'original':pin(T/n),'candidate':pin(H/n),'segments':segments,'full_byte_inverse':True,'full_AST_inverse':True,'unchanged_function_AST':[k for k in oldfunc if newfunc.get(k)==oldfunc[k]],'changed_function_AST':[k for k in oldfunc if newfunc.get(k)!=oldfunc[k]]}
unchanged={}
for n in ('recover.template01.py','caller_remote01.py','caller_flat01.py','cohort01.py','flat_primitives01.py','receipt01.py','restore_bundle01.py','watch01.py','original_tree01.py','utilities/recovery_pax01.py','utilities/owned_io.py','utilities/bounded_git01.py'):
 assert (T/n).read_bytes()==(H/n).read_bytes();unchanged[n]={'original':pin(T/n),'candidate':pin(H/n)}
put('SOURCE_INVERSE01.json',{'schema_version':1,'changes':changes,'unchanged':unchanged,'new_source':pin(H/'bind_capture01.py')})
checks=json.loads((H/'CHECK01.stdout').read_bytes());assert checks['passed']==26
draft={'schema_version':1,'status':'SOURCE_PREPARATION_NOT_RELEASED','source':'d4c81c0961342bfe4c5771aabbef1d46a14cffb8','actual_capture_root':str(H.parent/'financial-wrapper-continuation-canonical-delta-root01-2026-10-05'),'capture_sha256':None,'archive_sha256':None,'manifest_sha256':None,'actual_counts':None,'selection':None,'actual_remote_commit':None,'remote_receipt':None,'flat_receipt':None,'independent_entry_release':None,'numerical_authority':False,'bound_source_root':str(H.parent/'financial-wrapper-continuation-canonical-transport-bound01-2026-10-05'),'receiver_root':str(H.parent/'financial-wrapper-continuation-canonical-remote01-2026-10-05'),'flat_root':str(H.parent/'financial-wrapper-continuation-canonical-flat01-2026-10-05')}
put('BINDING_DRAFT01.json',draft)
put('REPORT01.md','''# Canonical continuation byte transport source preparation

The receiver, callers, PAX, owned I/O, bounded Git, watcher, cohort and flat restoration primitives are copied byte-for-byte from the accepted current transport preparation. The three contextual source files have complete literal and AST inverses. Their changes select the canonical source, fresh receiver/flat namespaces and status strings, and replace the obsolete capture author helper with the actual-pin binder. No scientific or native execution source changes.

`bind_capture01.py` requires the three genuine non-null SHA256 values of Root's actual canonical delta. It checks their bounded bytes, manifest counts, scope and exclusions; then binds only the capture hash in a fresh source bundle. Actual counts, archive identity, remote commit, receipts and independent entry releases are not yet available and remain null. No actual capture, source materialization, receiver or flat entry has run in this preparation. The final input fingerprint check is a finite metadata sample, not writer exclusion or an atomic filesystem guarantee.

Root sequence after the actual capture is independently accepted:

1. Run `bind_capture01.py --capture-sha256 ACTUAL --manifest-sha256 ACTUAL --archive-sha256 ACTUAL --materialize` from this source directory. It creates only the fixed fresh canonical-transport-bound01 source bundle.
2. From that bundle run `bind_entry01.py --commit ACTUAL_PUSHED_COMMIT --phase remote`. The exact three-body canonical selection and generated caller/receiver contract then require independent actual binding and entry release before Root invokes the caller. No entry is invoked by either binder.
3. After the genuine receiver completes, run the same bound `bind_entry01.py --commit SAME_COMMIT --phase flat`; bind its real receipt, selected mode profile and exact inner/outer releases before one fresh flat entry.

The original 818 bodies are not recopied. Accepted full capsule/416 Git ancestry is reused; the actual new two metadata bodies, six Git objects and complete final Parent/proof population belong to the forthcoming capture. Transport utility availability and preservation are separate from the three selected payloads. The unchanged 4 MiB per-body/archive, finite selection/read/watch/time bounds and 10 GiB floor remain. The 192 MiB shared space check is conservative headroom, not a kernel reservation or whole-fit capacity proof.

Validation: 26 focused source/null/refusal checks; 12 unchanged source/template byte joins; full inverse for all three contextual files. Missing actual pins refuse before a Root route can be produced. No fake receipt, successful authority, actual restoration or financial run was used. Future actual binding, independent entry review, Root execution and complete outcome composition remain required. Installed runtime package bytes, POSIX reconstruction, writer exclusion, capacity and numerical authority are excluded. The unrelated optional Parent builder remains withheld and untouched.
''')
machine={'schema_version':1,'decision':'SOURCE_PREPARATION_COMPLETE_PENDING_ACTUAL_BINDING_AND_INDEPENDENT_REVIEW','author':'combined_worker_review','checks_passed':checks['passed'],'unchanged_source_bodies':len(unchanged),'source_inverse':pin(H/'SOURCE_INVERSE01.json'),'source_helpers':{n:pin(H/n) for n in ('outcome01.py','space01.py','bind_entry01.py','bind_capture01.py')},'binding_draft':pin(H/'BINDING_DRAFT01.json'),'report':pin(H/'REPORT01.md'),'actual_capture_available':False,'actual_root_entry':False,'execution_released':False,'numerical_authority':False}
put('MACHINE01.json',machine)
rows=[]
for p in sorted(H.rglob('*')):
 s=p.lstat();row={'path':p.relative_to(H).as_posix(),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISDIR(s.st_mode):row['kind']='directory'
 elif stat.S_ISREG(s.st_mode):
  b=p.read_bytes();assert len(b)<=4*1024**2;row.update(kind='file',bytes=len(b),sha256=sha(b))
 else:raise ValueError('unexpected source member')
 rows.append(row)
put('MANIFEST01.json',{'schema_version':1,'root_mode':stat.S_IMODE(H.stat().st_mode),'members':rows,'scope':'complete source preparation before this self-excluded manifest','numerical_authority':False})
print(json.dumps({n:pin(H/n) for n in ('MANIFEST01.json','MACHINE01.json','outcome01.py','bind_capture01.py','bind_entry01.py')},sort_keys=True))
