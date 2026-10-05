import json,stat,os
from pathlib import Path
import recovery_pax01 as R
from cohort01 import VerifiedCohort

def restore_archives(q,selected,output,boundary,return_cohort=False):
 """Root-authenticated finite archive population; no origin authority inferred."""
 results={};manifests={};cohort=VerifiedCohort()
 R.require(all(not os.path.lexists(output/('flat-'+b['name'])) for b in q['bundles']),'all output scopes fresh')
 for b in q['bundles']:
  boundary();raw=R.read(selected,b['manifest']['path']);R.require(R.digest(raw)==b['manifest']['sha256'] and len(raw)==b['manifest']['bytes'],'selected manifest pin');m=json.loads(raw);R.validate(m);manifests[b['name']]=m
  archive=R.read(selected,b['archive']['path']);R.require(R.digest(archive)==b['archive']['sha256'] and len(archive)==b['archive']['bytes'],'selected archive pin')
  destination=output/('flat-'+b['name']);destination.mkdir(mode=0o700);R.require(destination.resolve()==destination and stat.S_IMODE(destination.stat().st_mode)==0o700,'fresh private scope')
  descriptor={'bytes':len(archive),'sha256':R.digest(archive),'manifest_sha256':R.digest(raw)}
  results[b['name']]=R.restore(selected/b['archive']['path'],descriptor,m,destination);boundary()
 # Complete byte population rejoined after all later-scope cleanup.
 for name,result in results.items():
  boundary();root=output/('flat-'+name);raw=cohort.read(root,result['metadata_file']);R.require(R.digest(raw)==result['metadata_sha256'],'actual mode metadata');meta=json.loads(raw);m=manifests[name];R.require(meta['manifest']==m,'complete original metadata');files={x['path']:x for x in m['members'] if x['kind']=='file'};mapping=meta['flat_members'];R.require(set(mapping)==set(files) and len(set(mapping.values()))==len(files) and set(p.name for p in root.iterdir())==set(mapping.values())|{result['metadata_file']},'full restored population')
  cohort.tree(root,set(mapping.values())|{result['metadata_file']})
  for path,row in files.items():
   raw=cohort.read(root,mapping[path]);R.require(len(raw)==row['bytes'] and R.digest(raw)==row['sha256'],'retained actual body')
  boundary()
 cohort.check()
 return (results,cohort) if return_cohort else results


def input_read(inputs,root,name):
 """Bind an actual read to the existing sampled cohort; no writer exclusion."""
 path=Path(root)/R.path_name(name);before=inputs.pin(path);raw=R.read(root,name)
 R.require(inputs.signature(path)==before,'input changed during verified read cleanup')
 proof=(len(raw),R.digest(raw));R.require(path not in inputs.byte_proofs or inputs.byte_proofs[path]==proof,'input byte proof changed');inputs.byte_proofs[path]=proof
 return raw


