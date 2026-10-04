from pathlib import Path
import ast,hashlib,json,os,stat,sys
P=Path(__file__).resolve().parent
canon=lambda v:json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
sha=lambda b:hashlib.sha256(b).hexdigest()
def put(name,v):
 with (P/name).open('xb') as f:f.write(canon(v))
pins=json.loads((P/'SOURCE_PINS03.json').read_bytes());originals=P/'source-evidence';originals.mkdir()
for row in pins['sources']:
 p=Path(row['path']);raw=p.read_bytes();assert sha(raw)==row['sha256']
 if p.name in ('component_store.py','compact_graph_artifacts.py','compact_features.py','compact_owner.py'):
  (originals/p.name).write_bytes(raw)
# Exact source inverse records original attempted implementation and successor.
a=(P/'npy_bytes01.py').read_text();b=(P/'npy_bytes02.py').read_text()
oldtree=ast.parse(a);newtree=ast.parse(b)
changes=[]
for item in oldtree.body:
 name=getattr(item,'name',None)
 if not name:continue
 other=next(x for x in newtree.body if getattr(x,'name',None)==name)
 if ast.dump(item,include_attributes=False)!=ast.dump(other,include_attributes=False):changes.append(name)
assert changes==['Cursor']
put('INVERSE01.json',{'changed_definitions':changes,'source01_sha256':sha(a.encode()),'source02_sha256':sha(b.encode()),'scope':'Added post-original-cursor-cleanup bounded full byte recheck; original remains retained. Final verification cleanup still has the demonstrated sub-tick currentness defect.'})
put('DRAFT_ROLE01.json',{'schema_version':1,'status':'REFUSED_UNADMITTED_DRAFT','source339_supported':False,'genuine_grant':None,'registered_npy_role':None,'target_owner_binding':None,'ordered_nodes_dictionary_sample_source_join':None,'shared_storage_lease':None,'typed_transport_recovery':None,'retirement_authority':None,'native_capacity':None,'current_file_cap':4194304,'current_disk_floor':10737418240,'projected_payload_bytes':2309992448,'projected_rows':2309992448//128,'member':'array-000000.npy','companion_edge_index_covered':False,'raw_payload_is_not_whole_npy':True})
put('MACHINE01.json',{'schema_version':1,'decision':'WITHHELD_NPY_CURRENTNESS_01','source_sha256':sha(b.encode()),'predecessor_sha256':sha(a.encode()),'ordinary_controls':120,'boundary_cases':12,'accepted_corrupted_after_final_close':5,'refused_after_final_close':7,'witness_sha256':sha((P/'SAMPLED_BOUNDARY01.json').read_bytes()),'source339_unchanged':True,'numerical_imports':False,'genuine_authority':False,'production_available':False,'capacity_proved':False,'scope':'Concrete restricted NPY parser/aligned opaque cursor preparation with exact unresolved final-cleanup timestamp-collision defect; independent review required.'})
report='''# Opaque graph MCM NPY preparation — withheld

Concrete stdlib implementation is retained in `npy_bytes02.py`; original `npy_bytes01.py` and all attempted harnesses remain unchanged. The disposition is **WITHHELD_NPY_CURRENTNESS_01**. No module was installed, no scientific array was imported or decoded, and no genuine Graph/Owner/Run/Binding was constructed.

## Implemented byte format

The parser accepts the pinned NumPy writer's plain NPY 1.0, 2.0 and 3.0 envelopes, ASCII `<f4`, C order, positive `(N, 32)` dimensions, complete 64-byte header alignment, exact three-key restricted grammar with arbitrary key order, and space padding plus final newline. It does not evaluate Python expressions. It preserves the literal magic/version/length/header/padding/newline bytes and binds their hash, payload offset, raw payload hash and whole-file hash. Header extent is at most 4096 bytes. UTF-8 structured fields, arbitrary NPY dtypes, object/pickle payloads, zero dimensions, historical 16-only alignment and general Fortran arrays are intentionally outside this supported subset.

The single-use cursor uses real nofollow read descriptors, canonical path/current inode fingerprints, strict immutable canonical expected metadata, four-byte alignment, sequential offsets, bounded 1 MiB reads, exact EOF and terminal failure. Actual reads remain subject to the existing 4 MiB file cap, sampled 10 GiB free-space floor and 120-second deadline. The timer cannot interrupt a blocking system call. No file reservation, scratch recycling, network sink or retirement exists. The metadata-only projected 2,309,992,448-byte payload is 18,046,816 rows and requires an additional literal NPY header; it is not locally admitted. The function `production()` always refuses.

## Actual scientific seam (source text only)

The frozen Source339 root is the isolated claimedrun source at commit `0a2e7639b42b9423b90743feadcda4078aa21816`. `compact_graph_artifacts._payload` preserves both MCM and edge_index NumPy views. `_template` calculates the NumPy v1 header and array extent; `publish` validates real Features, Owner transition and leases, registered output policy, full source/producer/context and retained resource bounds, then calls `component_store.save_component`. That writer uses `np.save(..., allow_pickle=False)` and fsync, with MCM first as `array-000000.npy` and edge_index second. Existing Component ArrayReference subsequently verifies whole member hash/extent, dtype and shape through genuine numerical APIs. This preparation never calls those APIs and does not replace their ownership or context checks.

Eight expected hashes name source, whole component manifest, context, ordered nodes, dictionary, sample, feature receipt and graph. They are opaque caller assertions, not proof that those scientific objects agree. The component manifest's original dtype string `float32` must be explicitly joined to on-disk descriptor `<f4` by a future genuine adapter. The edge_index companion, full component tree/context, native producer, registered source counts/gate, genuine shared lease, typed complete recovery and actual capacity remain unresolved. Existing codec and bridge sources are untouched and this NPY role is unsupported by Source339.

## Verification and retained findings

Fresh check03 passes 105 checks, including exact header comparison with AST-isolated `_wrap_header` from the pinned installed NumPy source, all three versions, ordered opaque cursor reconstruction, header/key/type/shape/byte-order/padding refusals, strict expected fields, short reads, replay, truncation, surplus and corruption, mutable expected dictionary, real cursor-close corruption, and nine actual first-primary/close exception pairs. Check04 passes 15 further cleanup/mode/path/hash/deadline/floor/extent checks. No NumPy/Torch/SciPy import occurred. All fixtures are opaque literal bytes; no float values or labels were decoded.

Check01 stopped on an author's 17-byte fixture string mistakenly counted as 16; check02 corrected that fixture and exposed actual same-extent post-cursor-close corruption acceptance. These original scripts, traces and partial files remain. A separately retained witness01 refused with changed timestamps. Successor02 adds a full bounded reread after original cursor descriptor cleanup, fixing the first-close witness. It does not establish final cleanup safety.

`sampled_boundary01.py` closes the actual final verification descriptor, then changes the first payload byte through an actual owned file write. Five of twelve fresh cases return a proof even though the independent whole-file hash changed; creation and rewrite fingerprints are identical within the filesystem's effective timestamp granularity. Seven refuse when fingerprints advance. No arbitrary timestamp reset, fabricated descriptor, numerical handle or concurrent timing race was used. Check04's forced mtime advance is separately labeled and does not supersede this counterexample. A second identical verification loop merely moves the vulnerable final cleanup boundary. The implementation therefore cannot be accepted as proving current unchanged bytes after all owned cleanup. A separate design must resolve the resource/proof lifetime or establish a genuine writer-exclusion contract; continuous filesystem immunity is not demanded or claimed.

All copied original scientific source bodies and runtime-source hashes are retained for review. Python runtime pin and actual NumPy source path/hash are in SOURCE_PINS03. Local source copies and this manifest are not an external recoverable backup, production authorization or numerical claim.
'''
(P/'REPORT01.md').write_text(report)
rows=[]
for p in [P]+sorted(P.rglob('*')):
 if p.name=='MANIFEST01.json':continue
 s=p.lstat();row={'path':'.' if p==P else p.relative_to(P).as_posix(),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISDIR(s.st_mode):row['kind']='directory'
 elif stat.S_ISREG(s.st_mode):row.update(kind='file',bytes=s.st_size,sha256=sha(p.read_bytes()))
 elif stat.S_ISLNK(s.st_mode):row.update(kind='symlink',target=os.readlink(p))
 else:raise ValueError('unsupported owned type')
 rows.append(row)
put('MANIFEST01.json',{'schema_version':1,'self_excluded':True,'members':rows})
print(json.dumps({'manifest_sha256':sha((P/'MANIFEST01.json').read_bytes()),'source_sha256':sha(b.encode()),'machine_sha256':sha((P/'MACHINE01.json').read_bytes()),'members':len(rows)}))
