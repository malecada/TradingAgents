"""Prospective reviewed ceilings without rewriting historical family objects.

This is metadata admission only. Independent review and a larger claim ceiling do
not supply source, resource, scientific, trading or deployment authorization.
"""
import hashlib
import json
import re


def effective_budget(root, program, experiment_id, experiment, family, relevant, read_bound):
    base=family['attempt_budget']
    previous=max([base]+[c.get('effective_attempt_budget',base) for c in relevant])
    reference=experiment.get('cumulative_budget_extension')
    if reference is None:
        if previous>base:raise ValueError('adopted budget extension must be carried forward')
        return base
    if not isinstance(reference,dict) or set(reference)!={'extension','review'}:
        raise ValueError('budget extension reference differs')
    raw=read_bound(reference['extension']);extension=json.loads(raw)
    fields={'schema_version','program_id','base_family','cumulative_ceiling',
            'consumed_before','initial_experiment','allocation','claims','reason'}
    if (not isinstance(extension,dict) or set(extension)!=fields
            or type(extension['schema_version']) is not int or extension['schema_version']!=1
            or extension['program_id']!=program or extension['base_family']!=family):
        raise ValueError('budget extension program/base family differs')
    ceiling=extension['cumulative_ceiling']
    if type(ceiling) is not int or ceiling<=base or ceiling<previous:
        raise ValueError('budget extension ceiling must increase baseline and retain adopted ceiling')
    if not isinstance(extension['reason'],str) or not extension['reason'].strip():
        raise ValueError('budget extension reason required')
    initial=extension['initial_experiment']
    if not isinstance(initial,str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}',initial):
        raise ValueError('budget extension initial adopter identity differs')
    # Allocation contents are reviewed policy, pinned as metadata, never data.
    if not isinstance(json.loads(read_bound(extension['allocation'])),dict):
        raise ValueError('budget extension allocation object required')
    review=json.loads(read_bound(reference['review']))
    if (not isinstance(review,dict) or set(review)!={'schema_version','decision','extension_sha256','reviewer','scope'}
            or type(review['schema_version']) is not int or review['schema_version']!=1
            or review['decision']!='accepted' or review['extension_sha256']!=hashlib.sha256(raw).hexdigest()
            or any(not isinstance(review[k],str) or not review[k].strip() for k in ('reviewer','scope'))):
        raise ValueError('accepted review of exact budget extension required')
    snapshot=extension['claims'];claims={c['experiment_id']:c for c in relevant};seen=set()
    if not isinstance(snapshot,list) or not snapshot:
        raise ValueError('budget extension closed claim snapshot required')
    for record in snapshot:
        if not isinstance(record,dict) or set(record)!={'experiment','claim_sha256','terminal_status','terminal_sha256'}:
            raise ValueError('budget extension snapshot record differs')
        name=record['experiment']
        if not isinstance(name,str) or name not in claims or name in seen or name==initial:
            raise ValueError('budget extension snapshot identity differs')
        seen.add(name);directory=root/'research_runs'/name
        if record['terminal_status'] not in ('complete','failed'):
            raise ValueError('budget extension snapshot terminal status differs')
        terminal=directory/(record['terminal_status']+'.json')
        if terminal.is_symlink() or not terminal.is_file():
            raise ValueError('budget extension snapshot requires closed claims')
        claim_raw=(directory/'claim.json').read_bytes();terminal_raw=terminal.read_bytes()
        value=json.loads(terminal_raw)
        if (hashlib.sha256(claim_raw).hexdigest()!=record['claim_sha256']
                or hashlib.sha256(terminal_raw).hexdigest()!=record['terminal_sha256']
                or value.get('claim_sha256')!=record['claim_sha256']
                or value.get('experiment_id')!=name or value.get('status')!=record['terminal_status']):
            raise ValueError('budget extension snapshot claim/terminal binding differs')
    used=extension['consumed_before']
    if type(used) is not int or used!=family['prior_attempts']+len(seen) or used>=ceiling:
        raise ValueError('budget extension snapshot cumulative count differs')
    adopters=[c for c in relevant if c['experiment'].get('cumulative_budget_extension')==reference]
    if not adopters:
        if experiment_id!=initial or seen!=set(claims):
            raise ValueError('budget extension first-adopter snapshot is stale or incomplete')
    else:
        first=min(adopters,key=lambda c:c['started_at'])
        if first['experiment_id']!=initial or first.get('effective_attempt_budget')!=ceiling:
            raise ValueError('budget extension original adopter differs')
        # No pre-adoption claim may disappear from the accepted snapshot.
        if any(name not in seen and c['started_at']<first['started_at'] for name,c in claims.items()):
            raise ValueError('budget extension snapshot omits an earlier claim')
    return ceiling
