"""Explicit resource subset, derived only in the genuine registered worker.

This does not emit a schema1 financial population or full-fold scaler claim.
Importing this module is metadata-only; numerical imports stay in produce().
"""
import hashlib
import json
from datetime import datetime, timedelta

SCOPE = 'resource_pilot_subset'
SCOPE_SHA = '57a97518d2b12e0c787b49f91d9bf509888f9c63fb8f644d1ace90b5bd05e2a8'
PRICE_PANEL_SHA = 'f7a4d89ff66d37ec00d8d4d834a1a771ac55f36bc9b210cfbecb6768ecc3bbbe'
CALENDAR_SHA = '21bb348b9c779238b212d0e4074cf806f6a54d0ce3b7713d97bc3ad65d57ef22'
PRICE_SOURCE_SHA = '46b18f3df967405374b1f6ee8a3d11ee1b7a5b176ac9fb4342caf6bf8648f2cc'
GRAPH_CONFIG_SHA = '01ed0f0dc76b2685598dd7687466dd81880e5d332c0c6827da8f90f8f17a4a9d'
DECISIONS = [(datetime(2022,6,7)+timedelta(days=i)).isoformat()+'Z' for i in range(16)]
WEEKS = [(datetime(2022,5,2)+timedelta(days=7*i)).isoformat()+'Z' for i in range(7)]


def require(value, message):
    if not value: raise ValueError('resource population: '+message)


def validate_plan(plan, pilot):
    require(type(plan) is dict and set(plan)=={'schema_version','population_scope','financial_fit_complete','fold','scope_input','calendar_input','price_panel_input','graphs','outputs'}, 'plan fields differ')
    require(type(plan['schema_version']) is int and plan['schema_version']==1
            and plan['population_scope']==SCOPE and plan['financial_fit_complete'] is False
            and plan['fold']=='2024', 'explicit resource subset required')
    require(pilot['schema_version']==2 and pilot['population_scope']==SCOPE
            and pilot['indices'] is None and pilot['decisions']==DECISIONS, 'fixed deferred eligible selection differs')
    require(type(plan['graphs']) is dict and set(plan['graphs'])==set(WEEKS)
            and set(plan['graphs'].values())==set(pilot['graph_inputs'].values()), 'seven complete graph roles required')
    roles=[plan['scope_input'],plan['calendar_input'],plan['price_panel_input'],*plan['graphs'].values()]
    require(all(type(x) is str and x for x in roles) and len(set(roles))==10, 'distinct registered input roles required')
    outputs=plan['outputs']
    require(type(outputs) is dict and set(outputs)=={'resource_population','binding'}
            and len(set(outputs.values()))==2 and all(type(x) is str and x for x in outputs.values()), 'explicit distinct output roles required')
    return plan


def selected_positions(train, decisions):
    """Pure membership seam, operating on already derived actual training rows."""
    require(decisions==DECISIONS, 'frozen decision dates differ')
    dates=[row.decision_at for row in train]
    require(dates==sorted(set(dates)), 'training order differs')
    positions=[]
    for decision in decisions:
        require(decision in dates, 'selected decision is not genuinely eligible')
        positions.append(dates.index(decision))
    require(positions==list(range(positions[0],positions[0]+16)), 'selected eligible rows are not consecutive')
    return positions


def produce(run, plan_input, pilot):
    from tradingagents.research.lifecycle import ResearchRun
    require(type(run) is ResearchRun, 'genuine registered worker required')
    run._active(); run._check_source()
    from dataclasses import asdict
    from .contracts import Fold, PricePanel
    from .dataset import CalendarGraph, ExampleManifest, build_examples_from_metadata, fit_scaler
    from .provenance import canonical_bytes, digest
    plan=validate_plan(json.loads(run.read_input(plan_input)),pilot)
    require(set(plan['outputs'].values()) <= set(run.admission.experiment['outputs']), 'outputs not admitted')
    require(not set(plan['outputs'].values()) & set(run._published_outputs), 'outputs already published')
    require(hashlib.sha256(run.read_input(plan['scope_input'])).hexdigest()==SCOPE_SHA, 'registered subset scope differs')
    raw=run.read_input(plan['calendar_input'])
    require(hashlib.sha256(raw).hexdigest()==CALENDAR_SHA, 'fixed calendar differs')
    calendar=json.loads(raw);fold_record=next(f for f in calendar['folds'] if f['id']=='2024')
    fold=Fold(**fold_record,member_hash=digest(canonical_bytes(fold_record)))
    price_raw=run.read_input(plan['price_panel_input'])
    require(hashlib.sha256(price_raw).hexdigest()==PRICE_PANEL_SHA, 'retained original price panel differs')
    price_record=json.loads(price_raw)
    prices=PricePanel(**{k:tuple(v) if k in ('dates','closes','missing_dates') else v for k,v in price_record.items()})
    require(prices.symbol=='ETH-USD' and prices.source_hash==PRICE_SOURCE_SHA, 'original actual price source differs')
    graphs=[];manifest_pins={}
    for week,role in sorted(plan['graphs'].items()):
        raw=run.read_input(role);value=json.loads(raw);metadata=value['metadata'];key=value['graph_hash']
        require(metadata['asset']=='ETH' and metadata['start_utc']==week
                and metadata['graph_config_hash']==GRAPH_CONFIG_SHA
                and pilot['graph_inputs'].get(key)==role, 'complete graph identity differs')
        graphs.append(CalendarGraph(metadata['asset'],metadata['start_utc'],metadata['end_utc'],metadata['available_at'],tuple(metadata['source_hashes']),key))
        manifest_pins[week]=digest(raw)
    # Original date/price/availability/label checks; original paper assembler is untouched.
    observed=build_examples_from_metadata(graphs,prices,fold,calendar)
    positions=selected_positions(observed.train,pilot['decisions'])
    selected=tuple(observed.train[i] for i in positions)
    require([list(x.graph_hashes) for x in selected]==pilot['graph_sequences'], 'actual selected graph sequences differ')
    require({h for x in selected for h in x.graph_hashes}==set(pilot['graph_inputs']), 'exact seven graph membership differs')
    examples=ExampleManifest(selected,(),(),digest(canonical_bytes([asdict(x) for x in selected])),
                             digest(canonical_bytes([])),observed.source_hashes,observed.fold_hash)
    # Same scaler algorithm, explicitly fitted to this selected resource population.
    scaler=fit_scaler(examples,prices,fold)
    indices=list(range(len(examples.train)))
    value={'schema_version':1,'population_scope':SCOPE,'financial_fit_complete':False,
           'paper_financial_fits':0,'full_fold_population':False,'full_fold_scaler':False,
           'decision_dates':pilot['decisions'],'source_candidate_positions':positions,'subset_indices':indices,
           'resource_train_hash':examples.train_hash,'resource_scaler':asdict(scaler),
           'resource_rows':[asdict(x) for x in selected], 'graph_manifest_hashes':manifest_pins,
           'source_population_eligible_training_count':len(observed.train),
           'source_population_exclusions':[dict(x) for x in observed.exclusions],
           'qualification':'Original eligibility and scaler algorithms applied to prospectively declared16-row resource subset. No full-fold population, scaler, test-mask, accuracy or financial completion claim.'}
    # The wrapper deliberately cannot pass population_from_record or assemble_population.
    run.write_json(plan['outputs']['resource_population'],value)
    run.write_json(plan['outputs']['binding'],{'schema_version':1,'population_scope':SCOPE,
        'financial_fit_complete':False,'plan_sha256':run.admission.inputs[plan_input]['sha256'],
        'pilot_population_sha256':digest(canonical_bytes(value)),'resource_train_hash':examples.train_hash,
        'graph_manifest_hashes':manifest_pins,'price_panel_sha256':run.admission.inputs[plan['price_panel_input']]['sha256']})
    return examples,scaler,indices
