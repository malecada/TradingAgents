from pathlib import Path
import json,hashlib,stat,os
H=Path(__file__).resolve().parent;A=H.with_name('financial-batch-output-codec-spool-integration-preparation03-2026-10-04');sha=lambda b:hashlib.sha256(b).hexdigest()
files=['AUTHENTICATION03.json','RESULT01.json','IR3_WITNESS01.json','DERIVATIVE01.json','WITNESS01.json','STRICT01.json','FATAL01.json','ADVERSARIAL01.json','INDEPENDENT02.json'];checks=0;pins={}
for n in files:
 b=(H/n).read_bytes();o=json.loads(b);checks+=o.get('count',o.get('checks',0)) if isinstance(o,dict) else len(o);pins[n]=sha(b)
(H/'REPORT01.md').write_text('''# Independent router successor03 review

Accepted as a source-only engineering routing utility. IR3 is corrected: the compact pin now validates complete derived partition slices and exact original spool plans, and the instance retains its original immutable route reference. Checks bracket each external engineering callback. The preserved old witness accepts its changed raw offset; the successor refuses both the malformed pin and public route replacement before recovery.

Complete current source1930, predecessor1710, preceding review1608, original3431 and earlier review1673 typed members were authenticated, together with underlying utility scopes. The complete literal and AST inverse contains only the four declared functions. Six copied utility bodies and their source evidence remain unchanged. No format, cap, scientific method or accounting change was inferred.

A fresh real opaque 95-file, 14-retained-plan pipeline completed. Independent checks compared every recovered body and mode and reconstructed both ordered raw payloads. All nested primitive and derivative mutations, callback-boundary replacement, retained-state and cross-envelope controls refused. Nine actual primary-fatal/secondary-owned-close pairs preserved the first exception and drained descriptors. Original IR1 and IR2 regressions passed.

One independent harness initially expected ValueError/TypeError for production refusal, while the source correctly raises RuntimeError. The failed script and stderr are retained; independent02 adds the actual exception class without changing source or fixtures.

Protection is sampled at implemented boundaries, not continuous race immunity or callback preemption. Original and recovered complete stores remain local and retained; no sliding reuse, retirement or deletion is admitted. The arithmetic 8952 aggregate files/280 retained plans is not an observed full population or capacity result. Source339 does not thereby gain these modules or revised source/gate authority. Genuine Target/Owner/Binding publication, typed external recovery, whole resource capacity and financial admission remain unavailable. No numerical imports, genuine claims, network or live integration occurred.
''')
m={'schema_version':1,'decision':'ACCEPTED_SOURCE_ONLY_ROUTER03','source_sha256':sha((A/'router06.py').read_bytes()),'author_manifest_sha256':sha((A/'MANIFEST01.json').read_bytes()),'checks':checks,'evidence':pins,'IR1_IR2_preserved':True,'IR3_corrected':True,'six_utilities_unchanged':True,'whole_byte_AST_inverse':True,'pipeline_files':95,'retained_plans':14,'production_authority':False,'capacity_observed':False,'report_sha256':sha((H/'REPORT01.md').read_bytes())};(H/'MACHINE01.json').write_text(json.dumps(m,sort_keys=True,indent=2)+'\n')
rows=[]
for p in sorted(H.rglob('*')):
 if p==H/'MANIFEST01.json':continue
 s=p.lstat();r={'path':str(p.relative_to(H)),'mode':oct(stat.S_IMODE(s.st_mode))}
 if stat.S_ISREG(s.st_mode):b=p.read_bytes();r.update(kind='file',bytes=len(b),sha256=sha(b))
 elif stat.S_ISDIR(s.st_mode):r.update(kind='directory')
 elif stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(p))
 else:raise ValueError('unexpected type')
 rows.append(r)
(H/'MANIFEST01.json').write_text(json.dumps({'schema_version':1,'members':rows},sort_keys=True,indent=2)+'\n');print(json.dumps({'checks':checks,'members':len(rows),'files':sum(r['kind']=='file' for r in rows),'manifest':sha((H/'MANIFEST01.json').read_bytes()),'machine':sha((H/'MACHINE01.json').read_bytes()),'report':sha((H/'REPORT01.md').read_bytes())}))
