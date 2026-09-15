"""Read-only staged source admission and bounded normalization, never evaluation.

The external assignment anchor is supplied by the local coordinator. Original
host/data-root values are provenance; staging deliberately does not execute the
worker or impersonate its host. Source seals do not establish worker quiescence.
"""
from collections.abc import Mapping
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat

from . import adapter, funding
from .journal import Journal, encode, digest, safe
from .schedule import ASSETS, DAY, HOUR, JOURNALS, WINDOW, calendar, groups
from .worker import CAPS, RESERVES, PACKAGE_FILES

MIB=1024**2
MAX_BYTES=2*1024**3
MAX_MEMBERS=1200100
CELLS=tuple(f'{a.lower()}-{capital}-{cost}' for a in ASSETS for capital in (1000,10000) for cost in ('base','stress'))


def _regular(path, cap):
    path=safe(path);info=path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size>cap:raise ValueError('bounded regular staged member required')
    return info.st_size


def _open_read(path,cap):
    _regular(path,cap)
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    info=os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_size>cap:
        os.close(fd);raise ValueError('bounded regular staged descriptor required')
    return os.fdopen(fd,'rb')


def _read(path,cap=16*MIB):
    with _open_read(path,cap) as stream:return stream.read(cap+1)


def _hash(path,cap=16*MIB):
    h=hashlib.sha256()
    with _open_read(path,cap) as stream:
        for chunk in iter(lambda:stream.read(MIB),b''):h.update(chunk)
    return h.hexdigest()


def _json(path,cap=16*MIB):return json.loads(_read(path,cap))


def _ms(text):
    d=datetime.fromisoformat(text.replace('Z','+00:00'))
    if d.utcoffset() is None or d.utcoffset().total_seconds()!=0:raise ValueError('explicit UTC source clocks')
    return int(d.timestamp()*1000)


def package_assignment(package,expected):
    package=safe(package)
    raw=_read(package/'assignment.json',MIB)
    if not isinstance(expected,str) or not re.fullmatch('[0-9a-f]{64}',expected) or digest(raw)!=expected:raise ValueError('external assignment anchor mismatch')
    spec=json.loads(raw)
    keys={'schema_version','entry_ms','lease_not_before_ms','lease_expires_ms','claim_path','claim_sha256','package_files','journal_caps','terminal_reserves','authority','target','source_commit','data_root','host_identity'}
    if set(spec)!=keys or type(spec['schema_version']) is not int or spec['schema_version']!=1 or spec['authority']!='raw-worker-only' or spec['target']!='options-episode-20260911':raise ValueError('raw assignment schema/authority')
    t=spec['entry_ms'];calendar(t)
    if spec['lease_not_before_ms']!=t-120000 or spec['lease_expires_ms']!=t+45*DAY+60000 or spec['journal_caps']!=CAPS or spec['terminal_reserves']!=RESERVES:raise ValueError('frozen assignment clocks/resources')
    if spec['claim_path']!='claim.json' or _hash(package/'claim.json',512*1024)!=spec['claim_sha256']:raise ValueError('copied claim anchor')
    claim=_json(package/'claim.json',512*1024)
    if not isinstance(spec['source_commit'],str) or not re.fullmatch('[0-9a-f]{40}',spec['source_commit']) or claim.get('source')!=spec['source_commit']:raise ValueError('claim source pin')
    protocol=claim['episode_protocol']
    if [_ms(protocol['worker_lease'][k]) for k in ('not_before','expires_at')]!=[spec['lease_not_before_ms'],spec['lease_expires_ms']] or [_ms(protocol['observation_window'][k]) for k in ('start','end')]!=[t,t+44*DAY+WINDOW]:raise ValueError('claim future/lease binding')
    if not isinstance(spec['host_identity'],str) or not spec['host_identity'] or not isinstance(spec['data_root'],str) or not Path(spec['data_root']).is_absolute() or '..' in Path(spec['data_root']).parts:raise ValueError('original host/data provenance')
    if set(spec['package_files'])!=PACKAGE_FILES:raise ValueError('exact source package denominator')
    allowed=set(PACKAGE_FILES)|{'assignment.json','claim.json'}
    dirs={str(parent) for name in allowed for parent in Path(name).parents if str(parent)!='.'}
    seen=set()
    for current,subdirs,names in os.walk(package,followlinks=False):
        for name in subdirs:
            p=Path(current)/name
            if p.is_symlink() or p.relative_to(package).as_posix() not in dirs:raise ValueError('unsafe/unregistered package directory')
        for name in names:
            p=Path(current)/name;relative=p.relative_to(package).as_posix()
            if relative not in allowed:raise ValueError('unregistered package file')
            _regular(p,2*MIB);seen.add(relative)
    if seen!=allowed:raise ValueError('missing package member')
    for name,hashed in spec['package_files'].items():
        if _hash(package/name,2*MIB)!=hashed:raise ValueError('package source hash mismatch')
    # Normalization must use the same source journal/calendar/selection parser.
    root=Path(__file__).resolve().parents[2]
    for name in ('journal','schedule','adapter'):
        relative=f'tradingagents/research_options_capture/{name}.py'
        if _hash(root/relative,2*MIB)!=spec['package_files'][relative]:raise ValueError('local normalizer differs from frozen capture parser')
    for name in ('selection','batch'):
        relative=f'research/strategy-search-2026-09-11/options_policy_{name}.py'
        if _hash(root/relative,2*MIB)!=spec['package_files'][relative]:raise ValueError('local policy parser differs from frozen source')
    return spec


def _inventory(data,entry):
    data=safe(data)
    if not data.is_dir():raise ValueError('staged data directory missing')
    rootfiles={'selection.json','source-seal.json','STOP','worker.lock','supervisor.lock'}
    slots=calendar(entry)
    caps={name:{s['id']:s['body_cap'] for s in values} for name,values in slots.items()}
    caps['selected']={f'h{h:04d}-{a.lower()}-{side}-{role}':8192 for h in range(1057) for a in ASSETS for side in ('call','put') for role in ('depth','mark')}
    total=count=0;partials={};directories=[];roots=[]
    # Full structural/count pass before any content hash, including the tighter
    # worker frame denominator, before the generic journal validator allocates.
    for p in data.iterdir():
        if p.name in JOURNALS:
            if p.is_symlink() or not p.is_dir():raise ValueError('unsafe journal directory')
            directories.append(p)
            with os.scandir(p) as entries:
                for e in entries:
                    name=e.name
                    if name not in {'lock','spec.json','seal.json'} and not re.fullmatch(r'(intent|receipt)-[a-z0-9-]+\.json|partial-[a-z0-9-]+-[0-9]{6}\.bin|recovery-[0-9]{6}\.json|pending-[0-9a-f]{32}',name):raise ValueError('unregistered journal member')
                    size=_regular(Path(e.path),16*MIB);total+=size;count+=1
                    if total>MAX_BYTES or count>MAX_MEMBERS:raise ValueError('whole return byte/member cap')
                    if name.startswith('partial-'):
                        slot=name[len('partial-'):].rsplit('-',1)[0]
                        if slot not in caps[p.name]:raise ValueError('unknown partial source slot')
                        cap=caps[p.name][slot];frame=max(8192,(cap+62)//63);limit=(cap+frame-1)//frame
                        key=(p.name,slot);partials[key]=partials.get(key,0)+1
                        if partials[key]>limit:raise ValueError('fragmentation exceeds frozen production worker frame bound')
        elif p.name in rootfiles or re.fullmatch(r'supervisor-exit-[0-9]{6}\.json',p.name):
            total+=_regular(p,MIB);count+=1;roots.append(p)
        else:raise ValueError('unexpected staged data member')
    if total>MAX_BYTES or count>MAX_MEMBERS:raise ValueError('whole return byte/member cap')
    stream=hashlib.sha256()
    for p in sorted(roots+directories,key=lambda p:p.name):
        members=(p/name for name in sorted(os.listdir(p))) if p in directories else iter((p,))
        for member in members:
            record=[member.relative_to(data).as_posix(),_regular(member,16*MIB),_hash(member)]
            stream.update(encode(record))
    return {'member_count':count,'logical_bytes':total,'inventory_sha256':stream.hexdigest()}


class Receipts(Mapping):
    """Read at most one bounded receipt; no eager multi-day metadata cache."""
    def __init__(self,data,name,slots):
        self.directory=data/name
        self.names={s['id'] for s in slots if (self.directory/('receipt-'+s['id']+'.json')).exists()}
    def __iter__(self):return iter(self.names)
    def __len__(self):return len(self.names)
    def __getitem__(self,name):
        if name not in self.names:raise KeyError(name)
        return _json(self.directory/('receipt-'+name+'.json'))


def _selection(data,full,assignment_sha,entry):
    path=data/'selection.json'
    if not path.exists():return None,None
    saved=_json(path,MIB)
    if set(saved)!={'assignment_sha256','result','input_sha256'} or saved['assignment_sha256']!=assignment_sha:raise ValueError('selection assignment binding')
    initial=_json(data/'bootstrap/receipt-initial-options-rules.json')
    names=groups(full['known'])[0][1]
    known={name:_json(data/'known'/('receipt-'+name+'.json')) for name in names}
    bindings={'initial':digest(encode(initial)),**{name:digest(encode(row)) for name,row in known.items()}}
    recomputed=adapter.select_initial(initial,{name.removeprefix('h0000-'):row for name,row in known.items()},entry_ms=entry)
    if saved['input_sha256']!=bindings or saved['result']!=recomputed:raise ValueError('selection raw binding or deterministic result changed')
    if set(recomputed)!=set(ASSETS) or any(recomputed[a].get('status')!='complete' for a in ASSETS):return saved,None
    return saved,{a:recomputed[a]['selected'] for a in ASSETS}


def _rules(options,futures,selection):
    # Preserve every matching row, including duplicates and malformed filters.
    # Per-asset rule_snapshot performs semantic validation; a BTC failure must
    # not erase valid ETH rules. Invalid shared containers affect both assets.
    if not isinstance(options,dict) or not isinstance(futures,dict):raise ValueError('rule objects required')
    for rows in (options['optionContracts'],options['optionSymbols'],futures['symbols']):
        if not isinstance(rows,list) or any(not isinstance(row,dict) for row in rows):raise ValueError('rule row/list schema')
    selected={selection[a][side] for a in ASSETS for side in ('call','put')}
    symbols={a+'USDT' for a in ASSETS}
    return {'options':{'optionContracts':[r for r in options['optionContracts'] if r.get('underlying') in symbols],
                       'optionSymbols':[r for r in options['optionSymbols'] if r.get('symbol') in selected]},
            'futures':{'symbols':[r for r in futures['symbols'] if r.get('symbol') in symbols]}}


def _rule_pair(receipts,slots,prefix):
    specs={s['id']:s for s in slots};values={};at=[]
    for venue,label in [('options','options'),('futures','futures')]:
        name=prefix+'-'+venue+'-rules';spec=specs[name]
        value,_,meta=adapter.decode(receipts[name],spec['request'],scheduled_ms=spec['scheduled_ms'],cap=spec['body_cap'])
        values[label]=value;at.append(meta['controller_retrieval_ms'])
    return values,max(at)


def prepare(*,package,data,expected_assignment_sha256,require_sealed=True):
    package=safe(package);data=safe(data)
    spec=package_assignment(package,expected_assignment_sha256)
    inventory=_inventory(data,spec['entry_ms']);full=calendar(spec['entry_ms'])
    saved,selection=_selection(data,full,expected_assignment_sha256,spec['entry_ms'])
    if selection is not None:full=calendar(spec['entry_ms'],selection)
    reports={};seals={};expected_journals=set(JOURNALS)-({'selected'} if selection is None else set())
    if selection is None and (data/'selected').exists():raise ValueError('selected journal without admitted initial identities')
    for name in expected_journals:
        if not (data/name).exists():continue
        with Journal(data/name,claim_path=package/'claim.json',claim_sha256=spec['claim_sha256'],slots=full[name],total_cap=CAPS[name],terminal_reserve=RESERVES[name],check_source=lambda:None,readonly=True) as journal:
            result=journal._cache
            counts={}
            for row in result['slots']:counts[row['status']]=counts.get(row['status'],0)+1
            reports[name]={'slots':len(result['slots']),'states':counts,'members':len(result['members']),'logical_bytes':result['bytes']}
            if (data/name/'seal.json').exists():seals[name]=_json(data/name/'seal.json',MIB)
    report={**inventory,'assignment_sha256':expected_assignment_sha256,'original_host':spec['host_identity'],'original_data_root':spec['data_root'],
            'staged_data_root':str(data),'journal_reports':reports,'intended_slot_count':17144,'quiescence':'unavailable: independent external observation review required',
            'selection_result':None if saved is None else saved['result'],'source_status':'incomplete','reasons':[]}
    output={'source_report':report,'evaluate_kwargs':None,'unavailable_cells':[]}
    def unavailable(reason):
        report['reasons'].append(reason)
        output['unavailable_cells']=[{'id':name,'status':'unavailable','reason':reason} for name in CELLS]
        return output
    source_path=data/'source-seal.json'
    if not source_path.exists():
        return unavailable('Source is not sealed; no analysis-source admission.')
    source=_json(source_path,MIB)
    fields={'assignment_sha256','status','reason','journal_seals','intended_slot_count','unresolved_selected_slots','unresolved_selected_ids_sha256','failure_scope','selection_sha256','quiescent_ms','scope'}
    if set(source)!=fields or source['assignment_sha256']!=expected_assignment_sha256 or source['status'] not in {'complete','failed'} or source['intended_slot_count']!=17144 or source['journal_seals']!=seals or set(reports)!=expected_journals or set(seals)!=expected_journals:raise ValueError('source seal/whole denominator binding')
    if source['selection_sha256']!=(None if saved is None else _hash(data/'selection.json',MIB)):raise ValueError('global selection hash')
    unresolved=[f'h{h:04d}-{a.lower()}-{side}-{role}' for h in range(1057) for a in ASSETS for side in ('call','put') for role in ('depth','mark')]
    if source['unresolved_selected_slots']!=(8456 if selection is None else 0) or source['unresolved_selected_ids_sha256']!=(digest(encode(unresolved)) if selection is None else None):raise ValueError('unresolved selected denominator')
    if type(source['quiescent_ms']) is not int or not spec['lease_not_before_ms']<=source['quiescent_ms']<=spec['lease_expires_ms']:raise ValueError('source declared stop clock outside lease')
    if source['scope']!='raw source seal only; no financial or outer terminal authority' or source['failure_scope']!='Source operability only; no economic rejection of either asset or strategy family.':raise ValueError('source seal authority scope')
    if any(s['status']!=source['status'] for s in seals.values()):raise ValueError('global/journal source disposition mismatch')
    if source['status']=='complete' and (selection is None or source['reason'] is not None):raise ValueError('source completion requires actual fixed selection')
    report['source_status']=source['status']
    if selection is None:return unavailable('Initial source selection unavailable; all eight cases retained without fabricated symbols.')
    lazy={name:Receipts(data,name,full[name]) for name in JOURNALS}
    try:
        initial,initial_at=_rule_pair(lazy['bootstrap'],full['bootstrap'],'initial')
        initial=_rules(initial['options'],initial['futures'],selection)
    except (KeyError,ValueError,TypeError,ArithmeticError) as exc:
        return unavailable('Initial rule source unavailable: '+str(exc))
    vintages=[]
    for day in range(45):
        try:
            values,available=_rule_pair(lazy['daily'],full['daily'],f'd{day:02d}')
        except (KeyError,ValueError,TypeError,ArithmeticError) as exc:
            report['reasons'].append(f'd{day:02d} rule pair missing/unadmitted: '+str(exc));continue
        try:projection=_rules(values['options'],values['futures'],selection)
        except (KeyError,ValueError,TypeError,ArithmeticError) as exc:
            projection={'options':{},'futures':{}};report['reasons'].append(f'd{day:02d} malformed/changed complete rules: '+str(exc))
        vintages.append({**projection,'available_ms':available})
    records={a:[] for a in ASSETS};benchmarks={a:[] for a in ASSETS}
    exits={a:selection[a]['expiry_ms']-DAY for a in ASSETS};max_hour=(max(exits.values())-spec['entry_ms'])//HOUR
    known_specs=adapter.known_requests()
    for hour in range(max_hour+1):
        at=spec['entry_ms']+hour*HOUR;prefix=f'h{hour:04d}-';batch={}
        for name in ('known','selected'):
            # Exactly sixteen roles, read one hour then release encoded bodies.
            for slot in full[name][hour*8:(hour+1)*8]:
                if slot['id'] in lazy[name]:batch[slot['id'].removeprefix(prefix)]=lazy[name][slot['id']]
        assembled=adapter.assemble_hour(entry_ms=spec['entry_ms'],hour=hour,selection=selection,receipts=batch)
        for asset in ASSETS:
            if at<=exits[asset]:records[asset].append(assembled['records'][asset])
            try:
                clock,_,clockmeta=adapter.decode(batch['options-time'],adapter._recipe(known_specs['options-time']),scheduled_ms=at)
                bounds=adapter._clock(clock,clockmeta);key=asset.lower()+'-index';source=known_specs[key]
                value,raw,meta=adapter.decode(batch[key],adapter._recipe(source),scheduled_ms=at)
                parsed=adapter.BATCH.parse(raw,source);adapter._fresh(parsed,meta,bounds,at)
                price=parsed['index']
            except (KeyError,ValueError,TypeError,ArithmeticError):price=None
            benchmarks[asset].append(price)
    normal_funding={a:funding.normalize(asset=a,entry_ms=spec['entry_ms'],exit_ms=exits[a],receipts={k:lazy[k] for k in ('known','daily','final')},bootstrap_receipt=lazy['bootstrap'].get('initial-futures-rules')) for a in ASSETS}
    output['evaluate_kwargs']={'entry_ms':spec['entry_ms'],'selection':selection,'records':records,'initial_rules':initial,'initial_rules_ms':initial_at,
                               'rule_vintages':vintages,'funding':normal_funding,'benchmarks':benchmarks}
    return output
