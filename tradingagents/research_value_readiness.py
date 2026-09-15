"""Pure value_rev source-readiness proposals, not registered probe admission.

No filesystem, network, panel, portfolio or legacy-runner access. Provenance
hashes supplied here are references: caller admission must independently verify
raw bytes, economic-day semantics, requested-member completeness and timestamp
witnesses. The original charter does not contain all proposed conventions here.
"""
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import hashlib
import json
import re

SCOPE = 'readiness-only; pending registered clarification'
PROPOSAL = 'value_rev_source_clarification_20260915_unregistered'
METRICS = ('dailyFees', 'dailyRevenue')
CUTOFF = datetime(2026, 9, 4, tzinfo=timezone.utc)-timedelta(days=30)
STAGES = ('P0', 'P1', 'P2')


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()


def sha(raw):
    if not isinstance(raw, bytes):raise ValueError('immutable bytes required')
    return hashlib.sha256(raw).hexdigest()


def _hash(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):raise ValueError('SHA256 reference required')
    return value


def _utc(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?(?:Z|\+00:00)', value):
        raise ValueError('explicit UTC instant required; a date label is not clock evidence')
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def _number(value):
    if not isinstance(value, str) or len(value)>64:raise ValueError('bounded numeric literal required')
    try:number=Decimal(value)
    except InvalidOperation as exc:raise ValueError('invalid numeric literal') from exc
    if not number.is_finite() or number<0 or number and not -32<=number.adjusted()<=32:raise ValueError('finite nonnegative source value required')
    return Fraction(number)


def _fraction(value):
    return {'numerator':value.numerator,'denominator':value.denominator}


def _rows(rows):
    if not isinstance(rows, (list, tuple)):raise ValueError('explicit observation list required')
    indexed=defaultdict(list)
    for row in rows:
        if not isinstance(row, dict) or set(row)!={'protocol','metric','start_utc','end_utc','status','value','member_sha256'}:raise ValueError('observation schema')
        if not isinstance(row['protocol'], str) or not row['protocol'] or len(row['protocol'])>128 or row['metric'] not in METRICS:raise ValueError('literal protocol/metric identity')
        if row['status'] not in ('observed','missing','failed'):raise ValueError('explicit source observation state required')
        if row['status']!='observed' and row['value'] is not None:raise ValueError('missing/failed source cannot carry an observed value')
        _hash(row['member_sha256'])
        start,end=_utc(row['start_utc']),_utc(row['end_utc'])
        key=(row['metric'],row['protocol'],start.isoformat())
        value=json.loads(canonical(row))
        value['day_valid']=start.hour==start.minute==start.second==start.microsecond==0 and end==start+timedelta(days=1)
        indexed[key].append(value)
    return indexed


def compare_protocol_days(first_rows, second_rows):
    """Separate proposed fee/revenue screens; no pooled or family pass.

    Duplicate intervals are retained, not merged. Recent intervals are excluded
    by the proposed conservative economic-day END cutoff. Whole-member/source
    completeness is an independent prerequisite, not inferred from these rows.
    """
    first,second=_rows(first_rows),_rows(second_rows)
    result={'scope':SCOPE,'proposal':PROPOSAL,'economic_day_end_cutoff_utc':CUTOFF.isoformat(),
            'first_observations_sha256':sha(canonical(first_rows)),'second_observations_sha256':sha(canonical(second_rows)),
            'source_admission':False,'source_completeness_and_day_semantics':'Not proved by structured observations or hash references.',
            'metrics':{}}
    for metric in METRICS:
        keys=sorted(k for k in first.keys()|second.keys() if k[0]==metric)
        cells=[];counts=Counter({name:0 for name in ('union_keys','first_keys','second_keys','common_keys','first_only_keys','second_only_keys','first_rows','second_rows','first_observed_zeros','second_observed_zeros','first_duplicate_keys','second_duplicate_keys')});comparable=changed=0
        for key in keys:
            a,b=first.get(key,[]),second.get(key,[])
            ends={_utc(row['end_utc']).isoformat() for row in a+b}
            cell={'protocol':key[1],'start_utc':key[2],'end_utc':next(iter(ends)) if len(ends)==1 else None,
                  'first_rows':a,'second_rows':b,'relative_change':None,'changed_gt_10pct':None}
            counts['union_keys']+=1;counts['first_rows']+=len(a);counts['second_rows']+=len(b)
            if a:counts['first_keys']+=1
            if b:counts['second_keys']+=1
            if a and b:counts['common_keys']+=1
            if a and not b:counts['first_only_keys']+=1
            if b and not a:counts['second_only_keys']+=1
            if len(a)>1:counts['first_duplicate_keys']+=1
            if len(b)>1:counts['second_duplicate_keys']+=1
            invalid_values=[]
            for label,rows in (('first',a),('second',b)):
                for i,row in enumerate(rows):
                    if row['status']=='observed':
                        try:
                            if _number(row['value'])==0:counts[label+'_observed_zeros']+=1
                        except ValueError:invalid_values.append({'vintage':label,'row_index':i})
            cell['invalid_value_rows']=invalid_values
            if any(not row['day_valid'] for row in a+b):state='invalid_interval'
            elif _utc(cell['end_utc'])>CUTOFF:state='excluded_recent'
            elif len(a)>1 or len(b)>1:state='duplicate_interval'
            elif invalid_values:state='invalid_value'
            elif not a:state='second_only_addition'
            elif not b:state='first_only_deletion'
            elif a[0]['status']!='observed' or b[0]['status']!='observed':state='missing_or_failed_common'
            else:
                try:left,right=_number(a[0]['value']),_number(b[0]['value'])
                except ValueError:state='invalid_value'
                else:
                    comparable+=1
                    if left==0:
                        change=right>0;state='zero_to_positive' if change else 'zero_to_zero'
                    else:
                        change=abs(right-left)*10>left;state='positive_baseline'
                        cell['relative_change']=_fraction((right-left)/left)
                    cell['changed_gt_10pct']=change;changed+=change
            cell['classification']=state;counts[state]+=1;cells.append(cell)
        blockers=[name for name in ('invalid_interval','duplicate_interval','first_only_deletion','missing_or_failed_common','invalid_value') if counts[name]]
        if not comparable:blockers.append('no_comparable_common_observations')
        result['metrics'][metric]={'counts':dict(sorted(counts.items())),'comparable_common':comparable,
            'changed_gt_10pct':changed,'changed_share':_fraction(Fraction(changed,comparable)) if comparable else None,
            'observed_subset_within_5pct':20*changed<=comparable if comparable else None,
            'proposed_completeness_blockers':blockers,'cells':cells}
    return result


def _snapshot(value):
    if not isinstance(value, dict) or set(value)!={'snapshot_id','label','manifest_sha256','inventory_sha256','completion_evidence','request_intervals'}:raise ValueError('snapshot descriptor schema')
    if not isinstance(value['snapshot_id'],str) or not value['snapshot_id'] or not isinstance(value['label'],str):raise ValueError('snapshot identity/label')
    _hash(value['manifest_sha256']);_hash(value['inventory_sha256'])
    evidence=value['completion_evidence']
    bound=None
    if evidence is not None:
        if not isinstance(evidence,dict) or set(evidence)!={'upper_bound_utc','inventory_sha256','witness_sha256'}:raise ValueError('completion evidence schema')
        if evidence['inventory_sha256']!=value['inventory_sha256']:raise ValueError('completion witness binds another inventory')
        _hash(evidence['witness_sha256']);bound=_utc(evidence['upper_bound_utc'])
    if not isinstance(value['request_intervals'],list):raise ValueError('explicit request interval denominator')
    seen=set();starts=[]
    for interval in value['request_intervals']:
        if not isinstance(interval,dict) or set(interval)!={'request_id','start_utc','end_utc','receipt_sha256'}:raise ValueError('request interval schema')
        identity=interval['request_id']
        if not isinstance(identity,str) or not identity or identity in seen:raise ValueError('unique request identity required')
        seen.add(identity);_hash(interval['receipt_sha256'])
        start,end=_utc(interval['start_utc']),_utc(interval['end_utc'])
        if end<start or bound is not None and end>bound:raise ValueError('request/completion interval ordering')
        starts.append(start)
    return bound,starts


def snapshot_pair(first, second, *, registration_sha256, clarification_sha256):
    """Immutable proposed pair binding; date labels never determine eligibility.

    A witness hash is a caller-admitted external evidence reference. Merely
    providing a timestamp and digest here does not prove that witness truthful.
    """
    _hash(registration_sha256);_hash(clarification_sha256)
    first_end,_=_snapshot(first);second_end,second_starts=_snapshot(second)
    if first['snapshot_id']==second['snapshot_id']:raise ValueError('distinct vintages required')
    reasons=[]
    earliest=first_end+timedelta(days=14) if first_end is not None else None
    if first_end is None:reasons.append('first completion upper bound unavailable')
    if second_end is None:reasons.append('second completion bound unavailable')
    if not second_starts:reasons.append('second request intervals unavailable')
    if earliest is not None and any(start<earliest for start in second_starts):reasons.append('a second request began before first completion bound plus14days')
    return canonical({'scope':SCOPE,'proposal':PROPOSAL,'registration_id':'value_rev',
        'registration_sha256':registration_sha256,'clarification_sha256':clarification_sha256,
        'first':first,'second':second,'earliest_second_request_utc':earliest.isoformat() if earliest else None,
        'interval_readiness':'unavailable' if reasons else 'supported_under_referenced_witnesses','reasons':reasons,
        'source_admission':False})


def verify_pair(raw, expected_sha256):
    _hash(expected_sha256)
    if sha(raw)!=expected_sha256:raise ValueError('external snapshot-pair anchor mismatch')
    value=json.loads(raw)
    rebuilt=snapshot_pair(value['first'],value['second'],registration_sha256=value['registration_sha256'],clarification_sha256=value['clarification_sha256'])
    if raw!=rebuilt:raise ValueError('pair fields or canonical bytes changed')
    return value


def stage_record(stage, pair, *, expected_pair_sha256, source_code_sha256,
                 verdict, result, predecessor=None, predecessor_sha256=None,
                 occupied_stage_ids=(), terminal_seen=False):
    """Build a proposed immutable stage record, never execute or admit a stage.

    Occupancy/terminal evidence is caller-supplied. Durable exclusive intents,
    independently verified predecessor verdicts and registration are outside
    this pure helper; it cannot enforce process/file exclusivity itself.
    """
    value=verify_pair(pair,expected_pair_sha256);_hash(source_code_sha256)
    if stage not in STAGES or type(terminal_seen) is not bool:raise ValueError('P0/P1/P2 readiness stages only')
    if terminal_seen:raise ValueError('terminal stage chain cannot continue')
    if verdict is not None and type(verdict) is not bool:raise ValueError('Boolean or unavailable verdict required')
    if not isinstance(result,dict):raise ValueError('explicit structured readiness result required')
    stage_id=sha(canonical({'pair_sha256':expected_pair_sha256,'stage':stage}))
    if stage_id in occupied_stage_ids:raise ValueError('stage intent already consumed; no repeat')
    if value['interval_readiness']!='supported_under_referenced_witnesses' and verdict is not None:raise ValueError('unavailable pair cannot support completed probe readiness')
    if stage=='P0':
        if predecessor is not None or predecessor_sha256 is not None:raise ValueError('P0 has no predecessor')
    else:
        _hash(predecessor_sha256)
        if sha(predecessor)!=predecessor_sha256:raise ValueError('predecessor bytes changed')
        prior=json.loads(predecessor)
        expected=STAGES[STAGES.index(stage)-1]
        if prior.get('scope')!=SCOPE or prior.get('proposal')!=PROPOSAL or prior.get('stage')!=expected or prior.get('pair_sha256')!=expected_pair_sha256 or prior.get('source_code_sha256')!=source_code_sha256:raise ValueError('predecessor stage/pair/source mismatch')
        if prior.get('registration_sha256')!=value['registration_sha256'] or prior.get('clarification_sha256')!=value['clarification_sha256'] or prior.get('stage_id')!=sha(canonical({'pair_sha256':expected_pair_sha256,'stage':expected})):raise ValueError('predecessor registration/policy/identity mismatch')
        if prior.get('status')!='complete' or prior.get('verdict') is not True:raise ValueError('failed/unavailable predecessor blocks next stage')
    return canonical({'scope':SCOPE,'proposal':PROPOSAL,'stage':stage,'stage_id':stage_id,
        'pair_sha256':expected_pair_sha256,'registration_sha256':value['registration_sha256'],
        'clarification_sha256':value['clarification_sha256'],'source_code_sha256':source_code_sha256,
        'predecessor_sha256':predecessor_sha256,'status':'unavailable' if verdict is None else 'complete',
        'verdict':verdict,'result':result,'source_admission':False})
