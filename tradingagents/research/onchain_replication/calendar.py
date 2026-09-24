"""UTC-only causal calendar; coverage is evidence, never permission to shrink folds."""
from datetime import datetime,timedelta
from .contracts import Fold
from .provenance import utc,canonical_bytes,digest


def stamp(value):return utc(value.isoformat() if isinstance(value,datetime) else value).isoformat().replace('+00:00','Z')


def eligible(available_at,decision_at):return utc(available_at)<=utc(decision_at)


def expected_week(decision_at):
    # At Tuesday 00:00 the week ending Monday becomes available (one-day lag).
    lagged=utc(decision_at)-timedelta(days=1)
    end=(lagged-timedelta(days=lagged.weekday())).replace(hour=0,minute=0,second=0,microsecond=0)
    return stamp(end-timedelta(days=7))


def build_folds(calendar_config,source_coverage):
    folds=[]
    for row in calendar_config['folds']:
        if not utc(row['train_start'])<utc(row['train_end'])<=utc(row['test_start'])<utc(row['test_end']):raise ValueError('invalid fold ordering')
        if row['validation_start'] is not None or row['validation_end'] is not None:raise ValueError('unregistered validation period')
        bound={k:(stamp(v) if v is not None and k!='id' else v) for k,v in row.items()}
        folds.append(Fold(**bound,member_hash=digest(canonical_bytes({'fold':bound,'coverage':source_coverage}))))
    if len({f.id for f in folds})!=len(folds):raise ValueError('duplicate folds')
    return folds
