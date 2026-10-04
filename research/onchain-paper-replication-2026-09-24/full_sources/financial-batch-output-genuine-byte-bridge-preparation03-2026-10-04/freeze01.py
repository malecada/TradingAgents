from pathlib import Path
import json,ast,hashlib,stat,os,difflib
H=Path(__file__).resolve().parent;F=H.parent;A=F/'financial-batch-output-genuine-byte-bridge-preparation02-2026-10-04';V=F/'financial-batch-output-genuine-byte-bridge-source-review02-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=0
def ok(v):
 global checks
 assert v;checks+=1
for root,manifest in [(A,'MANIFEST02.json'),(V,'MANIFEST01.json')]:
 rows=json.loads((root/manifest).read_text())['members'];actual=[str(p.relative_to(root)) for p in root.rglob('*') if p!=root/manifest];actual+=['.'] if any(r['path']=='.' for r in rows) else [];ok(sorted(actual)==sorted(r['path'] for r in rows))
 for r in rows:
  p=root/r['path'];s=p.lstat();mode=r['mode'];ok(stat.S_IMODE(s.st_mode)==(int(mode,8) if type(mode)is str else mode))
  if r['kind']=='file':b=p.read_bytes();ok(len(b)==r['bytes'] and sha(b)==r['sha256'])
  elif r['kind']=='directory':ok(stat.S_ISDIR(s.st_mode))
  else:ok(p.is_symlink() and os.readlink(p)==r['target'])
old=(A/'byte_bridge01.py').read_text();new=(H/'byte_bridge01.py').read_text();start=new.index('def _codec_population(');end=new.index('def _encode(',start);helper=new[start:end];back=new[:start]+new[end:];back=back.replace('        codec_before=_codec_population(store,R)\n','').replace("        boundary()\n        require(_codec_population(store,R)==codec_before,'post-verification codec population changed')\n",'');ok(back==old);ok(ast.dump(ast.parse(back))==ast.dump(ast.parse(old)))
for n in ['codec01.py','local_store01.py','recovery04.py','owned_io.py','bounded_git01.py','held_score_consumer.py','completed_f32.py']:ok((H/n).read_bytes()==(A/n).read_bytes())
(H/'INVERSE01.json').write_text(json.dumps({'original_sha256':sha(old.encode()),'successor_sha256':sha(new.encode()),'removed_added_helper':helper,'remove_tail_lines':['codec_before=_codec_population(store,R)',"boundary(); require(_codec_population(store,R)==codec_before,...)"],'complete_byte_AST_inverse':True,'checks':checks},indent=2)+'\n');(H/'INVERSE01.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True))))
(H/'REPORT01.md').write_text('''# BB2 sampled codec population correction

The final byte verifier is bracketed by a complete sorted codec population: every name, device/inode, type/mode/link count, size, nanosecond modification/change time, allocated blocks and block size, plus the owned root signature. The snapshot checks actual descriptor-relative membership and canonical root. After final verifier IO cleanup the original boundary runs, then the complete population must equal its preceding snapshot. BB1 complete byte/proof/descriptor/terminal/raw-hash comparison remains unchanged. All other genuine source/authority/cardinality/grant/reservation checks and exception handling remain byte-equivalent under the exact inverse; five utilities and two consumers are identical.

The actual preceding verifier-cleanup witness was replayed in a new owned directory and still accepts under source02. Source03 exact AST-extracted utility tail refuses the same scheduled mutation. BB1 old acceptance/new refusal and intact success pass, as do fresh opaque pipeline and nine writer/close first-fatal pairs. Six additional population controls cover intact, changed body, missing, extra, mode and inode replacement. Every external original/predecessor remains intact; the population controls deliberately mutate only new owned opaque fixtures. Their retained all_original_bytes_retained flag refers to original evidence preservation, not an assertion that each deliberately changed fixture still contains its starting byte value.

No genuine _encode or ResearchRun/Owner/Binding/Target handle was executed or simulated. boundary in composed utility witnesses denotes only the real LocalStore check; genuine original authority boundaries remain source-inspected. Protection is sampled before and after the final byte verifier, not atomic snapshot or continuous race immunity. No lease, capacity, transport, retirement, scientific publication, numerical admission, conversion, model or live Source339 change is admitted. Source preparation requires different-author review.
''')
m={'schema_version':1,'decision':'SOURCE_ONLY_REVIEW_REQUIRED','source_sha256':sha(new.encode()),'inverse_and_seal_checks':checks,'BB1_retained':True,'BB2_old_red_new_green':True,'genuine_encode_executed':False,'report_sha256':sha((H/'REPORT01.md').read_bytes())};(H/'MACHINE01.json').write_text(json.dumps(m,indent=2)+'\n')
rows=[]
for p in sorted(H.rglob('*')):
 if p==H/'MANIFEST01.json':continue
 s=p.lstat();r={'path':str(p.relative_to(H)),'mode':oct(stat.S_IMODE(s.st_mode))}
 if stat.S_ISREG(s.st_mode):b=p.read_bytes();r.update(kind='file',bytes=len(b),sha256=sha(b))
 elif stat.S_ISDIR(s.st_mode):r.update(kind='directory')
 else:r.update(kind='symlink',target=os.readlink(p))
 rows.append(r)
(H/'MANIFEST01.json').write_text(json.dumps({'schema_version':1,'members':rows},sort_keys=True,indent=2)+'\n');print(json.dumps({'source':m['source_sha256'],'manifest':sha((H/'MANIFEST01.json').read_bytes()),'machine':sha((H/'MACHINE01.json').read_bytes()),'checks':checks,'members':len(rows)}))
