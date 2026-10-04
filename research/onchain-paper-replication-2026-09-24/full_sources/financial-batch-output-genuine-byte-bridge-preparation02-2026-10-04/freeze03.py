from pathlib import Path
import ast,json,hashlib,stat,os,difflib
H=Path(__file__).resolve().parent;F=H.parent;A=F/'financial-batch-output-genuine-byte-bridge-preparation01-2026-10-04';V=F/'financial-batch-output-genuine-byte-bridge-source-review01-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ok(v,n):assert v,n;checks.append(n)
for root in (A,V):
 rows=json.loads((root/'MANIFEST01.json').read_text())['members'];ok(sorted((["."] if any(r['path']=='.' for r in rows) else [])+[str(p.relative_to(root)) for p in root.rglob('*') if p!=root/'MANIFEST01.json'])==sorted(r['path'] for r in rows),'full '+root.name)
 for r in rows:
  p=root/r['path'];s=p.lstat();mode=r['mode'];ok(stat.S_IMODE(s.st_mode)==(int(mode,8) if type(mode)is str else mode),'mode')
  if r['kind']=='file':b=p.read_bytes();ok(len(b)==r['bytes'] and sha(b)==r['sha256'],'body')
  elif r['kind']=='directory':ok(stat.S_ISDIR(s.st_mode),'directory')
  else:ok(p.is_symlink() and os.readlink(p)==r['target'],'link')
old=(A/'byte_bridge01.py').read_text();new=(H/'byte_bridge01.py').read_text();before="published['complete.json']=body;boundary();return result";after="published['complete.json']=body;boundary()\n        final_proof=store.verify(terminal,descriptor)\n        require(final_proof==proof and final_proof['logical_bytes']==done['bytes'] and final_proof['raw_sha256']==done['sha256'],'post-summary complete codec/original byte join')\n        return result";ok(new.count(after)==1 and new.replace(after,before)==old,'full byte inverse');ok(ast.dump(ast.parse(new.replace(after,before)))==ast.dump(ast.parse(old)),'full AST inverse')
for n in ('codec01.py','local_store01.py','recovery04.py','owned_io.py','bounded_git01.py','held_score_consumer.py','completed_f32.py'):
 ok((A/n).read_bytes()==(H/n).read_bytes(),'unchanged '+n)
(H/'INVERSE01.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='original/byte_bridge01.py',tofile='successor/byte_bridge01.py')))
(H/'INVERSE01.json').write_text(json.dumps({'original_sha256':sha(old.encode()),'source_sha256':sha(new.encode()),'replace_successor':after,'with_original':before,'checks':checks,'original_manifest':sha((A/'MANIFEST01.json').read_bytes()),'review_manifest':sha((V/'MANIFEST01.json').read_bytes())},indent=2)+'\n')
(H/'REPORT02.md').write_text('''# BB1 narrow successor

The genuine _encode source now performs a second complete store.verify against its original terminal and descriptor after summary writer cleanup and the final original boundary. The resulting complete proof must equal the earlier proof and cursor's original byte count/hash before return. Any failure enters the unchanged poisoning, retained failed marker and first-fatal cleanup path. All original authority/source/grant/job/512-sample/32-motif/cardinality/format checks remain; both consumer modules and five utilities are byte-identical.

The exact added utility statements were extracted by AST and exercised on new owned opaque codec trees. Original stat-only tail accepts deterministic one-byte corruption during the actual summary descriptor close; the successor tail refuses it; intact bytes pass. This does not execute genuine _encode or impersonate a research handle. The original witness and independent WITHHELD review are preserved and fully authenticated. Fresh inherited opaque pipeline controls and nine real write/close exception pairs pass. A stale inherited check02 comparing an older intermediate _authority draft failed and is retained, rather than changing that historical expectation. Current-source complete byte/AST inverse passes.

Checks are sampled; no continuous path immunity or authority/capacity inference is made. The complete.json filename may remain after a late failure, accompanied by the existing FAILED path; consumers must use actual outcome/byte evidence. No storage lease implementation, scientific conversion, gate, cumulative allowance, live Source339, genuine handle, numerical import, network, retirement or publication was changed. Different-author review and genuine future source/admission/resource/recovery remain required.
''')
out={'schema_version':1,'decision':'SOURCE_PREPARATION_ONLY_REVIEW_REQUIRED','source_sha256':sha(new.encode()),'inverse_checks':len(checks),'BB1_utility_cases':3,'original_review_preserved':True,'genuine_encode_executed':False,'authority':False,'capacity':False,'report_sha256':sha((H/'REPORT02.md').read_bytes())};(H/'MACHINE02.json').write_text(json.dumps(out,indent=2)+'\n')
rows=[]
for p in sorted(H.rglob('*')):
 if p==H/'MANIFEST02.json':continue
 s=p.lstat();r={'path':str(p.relative_to(H)),'mode':oct(stat.S_IMODE(s.st_mode))}
 if stat.S_ISREG(s.st_mode):b=p.read_bytes();r.update(kind='file',bytes=len(b),sha256=sha(b))
 elif stat.S_ISDIR(s.st_mode):r.update(kind='directory')
 else:r.update(kind='symlink',target=os.readlink(p))
 rows.append(r)
(H/'MANIFEST02.json').write_text(json.dumps({'schema_version':1,'members':rows},sort_keys=True,indent=2)+'\n');print(json.dumps({'source':out['source_sha256'],'manifest':sha((H/'MANIFEST02.json').read_bytes()),'machine':sha((H/'MACHINE02.json').read_bytes()),'members':len(rows),'inverse_checks':len(checks)}))
