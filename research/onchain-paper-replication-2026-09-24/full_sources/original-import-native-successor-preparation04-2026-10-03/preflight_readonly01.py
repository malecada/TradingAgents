"""Actual committed read-only admission/fixture boundary, no numerical imports."""
import hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;CAP=HERE/'capsule02'
sys.path.insert(0,str(CAP))
from tradingagents.research.admission import admit,claims
from tradingagents.research.onchain_replication import resource_fixture
def main():
    draft=json.loads((HERE/'release-draft01.json').read_bytes());identity=draft['cases']['success']['identity']
    ad=admit(root=CAP,registration=draft['registration'],experiment=identity,source=draft['capsule_commit'])
    job=json.loads((CAP/ad.inputs['execution_job']['path']).read_bytes())
    resource_fixture.admitted(ad,job)
    assert ad.ready and ad.effective_attempt_budget==3 and len(claims(CAP))==1
    assert not {'numpy','torch','scipy'}&set(sys.modules)
    assert not (CAP/'research_runs'/identity).exists() and not (CAP/'fixture_outer'/identity).exists()
    try:
        admit(root=CAP,registration=draft['registration'],experiment=draft['cases']['second_target_publication_failure']['identity'],source=draft['capsule_commit'])
    except ValueError as error:
        assert str(error)=='budget extension first-adopter snapshot is stale or incomplete';dependent=str(error)
    else:raise AssertionError('dependent identity ready without actual initial adopter')
    record={'schema_version':1,'status':'actual_read_only_successor_admission_and_selected_fixture_passed','identity':identity,
        'capsule_head':draft['capsule_commit'],'registration_sha256':draft['registration_sha256'],'ready':ad.ready,'effective_budget':3,
        'existing_claims':1,'new_claims':0,'input_count':len(ad.inputs),'source_count':len(ad.experiment['source_files']),
        'selected_fixture_module_sha256':hashlib.sha256(Path(resource_fixture.__file__).read_bytes()).hexdigest(),
        'dependent_case_admission':'pending actual first-adopter claim','dependent_refusal':dependent,
        'numerical_imports':False,'qualification':'Actual pure-metadata public admission and source-selected fixture.admitted succeeded. No ResearchRun.start, Binding/Owner birth, numerical/full producer preflight, native controls, MCM/scalar comparisons, wholecapacity or execution release. Dependent budget admission remains rightly refused until an actual first adopter; no synthetic claim is inserted.'}
    with (HERE/'READ_ONLY_PREFLIGHT01.json').open('x') as stream:json.dump(record,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps(record,sort_keys=True))
if __name__=='__main__':main()
