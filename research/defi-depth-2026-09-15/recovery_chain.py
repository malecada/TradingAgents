"""Validate explicit recovery provenance alongside a completed scientific claim."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess

BASE='research/defi-depth-2026-09-15/'
FILES={'recovery_adapter':BASE+'f1_restart_recovery.py',
       'recovery_decision':BASE+'F1-RESTART-DECISION.md',
       'recovery_investigation':BASE+'reviews/f1-restart-recovery-review.md'}
INPUTS=('f1_claim','f1_terminal','recovery_config','recovery_attachment','recovery_started','recovery_complete','recovery_import',*FILES)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def verify(inputs,root):
    claim=json.loads(inputs['f1_claim']);terminal=json.loads(inputs['f1_terminal'])
    config=json.loads(inputs['recovery_config']);started=json.loads(inputs['recovery_started']);done=json.loads(inputs['recovery_complete'])
    claim_hash=sha(inputs['f1_claim']);terminal_hash=sha(inputs['f1_terminal'])
    if terminal['status']!='complete' or terminal['claim_sha256']!=claim_hash:raise ValueError('completed original claim required')
    if inputs['recovery_attachment']!=inputs['recovery_started']:raise ValueError('shared attachment and recovery start differ')
    if started['recovery_config_sha256']!=sha(inputs['recovery_config']):raise ValueError('recovery config hash differs')
    if (started['recovery_id']!=config['recovery_id'] or started['original_root']!=config['execution_root']
        or not re.fullmatch('[0-9a-f]{40}',started['recovery_source'])):
        raise ValueError('recovery operation/source identity differs')
    if set(config['source_files'])!=set(FILES.values()):raise ValueError('exact recovery source inventory differs')
    for name,path in FILES.items():
        if sha(inputs[name])!=config['source_files'][path]:raise ValueError('recovery source bytes differ')
    for name,path in {**FILES,'recovery_config':BASE+'f1-restart-recovery.json'}.items():
        try:
            committed=subprocess.check_output(['git','show',started['recovery_source']+':'+path],cwd=root,stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as exc:raise ValueError('asserted recovery commit cannot be verified') from exc
        if committed!=inputs[name]:raise ValueError('asserted recovery commit source/config bytes differ')
    for obj in (config,started,done):
        if obj['original_claim_sha256']!=claim_hash:raise ValueError('recovery refers to another claim')
    if config['experiment']!=claim['experiment_id'] or config['registration']!=claim['registration']:
        raise ValueError('recovery experiment identity differs')
    for obj in (config,started):
        if obj['original_source']!=claim['source'] or obj['original_started_at']!=claim['started_at']:
            raise ValueError('original recovery source/time differs')
    if (config['new_empirical_claim'] is not False or config['shared_measurement_repair_consumed'] is not False
        or started['new_empirical_claim'] is not False or started['initial_output_members']!=[]):
        raise ValueError('recovery scope or budget differs')
    if config['required_original_output_members']!=[] or started['new_source_request_before_attachment'] is not False:
        raise ValueError('recovery empty-state/source scope differs')
    if done['original_terminal_sha256']!=terminal_hash or done['original_terminal']!='complete.json':
        raise ValueError('recovery completion terminal differs')
    receipt_dir=Path(root)/'research_recoveries'/config['recovery_id']
    expected={'attachment.json':'recovery_attachment','started.json':'recovery_started','complete.json':'recovery_complete'}
    if receipt_dir.is_symlink() or not receipt_dir.is_dir() or {p.name for p in receipt_dir.iterdir()}!=set(expected):
        raise ValueError('complete imported recovery directory required; failed/pending/extra records cannot be omitted')
    for filename,name in expected.items():
        path=receipt_dir/filename
        if path.is_symlink() or not path.is_file() or path.read_bytes()!=inputs[name]:
            raise ValueError('imported recovery directory bytes differ')
    inventory=json.loads(inputs['recovery_import'])
    hashes={filename:sha(inputs[name]) for filename,name in expected.items()}
    original_marker=str(Path(config['execution_root'])/'research_runs'/('.'+config['experiment']+'-recovery-attachment.json'))
    if (inventory['source_directory']!=started['recovery_receipt_directory']
        or inventory['source_members_sha256']!={k:v for k,v in hashes.items() if k!='attachment.json'}
        or inventory['attachment_source']!=original_marker or inventory['attachment_sha256']!=hashes['attachment.json']
        or inventory['destination_directory']!='research_recoveries/'+config['recovery_id']
        or inventory['destination_members_sha256']!=hashes):
        raise ValueError('complete recovery import inventory differs')
    clocks=[claim['started_at'],started['started_at'],terminal['ended_at'],done['ended_at']]
    values=[datetime.fromisoformat(v) for v in clocks]
    if any(v.tzinfo is None or v.utcoffset().total_seconds()!=0 for v in values) or values!=sorted(values):
        raise ValueError('recovery chronology differs')
    return {'original_scientific_source':claim['source'],'additional_recovery_source':started['recovery_source'],
            'original_claim_sha256':claim_hash,'original_terminal_sha256':terminal_hash,
            'recovery_attachment_sha256':sha(inputs['recovery_attachment']),
            'recovery_import_sha256':sha(inputs['recovery_import']),
            'recovery_started_at':started['started_at'],'recovery_completed_at':done['ended_at'],
            'new_empirical_claim':False,'scope':'Hash/identity/clock chain; additional reviewed execution provenance, no economic validation'}
