"""One fixed source delivery; writes this owned package only, never installs."""
from pathlib import Path
import hashlib,json,difflib
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3];F=HERE.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def emit(name,value):
 p=HERE/name
 assert not p.exists(),p
 p.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
parents={
 'durability':('real-data-pilot-chunk-durability-candidate01-2026-10-06','3247ff77ac2f8bb52240ea873c88027f83b3346fa450e28cf137c9c5a7028439'),
 'history':('real-data-pilot-control-history-candidate01-2026-10-06','00f9eb91ea6d1e3f55eedb4e4a64aa2dbc3b4b55d07a83e84503533c30ba0141'),
 'policy':('real-data-pilot-feature-policy-successor-preparation01-2026-10-06','2ac7c7a32f82630ecc1bdc0367e55548eab7636d55a2ec3add3ab0ce62e69bc3'),
 'progress':('real-data-pilot-buffered-progress-correction02-2026-10-06','4feb8af007638fe9dc7affb678e41fc2544e146c1c5ba642550dc9d9d84f5032'),
 'legacy':('real-data-pilot-june13-protected-reuse-handoff01-2026-10-06','21dcd4d42d452c360c3bb5ec6243095d92433521253045276179bdb393a67fe5')}
records={};sources=[]
for key,(directory,pin) in parents.items():
 p=F/directory;m=p/'MANIFEST01.json';assert sha(m.read_bytes())==pin
 body=json.loads(m.read_bytes());members=body.get('members',body.get('files',body))
 records[key]={'manifest':str(m.relative_to(ROOT)),'sha256':pin}
 names=sorted((p/'candidate').glob('*.py')) if key in ('durability','history','legacy') else [p/('successor01.py' if key=='policy' else 'real_pilot_partial_progress.py')]
 for s in names:
  rel=str(s.relative_to(p));expected=members[rel];expected=expected['sha256'] if isinstance(expected,dict) else expected
  raw=s.read_bytes();assert sha(raw)==expected
  destination=HERE/('successor01.py' if key=='policy' else 'candidate/'+s.name)
  destination.parent.mkdir(exist_ok=True);assert not destination.exists();destination.write_bytes(raw)
  main='tradingagents/research/onchain_replication/'+s.name
  runtime=key!='policy' and s.name not in ('controls01.py','build_inputs03.py')
  baseline=ROOT/main
  sources.append({'candidate':str(destination.relative_to(ROOT)),'accepted_parent':str(s.relative_to(ROOT)),
   'sha256':expected,'bytes':len(raw),'kind':'runtime' if runtime else 'metadata-preparer',
   'root_install_path':main if runtime else None,
   'before_sha256':sha(baseline.read_bytes()) if runtime and baseline.exists() else None})
assert len(sources)==17 and len({x['candidate'] for x in sources})==17
olddeps=F/parents['policy'][0]/'DEPENDENCIES01.json';deps=json.loads(olddeps.read_bytes())
(HERE/'DEPENDENCIES_BEFORE01.json').write_bytes(olddeps.read_bytes())
for key in ('history','builder','controls','durability'):
 name=Path(deps[key]['path']).name
 deps[key]['path']=str((HERE/'candidate'/name).relative_to(ROOT))
 assert sha((ROOT/deps[key]['path']).read_bytes())==deps[key]['sha256']
emit('DEPENDENCIES01.json',deps)
emit('PARENTS01.json',records)
emit('INSTALL_MAP01.json',{'status':'SOURCE_CANDIDATE_NOT_INSTALLED','runtime_bodies':14,'metadata_bodies':3,'same_file_merge_count':0,'sources':sources})
patch=''
for x in sources:
 if x['kind']!='runtime':continue
 old=(ROOT/x['root_install_path']).read_text() if x['before_sha256'] else ''
 new=(ROOT/x['candidate']).read_text()
 patch+=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=x['root_install_path'] if old else '/dev/null',tofile=x['root_install_path']))
(HERE/'integration01.patch').write_text(patch)
unchanged={}
for name in ('model.py','real_pilot_training.py','score_batches.py','typed_tail_binding.py','typed_score_store.py','mcm_raw_parts.py','compact_mcm_output.py','compact_mcm_publication.py','imported_authority_lease.py','original_import_stage.py','resource_binding.py','population_assembly.py','evaluation.py','job_payload.py','graph_legacy_coverage.py'):
 p=ROOT/'tradingagents/research/onchain_replication'/name
 unchanged[str(p.relative_to(ROOT))]=sha(p.read_bytes())
emit('UNCHANGED_SOURCE01.json',unchanged)
print(json.dumps({'runtime':14,'metadata':3,'same_file_merges':0,'dependency_path_rebinds':4}))
