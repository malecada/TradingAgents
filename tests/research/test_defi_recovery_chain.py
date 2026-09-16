"""Invented provenance records only; no actual source/results opened."""
import importlib.util
import json
import subprocess
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('tested_recovery_chain',Path(__file__).resolve().parents[2]/'research/defi-depth-2026-09-15/recovery_chain.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def encode(x):return json.dumps(x).encode()


def fixture(root):
    claim={'experiment_id':'invented','source':'a'*40,'registration':'invented.json','started_at':'2026-09-16T09:00:00+00:00'}
    c=encode(claim);h=m.sha(c)
    t=encode({'status':'complete','claim_sha256':h,'ended_at':'2026-09-16T11:00:00+00:00'})
    files={name:('invented '+name).encode() for name in m.FILES}
    config={'experiment':'invented','registration':'invented.json','original_claim_sha256':h,'original_source':'a'*40,
        'original_started_at':claim['started_at'],'new_empirical_claim':False,'shared_measurement_repair_consumed':False,
        'required_original_output_members':[],'recovery_id':'invented-recovery','execution_root':'/invented/root',
        'source_files':{path:m.sha(files[name]) for name,path in m.FILES.items()}}
    configraw=encode(config)
    def git(*args):
        return subprocess.check_output(['git','-c','core.hooksPath=/dev/null',*args],cwd=root).decode().strip()
    git('init','-q')
    for name,path in m.FILES.items():
        p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(files[name])
    (root/(m.BASE+'f1-restart-recovery.json')).write_bytes(configraw)
    git('add','research');git('-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid','commit','-qm','invented recovery source')
    recovery_source=git('rev-parse','HEAD')
    started={'original_claim_sha256':h,'original_source':'a'*40,'original_started_at':claim['started_at'],
        'recovery_source':recovery_source,'recovery_config_sha256':m.sha(configraw),'started_at':'2026-09-16T10:00:00+00:00',
        'initial_output_members':[],'new_empirical_claim':False,'new_source_request_before_attachment':False,
        'recovery_id':'invented-recovery','original_root':'/invented/root',
        'recovery_receipt_directory':'/invented/recovery-root/research_recoveries/invented-recovery'}
    startedraw=encode(started)
    done=encode({'original_claim_sha256':h,'original_terminal_sha256':m.sha(t),'original_terminal':'complete.json',
                 'ended_at':'2026-09-16T11:00:01+00:00'})
    directory=root/'research_recoveries'/'invented-recovery';directory.mkdir(parents=True)
    for name,raw in [('attachment.json',startedraw),('started.json',startedraw),('complete.json',done)]:
        (directory/name).write_bytes(raw)
    hashes={p.name:m.sha(p.read_bytes()) for p in directory.iterdir()}
    inventory=encode({'source_directory':started['recovery_receipt_directory'],
        'source_members_sha256':{k:v for k,v in hashes.items() if k!='attachment.json'},
        'attachment_source':'/invented/root/research_runs/.invented-recovery-attachment.json',
        'attachment_sha256':m.sha(startedraw),'destination_directory':'research_recoveries/invented-recovery',
        'destination_members_sha256':hashes})
    return {'f1_claim':c,'f1_terminal':t,'recovery_config':configraw,'recovery_attachment':startedraw,
            'recovery_started':startedraw,'recovery_complete':done,'recovery_import':inventory,**files}


def test_both_execution_sources_and_original_claim_retained(tmp_path):
    x=fixture(tmp_path);r=m.verify(x,tmp_path)
    assert r['original_scientific_source']=='a'*40 and r['additional_recovery_source']==json.loads(x['recovery_started'])['recovery_source']
    assert r['new_empirical_claim'] is False


@pytest.mark.parametrize('part',['recovery_adapter','recovery_decision','recovery_investigation','recovery_attachment'])
def test_changed_source_or_shared_attachment_is_rejected(part,tmp_path):
    x=fixture(tmp_path);x[part]+=b' '
    with pytest.raises(ValueError):m.verify(x,tmp_path)


def test_completion_cannot_refer_to_another_terminal(tmp_path):
    x=fixture(tmp_path);done=json.loads(x['recovery_complete']);done['original_terminal_sha256']='0'*64
    x['recovery_complete']=encode(done)
    with pytest.raises(ValueError,match='completion terminal'):m.verify(x,tmp_path)


def test_postdated_recovery_cannot_claim_prior_execution(tmp_path):
    x=fixture(tmp_path);s=json.loads(x['recovery_started']);s['started_at']='2026-09-16T12:00:00+00:00'
    x['recovery_started']=x['recovery_attachment']=encode(s)
    for name in ('started.json','attachment.json'):
        (tmp_path/'research_recoveries/invented-recovery'/name).write_bytes(encode(s))
    inventory=json.loads(x['recovery_import']);h=m.sha(encode(s))
    inventory['source_members_sha256']['started.json']=h;inventory['attachment_sha256']=h
    inventory['destination_members_sha256'].update({'started.json':h,'attachment.json':h})
    x['recovery_import']=encode(inventory)
    with pytest.raises(ValueError,match='chronology'):m.verify(x,tmp_path)


def test_asserted_recovery_commit_cannot_be_relabelled(tmp_path):
    x=fixture(tmp_path);s=json.loads(x['recovery_started']);s['recovery_source']='0'*40
    x['recovery_started']=x['recovery_attachment']=encode(s)
    with pytest.raises(ValueError,match='commit cannot be verified'):m.verify(x,tmp_path)


@pytest.mark.parametrize('extra',['failed.json','.complete.json.pending','unlisted'])
def test_extra_recovery_records_cannot_be_hidden_from_admission(tmp_path,extra):
    x=fixture(tmp_path)
    (tmp_path/'research_recoveries/invented-recovery'/extra).write_bytes(b'invented')
    with pytest.raises(ValueError,match='complete imported recovery directory'):m.verify(x,tmp_path)


def test_imported_receipt_cannot_differ_from_registered_bytes(tmp_path):
    x=fixture(tmp_path)
    (tmp_path/'research_recoveries/invented-recovery/complete.json').write_bytes(b'changed')
    with pytest.raises(ValueError,match='directory bytes differ'):m.verify(x,tmp_path)


def test_source_import_inventory_cannot_omit_failed_record(tmp_path):
    x=fixture(tmp_path);inventory=json.loads(x['recovery_import'])
    inventory['source_members_sha256']['failed.json']='f'*64
    x['recovery_import']=encode(inventory)
    with pytest.raises(ValueError,match='import inventory differs'):m.verify(x,tmp_path)
