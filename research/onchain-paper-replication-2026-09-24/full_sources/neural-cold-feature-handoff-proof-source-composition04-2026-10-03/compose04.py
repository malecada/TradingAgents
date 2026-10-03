from pathlib import Path
import json,hashlib,shutil
B=Path('research/onchain-paper-replication-2026-09-24/full_sources');old=B/'neural-cold-feature-handoff-proof-source-composition03-2026-10-03';new=B/'neural-cold-feature-handoff-proof-source-composition04-2026-10-03';new.mkdir()
sha=lambda b:hashlib.sha256(b).hexdigest();canonical=lambda v:(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
manifest=json.loads((old/'MANIFEST03.json').read_bytes())
for row in manifest['files']:
 p=old/row['path'];assert p.stat().st_size==row['bytes'] and sha(p.read_bytes())==row['sha256']
inv=json.loads((old/'source_inventory03.json').read_bytes());selected=B/'claim-source-git-batch-candidate01-2026-10-03/candidate01.py';assert sha(selected.read_bytes())=='3a45746a388307d1b375c885bb2fd7a22c2a60f139df714d2bbe98906d57d7eb'
for row in inv['source_inventory']:
 src=old/'source-bodies'/row['target'];dest=new/'source-bodies'/row['target'];dest.parent.mkdir(parents=True,exist_ok=True)
 data=src.read_bytes();assert len(data)==row['bytes'] and sha(data)==row['sha256']
 if row['target']=='tradingagents/research/verify.py':
  data=selected.read_bytes();row.update(bytes=len(data),sha256=sha(data),origin=str(selected),snapshot=str(dest),git_commit=None,git_path=None)
 dest.write_bytes(data)
inv['status']='source-only-verify-batch04-unreviewed';inv['logical_bytes']=sum(r['bytes'] for r in inv['source_inventory']);inv['predecessor']={'path':str(old/'source_inventory03.json'),'bytes':(old/'source_inventory03.json').stat().st_size,'sha256':sha((old/'source_inventory03.json').read_bytes())}
(new/'source_inventory04.json').write_text(json.dumps(inv,sort_keys=True,indent=2)+'\n')
helper=(old/'prepare_metadata_composed03.py').read_text().replace('aff7a877446e94a10c75d73f093c643e3e1f90296d86337352cd0f8dfac69379',sha(canonical(inv))).replace('source-only-outer03-unreviewed',inv['status'])
(new/'prepare_metadata_composed04.py').write_text(helper)
for name in ['recipe01.json','configs01.json','model01.json','training01.json']:shutil.copyfile(old/name,new/name)
(new/'origins04.json').write_text(json.dumps({'predecessor_manifest':sha((old/'MANIFEST03.json').read_bytes()),'accepted_candidate_manifest':sha((selected.parent/'MANIFEST01.json').read_bytes()),'accepted_candidate_review':'847f7f8552948ae19a1966d3f6176c8b67bd417924369754ba47600cd56d6c5f','changed_target':'tradingagents/research/verify.py','unchanged_source_bodies':194,'raw_inventory_sha256':sha((new/'source_inventory04.json').read_bytes()),'canonical_inventory_sha256':sha(canonical(inv))},indent=2)+'\n')
