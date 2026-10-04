from pathlib import Path
import os,stat,json,hashlib
H=Path(__file__).resolve().parent;A=H.with_name('financial-graph-feature-npy-byte-preparation01-2026-10-04');sha=lambda b:hashlib.sha256(b).hexdigest();a=json.loads((H/'AUTHENTICATION01.json').read_text())
(H/'REPORT01.md').write_text('''# Independent NPY byte-reader review

WITHHELD_NPY_CURRENTNESS_01 confirmed. The complete187-member author manifest and all retained failures are authenticated. Fresh check03/check04 pass120 assertions: exact pinned installed NumPy _wrap_header AST/golden bytes for versions1/2/3, restricted little-endian float32/C-order/positive Nx32 grammar, literal header and full/raw hashes, finite extent, ordering, EOF, mutable expected metadata, original cursor cleanup, refusal paths and nine first-fatal close pairs. NumPy and all numerical/project authority modules were not imported. Byte headers were generated through isolated stdlib AST, not scientific arrays.

All12 existing final-verifier-close cases were independently joined to actual retained files. Every current whole-file hash differs from its original expected hash. In exactly5 accepted cases the complete actual recorded before/after fingerprints coincide; all7 refused cases differ. Current retained fingerprints match each recorded after state. The source closes the real second/final verification descriptor before changing the payload, uses actual write/flush/fsync, and has no timestamp-reset call. These original cases were authenticated rather than replayed as historical work. This is a concrete proof-currentness defect, not merely a warning about arbitrary future concurrent writes.

The parser implementation and format tests do not resolve that defect. Currentness after all owned cleanup requires a defined proof/resource lifetime and an enforceable writer-exclusion or immutable-byte contract during consumption and closure. Any such contract must cover the actual inode/body, aliases, writers, callbacks, failure/cleanup and release ordering in the genuine execution domain. A proposed token, expected hash or promise of exclusive ownership alone is insufficient. Another identical scan would introduce another final descriptor cleanup and does not resolve the demonstrated premise. No repair or authority redesign was made by this review.

Source339 graph publication writes MCM and edge_index as distinct component arrays; the reviewed NPY subset is only the MCM member. Genuine component manifest/context, dtype float32 to on-disk <f4 mapping, source/graph/node/motif/sample lineage, companion edge_index, original producer/Owner/Run admission, shared storage lease and complete typed recovery remain separate requirements. Caller-supplied eight hashes do not authenticate those relations. The4MiB local file cap does not admit the projected2,309,992,448-byte payload or full financial population.

Cross-utility disposition: bridge03's final population rejoin also uses inode/time/stat fingerprints after a byte proof. This NPY witness demonstrates that equality of those fields cannot in general imply unchanged bytes on the tested filesystem. It does not by itself execute or falsify the distinct bridge03 path. Bridge adoption/currentness must remain on hold pending an explicit exact-domain review and genuine lifetime/writer-exclusion evidence; its earlier narrow acceptance of forced-different-timestamp witnesses is not a byte-immutability theorem. Metadata-only lease accounting remains a different claim.

The review's first authentication harness failed because it assumed every non-file member was a directory. The retained literal symlink is valid evidence; authenticate02 handles its original type and target. Both scripts and outputs remain. No author source/evidence, live source, gate, registration, claim, numerical input, network, upload or deletion was changed. No capacity, scientific representation, production or release authority follows.
''')
m={'schema_version':1,'decision':'WITHHELD_NPY_CURRENTNESS_01','source_sha256':sha((A/'npy_bytes02.py').read_bytes()),'authentication_checks':a['count'],'fresh_format_cleanup_assertions':120,'retained_cases':12,'accepted_changed_bytes_equal_fingerprint':5,'refused_changed_fingerprint':7,'direct_bridge_failure_proved':False,'bridge_adoption_requires_exact_domain_review':True,'numeric_imports':False,'genuine_handles':False,'report_sha256':sha((H/'REPORT01.md').read_bytes())};(H/'MACHINE01.json').write_text(json.dumps(m,indent=2)+'\n')
rows=[]
for p in sorted(H.rglob('*')):
 if p==H/'MANIFEST01.json':continue
 s=p.lstat();r={'path':str(p.relative_to(H)),'mode':oct(stat.S_IMODE(s.st_mode))}
 if stat.S_ISREG(s.st_mode):b=p.read_bytes();r.update(kind='file',bytes=len(b),sha256=sha(b))
 elif stat.S_ISDIR(s.st_mode):r.update(kind='directory')
 else:r.update(kind='symlink',target=os.readlink(p))
 rows.append(r)
(H/'MANIFEST01.json').write_text(json.dumps({'schema_version':1,'members':rows},sort_keys=True,indent=2)+'\n');print(json.dumps({'manifest':sha((H/'MANIFEST01.json').read_bytes()),'machine':sha((H/'MACHINE01.json').read_bytes()),'report':sha((H/'REPORT01.md').read_bytes()),'members':len(rows),'auth':a['count']}))
