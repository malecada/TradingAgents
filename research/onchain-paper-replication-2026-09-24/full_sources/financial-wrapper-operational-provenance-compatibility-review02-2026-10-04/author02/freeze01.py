import ast,hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;P=H/'predecessor01';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,v):(H/n).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
old=json.loads((P/'MANIFEST01.json').read_text())
for row in old['members']:
 p=P/row['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==row['mode']
 if row['kind']=='file':assert s.st_size==row['bytes'] and sha(p)==row['sha256']
 elif row['kind']=='symlink':assert os.readlink(p)==row['target']
 else:assert stat.S_ISDIR(s.st_mode)
requirements=json.loads((P/'ROOT_REQUIREMENTS01.json').read_text());requirements['source_successor_qualification']='Candidate02 adds exact same-policy/full-target/fixed-parent propagation for prediction; no source/gate/policy/release adoption. Freeze all3 consumer phases on this final195map before the new reference.';requirements['actual_target_source']=None;requirements['actual_policy']=None;requirements['actual_compatibility_review']=None;save('ROOT_REQUIREMENTS02.json',requirements)
source_names=('operational_source_compatibility.py','financial_wrapper_fixture.py','training.py','workflow_storage.py');sources={n:{'bytes':(H/n).stat().st_size,'sha256':sha(H/n)} for n in source_names}
checks=json.loads((H/'CHECKS01.json').read_text());r=json.loads((H/'SOURCE_READBACK01.json').read_text())
report='''# Operational-source policy propagation successor02

Source candidate only; independent review and all Root adoption predicates remain required. The exact independent OPC-PREDICT-POLICY-01 witness is preserved, along with the complete original preparation01, its506 final controls, source bodies, failed harness and typed manifest. No predecessor or actual research evidence was modified.

The wrapper adds one optional-role/predict-only guard after the genuine verified parent claim, actual COMPLETE lifecycle check and unchanged strict scientific provenance comparison, before original checkpoint/member access. The guard requires the completed parent to be the fixed continuation consumer and cell, to carry the identical current registered compatibility-policy SHA256 and identical complete closure-input SHA256, and to contain every exact target implementation path/hash. The original current-policy reader supplies these fields; the passed parent fields come from the original verify_claim route. Pure metadata validation creates no authority object. A changed/missing parent policy, wrong closure, wrong consumer/cell or any changed195-path source body refuses.

The witnessed old comparison is reproduced directly from the original production AST: equal implementation provenance under different commits accepts despite differing policy hashes. Candidate02's added predicate rejects that same differing-policy case. A consistent opaque same-policy case passes only the pure metadata predicate. There was no fabricated real claim, Run, Owner, Admission, COMPLETE receipt or numerical outcome.

The source delta is one wrapper insertion, the consequent exact wrapper hash update in the helper, and two appended helper functions. Exact full literal/AST inverses reconstruct candidate01. All preexisting helper functions, bounded readers, cleanup/fatal behavior and historical-parent predicate remain unchanged. Training6f278 and watcher91e21 are byte-identical. The original strict reference equality, generic checkpoint loader, old provenance, new output provenance and every numerical function remain unchanged. Legacy absent-role behavior is unchanged.

231 focused final controls passed. The two fresh inherited control scripts produced508 rows: all506 predecessor rows plus two inverse checks for the new wrapper substitution. The first combined harness wrongly expected506 after those two extra checks; both underlying script executions had passed. Its failed assertion, progress, raw output and first fresh replay tree are retained, and the corrected second replay is separate. These are author engineering controls, not an independent review or actual runtime execution.

The target map still has195 paths/194 distinct hashes and191 original byte-identical bodies. New helperd0d770 and wrapper5f478 pins update the source-closure/policy/proof drafts; future actual source/design/gate/policy/proof/recovery/consumer fields remain NULL or unavailable as before. The old0a2 checkpoint provenance and all original FAILED identities stay historical. Registered proof labels alone still do not establish independent authorship or external recovery.

Root must freeze and independently review this complete target closure before any replacement COMPLETE100 reference, then preserve/admit the exact policy, all consumer identities, current inputs/source/gate/caller, cumulative allowance and actual recovery/native release. Preclaim dependency validation and actual genuine integration remain unperformed. No numerical imports, checkpoint decoding, claim, network, allowance change, refund, transfer, scientific completion or full-capacity claim occurred.
'''
(H/'REPORT01.md').write_text(report)
machine={'schema_version':1,'status':'FROZEN_SOURCE_SUCCESSOR02_REQUIRES_INDEPENDENT_REVIEW','finding_addressed':'OPC-PREDICT-POLICY-01','predecessor_manifest_sha256':sha(P/'MANIFEST01.json'),'independent_review01_manifest_sha256':sha(H/'independent_finding01/MANIFEST01.json'),'independent_witness01_sha256':sha(H/'independent_finding01/WITNESS01.json'),'sources':sources,'inverse_sha256':sha(H/'SUCCESSOR_INVERSE01.json'),'full_original_inverse_sha256':sha(H/'SOURCE_INVERSES02.json'),'red_green_sha256':sha(H/'RED_GREEN01.json'),'new_controls':checks['new_controls'],'replayed_controls':checks['inherited_final_controls'],'inherited_original_rows':506,'additional_new_wrapper_inverse_rows':2,'source_footprint':{'original_paths':194,'original_distinct_hashes':193,'target_paths':len(r['target_map']),'target_distinct_hashes':len(set(r['target_map'].values())),'original_byte_identical_paths':191},'source_adopted':False,'policy_adopted':False,'actual_target_source':None,'actual_independent_review':None,'actual_recovery':None,'actual_native_release':None,'genuine_runtime_objects_constructed':False,'numerical_packages_imported':False,'checkpoint_deserialized':False,'preserved_harness_failure':'CHECK01.err: stale506 expectation after new inverse added2 rows; no implementation failure inferred. First and second replay trees retained.'}
save('MACHINE01.json',machine)
rows=[]
for root,dirs,files in os.walk(H,followlinks=False):
 for n in dirs+files:
  p=Path(root)/n;s=p.lstat();row={'path':str(p.relative_to(H)),'mode':stat.S_IMODE(s.st_mode)}
  if stat.S_ISLNK(s.st_mode):row.update(kind='symlink',target=os.readlink(p))
  elif stat.S_ISDIR(s.st_mode):row.update(kind='directory')
  elif stat.S_ISREG(s.st_mode):assert s.st_size<=4194304;row.update(kind='file',bytes=s.st_size,sha256=sha(p))
  else:raise ValueError(row)
  rows.append(row)
rows.sort(key=lambda x:x['path']);save('MANIFEST01.json',{'schema_version':1,'scope':'complete successor preparation excluding this self manifest','members':rows,'typed_members':len(rows),'regular_files':sum(x['kind']=='file' for x in rows),'regular_bytes':sum(x.get('bytes',0) for x in rows),'status':'SOURCE_ONLY_NOT_INSTALLED'})
print(json.dumps({'manifest':sha(H/'MANIFEST01.json'),'machine':sha(H/'MACHINE01.json'),'report':sha(H/'REPORT01.md'),'sources':sources,'typed_members':len(rows),'regular_bytes':sum(x.get('bytes',0) for x in rows)}))
