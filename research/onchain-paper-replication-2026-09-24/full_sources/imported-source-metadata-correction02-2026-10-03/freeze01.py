"""Freeze metadata02 candidate bodies, preserving all previous evidence."""
import ast,hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];FULL=HERE.parent
def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(path,obj):
    with path.open('x') as stream:json.dump(obj,stream,indent=2,sort_keys=True);stream.write('\n')
def main():
    old=(HERE/'compact_mcm.baseline.py').read_bytes();new=(HERE/'compact_mcm.py').read_bytes()
    assert sha(old)=='ed94415ff1798422d66bb19fc6b7ab72e70afef999101d0fb206e3f65556f93a'
    ast.parse(new);ast.parse((HERE/'test_metadata01.py').read_bytes())
    result=subprocess.run(['diff','-u','--label','baseline/compact_mcm.py','--label','candidate/compact_mcm.py',str(HERE/'compact_mcm.baseline.py'),str(HERE/'compact_mcm.py')],capture_output=True,timeout=10)
    assert result.returncode==1
    with (HERE/'metadata01.patch').open('xb') as stream:stream.write(result.stdout)
    predecessor=FULL/'original-import-fixture-native-preparation03-2026-10-03/source_inventory03.json'
    inventory=json.loads(predecessor.read_bytes());rows=inventory['source_inventory']
    assert len(rows)==153
    for row in rows:
        assert sha((ROOT/row['origin']).read_bytes())==row['sha256']
        if row['target']=='tradingagents/research/onchain_replication/compact_mcm.py':
            row.update(origin=str((HERE/'compact_mcm.py').relative_to(ROOT)),sha256=sha(new),bytes=len(new),git_commit=None,git_path=None)
    save(HERE/'source_inventory01.json',{'schema_version':1,'predecessor':{'path':str(predecessor.relative_to(ROOT)),'sha256':sha(predecessor.read_bytes())},'source_inventory':rows,'composed_package_count':142,'source_logical_bytes':sum(x['bytes'] for x in rows),'replaced_targets':['tradingagents/research/onchain_replication/compact_mcm.py'],'qualification':'Complete source closure for metadata-only candidate; separate refusal03 cleanup delta not composed; no executing Git/source anchor or actual gate/job.'})
    bodies=[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(HERE.iterdir()) if p.is_file() and p.name not in {'manifest01.json'}]
    save(HERE/'manifest01.json',{'schema_version':1,'status':'frozen_source_only_pending_independent_review','owned_bodies':bodies,'body_count':len(bodies),'logical_bytes':sum(x['bytes'] for x in bodies),'baseline_sha256':sha(old),'candidate_sha256':sha(new),'source_inventory_sha256':sha((HERE/'source_inventory01.json').read_bytes()),'actual_failure_reconstruction':{'path':str((FULL/'original-import-metadata-bound-investigation-2026-10-03/RECONSTRUCTION01.json').relative_to(ROOT)),'sha256':sha((FULL/'original-import-metadata-bound-investigation-2026-10-03/RECONSTRUCTION01.json').read_bytes())},'qualification':'Source/stdlib tests only; original failed capsule unchanged; no numerical imports, admission, claim, job, budget amendment or release.'})
    print(json.dumps({'manifest_sha256':sha((HERE/'manifest01.json').read_bytes()),'source_inventory_sha256':sha((HERE/'source_inventory01.json').read_bytes()),'candidate_sha256':sha(new),'body_count':len(bodies)}))
if __name__=='__main__':main()
