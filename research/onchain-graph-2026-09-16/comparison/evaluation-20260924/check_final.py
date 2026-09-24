"""Independent outcome forensics. Never imports the production evaluator or refits."""
from __future__ import annotations
import argparse
import calendar
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import subprocess
import stat
import sys
import zipfile
import numpy as np
import pandas as pd

BASE='research/onchain-graph-2026-09-16/comparison/evaluation-20260924'
EXPERIMENT='eth-matched-direction-20260924'
GRAPH_SOURCE='87b6ac39d12a4f9a2ac1832f34f68647c52c53c8'
FROZEN='/home/malecada/Data/onchain-research/TradingAgents-onchain-fullpanel-resume2'
PYTHON='/home/malecada/master_thesis/TradingAgents-audit-fixes/.venv/bin/python'
MONTHS=['2021-12']+[f'{y}-{m:02}' for y in range(2022,2025) for m in range(1,13)]+['2025-01']
COUNTS=['events','nodes','directed_pairs','stars','dyads','triangles','overlap_nodes','nonzero_nodes']
ARMS=('M0','M1','M2')
DAY=pd.Timedelta(days=1)

def require(ok,message):
    if not ok: raise ValueError(message)

def sha(raw): return hashlib.sha256(raw).hexdigest()
def iso(value): return pd.Timestamp(value).isoformat()
def clean(value):
    if isinstance(value,dict): return {k:clean(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)): return [clean(v) for v in value]
    if isinstance(value,(pd.Timestamp,)): return value.isoformat()
    if value is pd.NaT or value is None: return None
    if isinstance(value,np.generic): value=value.item()
    if isinstance(value,float) and not math.isfinite(value): return None
    return value

def same(actual,expected,path='value'):
    actual,expected=clean(actual),clean(expected)
    if isinstance(expected,dict):
        require(isinstance(actual,dict) and set(actual)==set(expected),path+' keys differ')
        for k in expected: same(actual[k],expected[k],path+'.'+k)
    elif isinstance(expected,list):
        require(isinstance(actual,list) and len(actual)==len(expected),path+' length differs')
        for i,(a,e) in enumerate(zip(actual,expected)): same(a,e,f'{path}[{i}]')
    elif isinstance(expected,(int,float)) and not isinstance(expected,bool):
        require(isinstance(actual,(int,float)) and not isinstance(actual,bool) and math.isclose(actual,expected,rel_tol=1e-9,abs_tol=1e-11),path+' numeric mismatch')
    elif isinstance(expected,str) and re.match(r'^\d{4}-\d\d-\d\dT',expected):
        require(pd.Timestamp(actual)==pd.Timestamp(expected),path+' timestamp differs')
    else: require(actual==expected,path+' differs')

def guard_check(value,command,cwd):
    require(value.get('command')==command and value.get('cwd')==cwd,'guard command/root mismatch')
    require(value.get('phase')=='complete' and type(value.get('child_exit_code')) is int and value['child_exit_code']==0 and value.get('limit_reason') is None and value.get('cleanup_verified') is True,'guard unclean exit')
    require(all(type(value.get('memory_events',{}).get(k)) is int and value['memory_events'][k]==0 for k in ('oom','oom_kill','oom_group_kill')),'guard unknown/nonzero OOM')

def rebuild_panel(market,graph,start,end):
    """Calendar lookup implementation independent of production rolling operations."""
    def indexed(rows,delay):
        result={}
        for row in rows:
            d=pd.Timestamp(row['day']); d=d.tz_localize('UTC') if d.tzinfo is None else d.tz_convert('UTC')
            require(d==d.floor('D') and d not in result,'duplicate/nonmidnight source')
            r=dict(row); a=r['available_at']
            r['available_at']=None if a is None or pd.isna(a) else max(pd.Timestamp(a),d+delay)
            result[d]=r
        return result
    m=indexed(market,DAY+pd.Timedelta(minutes=5)); g=indexed(graph,2*DAY)
    # Match the declared population-std floating arithmetic of pinned pandas;
    # separate calendar construction avoids importing the production features.
    start_time=pd.Timestamp(start); start_time=start_time.tz_localize('UTC') if start_time.tzinfo is None else start_time
    end_time=pd.Timestamp(end); end_time=end_time.tz_localize('UTC') if end_time.tzinfo is None else end_time
    calendar_index=pd.date_range(min(min(m),min(g),start_time-32*DAY),max(max(m),max(g),end_time))
    closes=pd.Series([m[d]['close'] if d in m else np.nan for d in calendar_index],index=calendar_index)
    daily=np.log(closes/closes.shift(1))
    volatility={n:daily.rolling(n,min_periods=n).std(ddof=0) for n in (7,30)}
    means={}
    for key,source in [('quote_volume',m),('events',g),('nodes',g),('directed_pairs',g)]:
        series=pd.Series([float(source[d][key]) if d in source else np.nan for d in calendar_index],index=calendar_index)
        means[key]=series.rolling(7,min_periods=7).mean()
    rows=[]
    for d in pd.date_range(start,end,inclusive='left',tz='UTC'):
        s=d-2*DAY
        row=dict(decision_at=d,label_start=d,label_end=d+DAY,y=None)
        if d in m and d+DAY in m: row['y']=int(m[d+DAY]['open']>m[d]['open'])
        def feature(name,source,width,calculate):
            window=[source.get(s-i*DAY) for i in range(width-1,-1,-1)]
            value=None; clock=None
            if all(r is not None for r in window):
                value=calculate(window)
                if all(r['available_at'] is not None for r in window): clock=max(r['available_at'] for r in window)
            row[name]=clean(value); row[name+'__available_at']=clock
        for n in (1,7,30):
            feature(f'return_{n}',m,n+1,lambda w: np.log(w[-1]['close']/w[0]['close']))
        for n in (7,30):
            feature(f'volatility_{n}',m,n+1,lambda w,n=n: float(volatility[n].loc[s]))
        feature('log_quote_volume',m,1,lambda w: np.log1p(w[-1]['quote_volume']))
        feature('relative_quote_volume_7',m,7,lambda w: np.log((1+w[-1]['quote_volume'])/(1+means['quote_volume'].loc[s])))
        for k in ('events','nodes','directed_pairs'):
            feature(k+'_log_count',g,1,lambda w,k=k: np.log1p(w[-1][k]))
            feature(k+'_relative_7',g,7,lambda w,k=k: np.log((1+w[-1][k])/(1+means[k].loc[s])))
        for k in ('stars','dyads','triangles'):
            feature(k+'_log_count',g,1,lambda w,k=k: np.log1p(w[-1][k]))
            feature(k+'_per_event',g,1,lambda w,k=k: w[-1][k]/(1+w[-1]['events']))
        feature('nonzero_fraction',g,1,lambda w: w[-1]['nonzero_nodes']/w[-1]['overlap_nodes'] if w[-1]['overlap_nodes'] else None)
        rows.append(row)
    return clean(rows)

def admission(rows):
    result=[]
    for r in rows:
        reasons=[]
        for k in r:
            if not k.endswith('__available_at'): continue
            name=k[:-14]; clock=r[k]
            if clock is not None and pd.Timestamp(clock)>pd.Timestamp(r['decision_at']): reasons.append('late:'+name)
            if r[name] is None or clock is None: reasons.append('missing:'+name)
        if r['y'] is None: reasons.append('missing:y')
        result.append(dict(decision_at=r['decision_at'],exclusion_reasons=reasons,included=not reasons))
    return result

def metrics(y,p):
    y=np.asarray(y,float); p=np.asarray(p,float)
    require(y.ndim==1 and len(y)>0 and p.shape==y.shape and np.isin(y,[0,1]).all() and np.isfinite(p).all() and ((p>=0)&(p<=1)).all(),'invalid metric inputs')
    pred=p>=.5; q=np.clip(p,1e-15,1-1e-15)
    recalls=[np.mean(pred[y==k]==k) for k in (0,1) if np.any(y==k)]
    return dict(n=len(y),accuracy=float(np.mean(pred==y)),balanced_accuracy=float(np.mean(recalls)) if len(recalls)==2 else None,brier=float(np.mean((p-y)**2)),log_loss=float(np.mean(-y*np.log(q)-(1-y)*np.log1p(-q))))

def decode_month(month,raw,checksum):
    name=f'ETHUSDT-1d-{month}.zip'
    match=re.fullmatch(r'([a-fA-F0-9]{64})[ \t]+\*?'+re.escape(name)+r'[\r\n]*',checksum.decode('ascii'))
    require(match is not None and match[1].lower()==sha(raw),'archive checksum/name mismatch')
    require(len(raw)<=2**20,'oversized ZIP')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries=z.infolist(); require(len(entries)==1,'ZIP member denominator')
        e=entries[0]
        mode=e.external_attr>>16
        require(not stat.S_ISLNK(mode) and stat.S_IFMT(mode) in (0,stat.S_IFREG) and e.compress_type in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED),'unsafe ZIP type')
        require(e.filename==name[:-4]+'.csv' and not e.is_dir() and not e.flag_bits&1 and 0<e.file_size<=2**20,'unsafe ZIP member')
        body=z.read(e)
    year,mon=map(int,month.split('-')); unit=1000000 if year>=2025 else 1000
    start=pd.Timestamp(month+'-01',tz='UTC'); rows=list(csv.reader(io.StringIO(body.decode()),strict=True))
    require(len(rows)==calendar.monthrange(year,mon)[1],'monthly row denominator')
    result=[]
    for i,r in enumerate(rows):
        day=start+i*DAY; stamp=int(day.timestamp())*unit
        require(len(r)==12 and r[0].isdigit() and r[6].isdigit() and int(r[0])==stamp and int(r[6])==stamp+86400*unit-1,'archive timestamp/shape mismatch')
        if day>pd.Timestamp('2025-01-01',tz='UTC'): continue
        o,h,l,c,v,q=[float(r[j]) for j in (1,2,3,4,5,7)]
        require(all(math.isfinite(x) and x>0 for x in (o,h,l,c)) and l<=min(o,c)<=max(o,c)<=h,'invalid OHLC')
        require(all(math.isfinite(x) and x>=0 for x in (v,q)),'invalid volume')
        result.append(dict(day=iso(day),open=o,close=c,quote_volume=q,available_at=iso(day+DAY+pd.Timedelta(minutes=5))))
    return result

def unpack(stored,meta):
    import zstandard
    require(meta['codec']=='zstd' and type(meta['raw_bytes']) is int and 0<meta['raw_bytes']<=2**20,'blob metadata bounds')
    require(len(stored)==meta['stored_bytes'] and sha(stored)==meta['stored_sha256'],'stored blob mismatch')
    require(zstandard.frame_content_size(stored)==meta['raw_bytes'],'zstd frame size')
    raw=zstandard.ZstdDecompressor().decompress(stored,max_output_size=2**20,allow_extra_data=False)
    require(len(raw)==meta['raw_bytes'] and sha(raw)==meta['raw_sha256'],'raw blob mismatch')
    return raw

def graph_rows(panel,full=True):
    require(panel.get('global_uniqueness_admitted') is True,'graph global admission')
    if full: same([r['day'] for r in panel['days']],[d.strftime('%Y-%m-%d') for d in pd.date_range('2022-01-01','2024-12-31')])
    rows=[]; excluded=[]
    for r in panel['days']:
        if r.get('source_admitted') is not True or r.get('graph_admitted') is not True:
            require(bool(r.get('reason')),'graph exclusion reason missing'); excluded.append(dict(day=r['day'],reason=r['reason'])); continue
        require(r['source_status']==r['graph_status']=='complete','graph status')
        counts={k:r[k] for k in COUNTS}; local=r['local40']; roles=local['local40_sums']
        require(all(type(v) is int and 0<=v<2**53 for v in counts.values()) and len(roles)==40 and all(type(v) is int and 0<=v<2**53 for v in roles),'graph exact counts')
        require(sum(roles[:24])==counts['stars'] and sum(roles[24:32])==2*counts['dyads'] and sum(roles[32:])==3*counts['triangles'],'role conservation')
        require(local['unique_occurrences']==sum(counts[k] for k in ('stars','dyads','triangles')) and local['overlap_node_count']==counts['overlap_nodes'] and local['nonzero_nodes']==counts['nonzero_nodes'],'local aggregates')
        require(counts['nodes']<=counts['overlap_nodes'] and counts['nonzero_nodes']<=counts['overlap_nodes'] and counts['directed_pairs']<=counts['events'],'graph denominator')
        require(counts['events'] or all(counts[k]==0 for k in ('nodes','directed_pairs','stars','dyads','triangles')),'empty graph inconsistency')
        d=pd.Timestamp(r['day'],tz='UTC'); clock=d+2*DAY
        if r.get('available_at') is not None: clock=max(clock,pd.Timestamp(r['available_at']))
        rows.append(dict(day=iso(d),available_at=iso(clock),**counts))
    if full: same([r['day'] for r in excluded],['2022-01-01','2024-12-31'])
    return rows,excluded

def bootstrap(rows,block,resamples,seed):
    dates=pd.DatetimeIndex([r['decision_at'] for r in rows]); n=len(rows)
    require(n>=block and dates.equals(pd.date_range(dates[0],periods=n,freq='D')),'bootstrap requires consecutive days')
    rng=np.random.default_rng(seed)
    # Draw order is scalar-equivalent to the frozen non-circular block algorithm.
    starts=rng.integers(n-block+1,size=(resamples,math.ceil(n/block)))
    indices=(starts[:,:,None]+np.arange(block)).reshape(resamples,-1)[:,:n]
    y=np.array([r['y'] for r in rows]); losses={}
    for arm in ARMS:
        p=np.array([r[arm+'_probability'] for r in rows]); metrics(y,p); q=np.clip(p,1e-15,1-1e-15)
        losses[arm]={'brier':(p-y)**2,'log_loss':-y*np.log(q)-(1-y)*np.log1p(-q)}
    daily=[dict(decision_at=r['decision_at'],fold=r['fold']) for r in rows]; summaries={}
    for new,old in (('M1','M0'),('M2','M1')):
        for loss in ('brier','log_loss'):
            key=f'{new}-{old}:{loss}'; diff=losses[new][loss]-losses[old][loss]
            for r,v in zip(daily,diff): r[key]=float(v)
            summaries[key]=dict(mean=float(diff.mean()),ci95=np.quantile(diff[indices].mean(axis=1),[.025,.975]).tolist())
    return dict(daily=daily,summaries=summaries,block_days=block,resamples=resamples,seed=seed,n=n)

def verify_predictions(panel,config,fits,predictions,attempts):
    import lightgbm as lgb
    require(lgb.__version__==config['model'].get('version',lgb.__version__),'LightGBM version')
    admitted=admission(panel); included={r['decision_at'] for r in admitted if r['included']}
    require(len(attempts)==len(config['folds']),'attempt denominator')
    lookup={}; counts=[]; monthly=[]; fold_metrics=[]; expected_predictions=[]
    for fit in fits:
        key=(fit['fold'],fit['arm']); require(key not in lookup,'duplicate saved fit'); lookup[key]=fit
    seen=set()
    for fold,attempt in zip(config['folds'],attempts):
        ident=fold['id']; start=pd.Timestamp(fold['start']); end=pd.Timestamp(fold['end']); cutoff=start-pd.Timedelta(config['purge_gap'])
        require(attempt['fold']==ident and attempt['status'] in ('complete','failed'),'attempt identity/status')
        tc=[r for r in panel if pd.Timestamp(r['decision_at'])<start and pd.Timestamp(r['label_end'])<=cutoff]
        vc=[r for r in panel if start<=pd.Timestamp(r['decision_at'])<end]
        train=[r for r in tc if r['decision_at'] in included]; test=[r for r in vc if r['decision_at'] in included]
        group=[r for r in predictions if r['fold']==ident]
        if attempt['status']=='failed': require(bool(attempt['error']) and not group,'failed fold predictions/reason')
        else:
            require(attempt['error'] is None and test and len({r['y'] for r in train})==2,'completed fold invalid admission')
            same([r['decision_at'] for r in group],[r['decision_at'] for r in test],'test membership')
        seen_gap=False
        for arm in ARMS:
            fit=lookup.get((ident,arm))
            if fit is None:
                require(attempt['status']=='failed','successful fold missing fit'); seen_gap=True; continue
            require(not seen_gap,'partial fits must retain completed arm prefix'); seen.add((ident,arm))
            same(fit['params'],config['model']['params'],'fit parameters')
            same(fit['train_days'],[r['decision_at'] for r in train],'train membership')
            same(fit['test_days'],[r['decision_at'] for r in test],'fit test membership')
            booster=lgb.Booster(model_str=fit['model_text'])
            require(booster.dump_model()['objective'].startswith('binary') and booster.num_model_per_iteration()==1,'saved objective differs')
            same(booster.feature_name(),config['feature_sets'][arm],'Booster feature order')
            require(booster.num_trees()<=config['model']['params']['n_estimators'] and booster.num_trees()>0,'tree count')
            aliases={'n_estimators':'num_iterations','n_jobs':'num_threads','random_state':'seed','reg_lambda':'lambda_l2','min_child_samples':'min_data_in_leaf'}
            for k,v in config['model']['params'].items():
                match=re.search(r'^\['+re.escape(aliases.get(k,k))+r': (.*?)\]$',fit['model_text'],re.M)
                require(match is not None,'saved parameter missing: '+k)
                wanted=str(int(v)) if isinstance(v,bool) else str(v)
                require(match[1]==wanted or (isinstance(v,(int,float)) and float(match[1])==v),'saved parameter differs: '+k)
            if test:
                replay=booster.predict(pd.DataFrame(test)[config['feature_sets'][arm]],num_threads=2)
                metrics([r['y'] for r in test],replay)
                if group: same([r[arm+'_probability'] for r in group],replay.tolist(),'probability replay')
        if group:
            majority=float(sum(r['y'] for r in train)/len(train)>.5)
            for r,t in zip(group,test):
                same({k:r[k] for k in ('decision_at','label_start','label_end','y')},{k:t[k] for k in ('decision_at','label_start','label_end','y')})
                same(r['majority_probability'],majority)
            expected_predictions.extend(group)
            counts.append(dict(fold=ident,train_candidates=len(tc),train_included=len(train),test_candidates=len(vc),test_included=len(test),train_label_cutoff=iso(cutoff)))
            for arm in (*ARMS,'majority'): fold_metrics.append(dict(fold=ident,model=arm,**metrics([r['y'] for r in group],[r[arm+'_probability'] for r in group])))
            difference=metrics([r['y'] for r in group],[r['M2_probability'] for r in group])['log_loss']-metrics([r['y'] for r in group],[r['M1_probability'] for r in group])['log_loss']
        else: difference=None
        monthly.append(dict(**attempt,n=len(group),M2_minus_M1_log_loss=difference))
    require(seen==set(lookup),'unknown fit identity'); same(predictions,expected_predictions,'prediction order/denominator')
    pooled={arm:metrics([r['y'] for r in predictions],[r[arm+'_probability'] for r in predictions]) for arm in (*ARMS,'majority')} if predictions else {}
    b=config['bootstrap']; required=[iso(d) for d in pd.date_range(b['required_start'],b['required_end_exclusive'],inclusive='left')]
    actual=[r['decision_at'] for r in predictions]; missing=[d for d in required if pd.Timestamp(d) not in {pd.Timestamp(x) for x in actual}]
    inference=dict(status='unavailable',reason='all 366 daily 2024 predictions required',missing_dates=missing); screening=dict(status='unavailable',supported=None)
    if [pd.Timestamp(d) for d in actual]==[pd.Timestamp(d) for d in required] and all(a['status']=='complete' for a in attempts):
        paired=bootstrap(predictions,b['block_days'],b['resamples'],b['seed']); inference=dict(status='available',result=paired,missing_dates=[])
        negative=sum(r['M2_minus_M1_log_loss']<0 for r in monthly); rule=config['screening']
        screening=dict(status='available',supported=bool(paired['summaries'][rule['primary']]['ci95'][1]<rule['ci95_upper_strictly_below'] and negative>=rule['monthly_negative_minimum']),negative_months=negative)
    return dict(admission=admitted,attempts=attempts,monthly=monthly,pooled_metrics=pooled,fold_metrics=fold_metrics,counts=counts,inference=inference,screening=screening)

def reconstruct_inputs(inputs):
    """Decode only bytes already checked against the registered lifecycle inputs."""
    panel=json.loads(inputs['graph_panel']); terminal=json.loads(inputs['graph_terminal']); review=json.loads(inputs['graph_review'])
    require(review.get('passed') is True and review.get('passing_full_panel') is True,'full graph review required')
    require(terminal.get('status')=='complete' and terminal.get('experiment_id')=='eth-full-history-feature-panel-resume2-20260922' and terminal.get('source')==review.get('source')==GRAPH_SOURCE,'graph terminal/source identity')
    require(review['terminal_sha256']==sha(inputs['graph_terminal']) and terminal['output_sha256']['panel.json']==review['output_sha256']['panel.json']==sha(inputs['graph_panel']),'graph report hashes')
    graphbase=FROZEN+'/research/onchain-graph-2026-09-16/fullpanel_resume2'
    graphguard=json.loads(inputs['graph_review_guard'])
    require(graphguard.get('memory_high_bytes')==graphguard.get('memory_max_bytes')==6*2**30 and graphguard.get('memory_swap_max_bytes')==2**29 and graphguard.get('cpus')==[0,1],'graph guard resource profile')
    require(all(type(graphguard.get('memory_events',{}).get(k)) is int and graphguard['memory_events'][k]==0 for k in ('high','max')),'graph review memory events')
    guard_check(graphguard,[PYTHON,'-B',graphbase+'/check_final.py','--root',FROZEN,'--source',GRAPH_SOURCE,'--report',graphbase+'/independent-report.json'],FROZEN)
    require(all(r.get('source_admitted') is True and r.get('source_status')=='complete' for r in panel['days']),'graph source admission')
    graph,excluded=graph_rows(panel)
    manifest=json.loads(inputs['spot_manifest']); capture=json.loads(inputs['spot_capture_review'])
    require(capture['spot_stage']['manifest_sha256']==sha(inputs['spot_manifest']) and capture['spot_stage']['independent_archive_check']=='passed' and capture['spot_stage']['months']==38 and capture['final_closure']['status']=='verified' and capture['final_closure']['complete_spot_months']==38,'spot review binding')
    require(manifest['status']=='complete' and manifest['months']==MONTHS and manifest['requests']==76 and manifest['complete_months']==38 and (manifest['market'],manifest['symbol'],manifest['interval'])==('spot','ETHUSDT','1d'),'spot manifest identity')
    require([c['month'] for c in manifest['cells']]==MONTHS,'spot monthly cells')
    artifacts={a['path']:a for a in manifest['artifacts']}; require(len(artifacts)==len(manifest['artifacts']),'duplicate spot artifacts')
    market=[]; total=0
    for month,cell in zip(MONTHS,manifest['cells']):
        raw=inputs[f'spot_{month}_metadata']; meta=json.loads(raw); entry=artifacts[f'month-{month}.json']
        require(meta==cell and entry['bytes']==len(raw) and entry['sha256']==sha(raw) and meta['status']=='complete' and meta['network_requests']==2 and meta['acquisition_attempted'] is True and len(meta['receipts'])==2,'spot month metadata binding')
        decoded=[]
        for i,kind in enumerate(('zip','checksum')):
            blob=meta[kind+'_blob']; receipt=meta['receipts'][i]; stored=inputs[f'spot_{month}_{kind}']; entry=artifacts[blob['path']]
            url='https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1d/'+f'ETHUSDT-1d-{month}.zip'+('.CHECKSUM' if kind=='checksum' else '')
            require(meta[kind+'_url']==url and receipt['status']==200 and receipt.get('error') is None and receipt['blob']==blob and receipt['bytes']==blob['raw_bytes'] and receipt['sha256']==blob['raw_sha256']==meta[kind+'_sha256'],'spot receipt binding')
            require(entry['bytes']==len(stored) and entry['sha256']==sha(stored),'spot artifact binding')
            decoded.append(unpack(stored,blob)); total+=len(decoded[-1])
        market.extend(decode_month(month,*decoded))
        with zipfile.ZipFile(io.BytesIO(decoded[0])) as archive:
            member=archive.infolist()[0]; csv_raw=archive.read(member)
        unit=1000000 if month>='2025-01' else 1000; start=pd.Timestamp(month+'-01',tz='UTC'); n=calendar.monthrange(start.year,start.month)[1]
        expected=dict(zip_sha256=sha(decoded[0]),checksum_sha256=sha(decoded[1]),csv_member=member.filename,csv_bytes=len(csv_raw),csv_sha256=sha(csv_raw),rows=n,fields=12,timestamp_unit='us' if unit==1000000 else 'ms',first_open_timestamp=int(start.timestamp())*unit,last_open_timestamp=int((start+(n-1)*DAY).timestamp())*unit,price_fields_parsed=False)
        for k,v in expected.items(): same(meta[k],v,'spot metadata.'+k)
    require(total==manifest['raw_bytes'] and total<=16*2**20,'spot raw byte total')
    same([r['day'] for r in market],[iso(d) for d in pd.date_range('2021-12-01','2025-01-01',tz='UTC')],'market full calendar')
    return market,graph,excluded

def check_cells(summary,terminal,evaluation,config,market,graph,panel,fits,predictions):
    cells=[dict(id='spot-'+m,status='complete') for m in MONTHS]+[dict(id='graph-panel',status='complete')]
    for a in evaluation['attempts']:
        for arm in ARMS:
            c=dict(id=f'fold-{a["fold"]}-{arm}',status='complete' if a['status']=='complete' else 'unavailable')
            if c['status']=='unavailable': c['reason']=a['error']
            cells.append(c)
    for name in ('inference','screening'):
        c=dict(id=name,status='complete' if evaluation[name]['status']=='available' else 'unavailable')
        if c['status']=='unavailable': c['reason']=evaluation[name].get('reason') or evaluation['inference'].get('reason') or 'complete pooled coverage required'
        cells.append(c)
    same(summary['cells'],cells); same(terminal['cells'],cells)
    for k,v in dict(cell_count=77,unavailable_count=sum(c['status']=='unavailable' for c in cells),market_rows=len(market),graph_rows=len(graph),panel_rows=len(panel),fit_count=len(fits),prediction_rows=len(predictions),screening=evaluation['screening'],error=None).items(): same(summary[k],v,'summary.'+k)
    require(bool(summary.get('qualification')),'summary qualification missing')

def check_saved_evaluation(computed,saved):
    """Validate descriptives while preserving a recorded operational inference failure."""
    failed=saved.get('inference',{}).get('error_type')=='inference_failed'
    if failed:
        require(computed['inference']['status']=='available','inference failure without full prediction coverage')
        require(set(saved['inference'])=={'status','reason','missing_dates','error_type'} and saved['inference']['status']=='unavailable' and isinstance(saved['inference']['reason'],str) and bool(saved['inference']['reason']) and saved['inference']['missing_dates']==[],'invalid operational inference failure')
        same(saved['screening'],dict(status='unavailable',supported=None))
        expected=dict(computed,inference=saved['inference'],screening=saved['screening'])
        same(saved,expected,'saved operationally failed evaluation')
    else: same(saved,computed,'evaluation')
    return failed

def compute_evidence(value,command,cwd):
    """Wrong identity is corruption; unknown/failed resource exit is failure-only."""
    if value is None: return dict(clean=False,reason='compute guard final receipt missing or empty',receipt=None)
    require(value.get('command')==command and value.get('cwd')==cwd,'guard command/root mismatch')
    try: guard_check(value,command,cwd)
    except ValueError as exc: return dict(clean=False,reason=str(exc),receipt=value)
    return dict(clean=True,reason=None,receipt=value)

def checkpoint_evidence(directory,source,claim_digest,final_fits=None,*,allow_pending=False):
    """Bind immutable fit receipts without treating partial evidence as outcomes."""
    directory=Path(directory)
    require(not directory.is_symlink(),'checkpoint directory symlink')
    if not directory.exists():
        require(final_fits is None or final_fits==[],'missing saved fit checkpoints')
        return dict(count=0,present=False,files=[],pending_files=[],saved_models_replayed=False)
    require(directory.is_dir(),'checkpoint directory type')
    records=[]; files=[]; pending=[]; total=0
    for path in sorted(directory.iterdir()):
        require(path.is_file() and not path.is_symlink(),'checkpoint member type')
        total+=path.stat().st_size; require(total<=64*2**20,'checkpoint byte bound')
        raw=path.read_bytes()
        if re.fullmatch(r'\.pending-[0-9a-f]{32}',path.name):
            require(allow_pending,'unpublished checkpoint in completed run')
            pending.append(dict(path=path.name,bytes=len(raw),sha256=sha(raw))); continue
        record=json.loads(raw)
        require(set(record)=={'schema_version','experiment_id','source','claim_sha256','sequence','fit'} and record['schema_version']==1 and record['experiment_id']==EXPERIMENT,'checkpoint envelope')
        require(record['source']==source and record['claim_sha256']==claim_digest,'checkpoint claim/source binding')
        require(type(record['sequence']) is int and record['sequence']>=0,'checkpoint sequence type')
        fit=record['fit']
        require(set(fit)=={'fold','arm','train_days','test_days','params','model_text'},'checkpoint fit schema')
        require(re.fullmatch(r'2024-(0[1-9]|1[0-2])',fit['fold']) and fit['arm'] in ARMS and path.name==f"{fit['fold']}-{fit['arm']}.json",'checkpoint filename/identity')
        require(isinstance(fit['train_days'],list) and isinstance(fit['test_days'],list) and isinstance(fit['params'],dict) and isinstance(fit['model_text'],str) and fit['model_text'],'checkpoint payload shape')
        records.append(record); files.append(dict(path=path.name,bytes=len(raw),sha256=sha(raw),sequence=record['sequence'],fold=fit['fold'],arm=fit['arm']))
    records.sort(key=lambda r:r['sequence']); files.sort(key=lambda r:r['sequence'])
    require([r['sequence'] for r in records]==list(range(len(records))),'checkpoint sequence gap/duplicate')
    keys=[(r['fit']['fold'],r['fit']['arm']) for r in records]
    require(keys==sorted(set(keys)),'checkpoint callback chronology/duplicates')
    if final_fits is not None: same([r['fit'] for r in records],final_fits,'checkpoint/final fits')
    return dict(count=len(records),present=True,files=files,pending_files=pending,saved_models_replayed=False)

def main():
    parser=argparse.ArgumentParser()
    for name in ('root','source','report'): parser.add_argument('--'+name,required=True)
    args=parser.parse_args(); root=Path(args.root).resolve(); here=root/BASE; run=root/'research_runs'/EXPERIMENT; report=Path(args.report)
    require(report.is_absolute() and report.parent.resolve()==here and not report.exists() and not report.is_symlink(),'exclusive report path required')
    sys.path.insert(0,str(root))
    from tradingagents.research.verify import verify_claim,verify_run
    claim=verify_claim(run); structural=verify_run(run)
    require(claim['source']==args.source==subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'current source mismatch')
    require(claim['experiment_id']==EXPERIMENT and claim['registration']==BASE+'/gates.json','claim identity')
    for path,digest in claim['experiment']['source_files'].items(): require(sha((root/path).read_bytes())==digest,'working source mismatch: '+path)
    require(claim['experiment']['source_files'].get(BASE+'/check_final.py')==sha(Path(__file__).read_bytes()),'checker source not bound')
    import importlib.util
    spec=importlib.util.spec_from_file_location('matched_review_infrastructure',here/'admission.py'); infrastructure=importlib.util.module_from_spec(spec); spec.loader.exec_module(infrastructure)
    infrastructure.assert_guard(root,args.source,review=True)
    def no_network(event,args):
        if event.startswith('socket.'): raise RuntimeError('offline independent review')
    sys.addaudithook(no_network)
    terminal_path=run/('complete.json' if structural['status']=='complete' else 'failed.json'); terminal_raw=terminal_path.read_bytes(); terminal=json.loads(terminal_raw)
    guard_path=here/'resources/compute/final.json'
    guard_raw=guard_path.read_bytes() if guard_path.is_file() else b''
    resource=compute_evidence(json.loads(guard_raw) if guard_raw else None,[PYTHON,'-B',str(here/'run.py'),'--source',args.source],str(root))
    inputs={}
    for name,ref in claim['inputs'].items():
        path=root/ref['path']; require(not path.is_symlink(),'symlink input'); raw=path.read_bytes(); require(sha(raw)==ref['sha256'],'registered input mismatch: '+name); inputs[name]=raw
    fit_path=run/'outputs/fits.json'
    final_fits=json.loads(fit_path.read_bytes())['fits'] if fit_path.is_file() else None
    checkpoints=checkpoint_evidence(run/'fit-checkpoints',args.source,sha((run/'claim.json').read_bytes()),final_fits=final_fits,allow_pending=structural['status']!='complete' or not resource['clean'])
    result=dict(passed=True,passing_complete_comparison=False,failed_run_evidence_only=True,numerical_validation_performed=False)
    result.update(execution_resource=resource,fit_checkpoints=checkpoints,partial_fit_count=checkpoints['count'])
    if structural['status']=='complete' and resource['clean']:
        config=json.loads(inputs['config']); same(config,json.loads((here.parent/'config.json').read_bytes()))
        outputs={p.name:json.loads(p.read_bytes()) for p in (run/'outputs').iterdir()}
        market,graph,exclusions=reconstruct_inputs(inputs)
        same(outputs['market.json'],dict(rows=market)); same(outputs['graph.json'],dict(rows=graph,exclusions=exclusions))
        panel=rebuild_panel(market,graph,config['decisions']['start'],config['decisions']['end_exclusive'])
        same(outputs['panel.json'],dict(rows=panel,feature_sets=config['feature_sets']))
        admission_record=outputs['inputs-admission.json']; require(admission_record['graph_source']==GRAPH_SOURCE and admission_record['historical_availability_verified'] is False and admission_record['availability_basis']=='protocol_assumption','input admission qualification')
        same(admission_record['graph_exclusions'],exclusions)
        names=('config','protocol','history','approval','amendment','graph_panel','graph_terminal','graph_review','graph_review_guard','spot_capture_review','spot_manifest')
        same(admission_record['source_sha256'],{n:sha(inputs[n]) for n in names})
        evaluation=outputs['evaluation.json']; predictions=outputs['predictions.json']['rows']; fits=outputs['fits.json']['fits']
        if evaluation.get('error'):
            require(not predictions and evaluation['inference']['status']==evaluation['screening']['status']=='unavailable','fatal outcome falsely available')
            verify_predictions(panel,config,fits,[],evaluation['attempts'])
            same(evaluation['admission'],admission(panel))
            require(all(a['status']=='failed' and a['error']==evaluation['error'] for a in evaluation['attempts']),'fatal fold records')
            require(evaluation['monthly']==evaluation['fold_metrics']==evaluation['counts']==[] and evaluation['pooled_metrics']=={},'fatal evaluator retained values')
            fallback_summary=dict(outputs['summary.json']); require(fallback_summary['error']==evaluation['error'],'fatal summary error')
            fallback_summary['error']=None
            check_cells(fallback_summary,terminal,evaluation,config,market,graph,panel,fits,[])
            result['failure_reason']=evaluation['error']; result['partial_fit_count']=len(fits)
        else:
            expected=verify_predictions(panel,config,fits,predictions,evaluation['attempts'])
            inference_failed=check_saved_evaluation(expected,evaluation)
            check_cells(outputs['summary.json'],terminal,evaluation,config,market,graph,panel,fits,predictions)
            full=evaluation['inference']['status']=='available' and not inference_failed
            result.update(passing_complete_comparison=full,failed_run_evidence_only=inference_failed,numerical_validation_performed=True,prediction_rows=len(predictions),fit_count=len(fits),screening=evaluation['screening'],inference_status=evaluation['inference']['status'])
            if inference_failed:
                result.update(failure_reason=evaluation['inference']['reason'],operational_failure_reproduced=False,inference_qualification='Retained predictions and descriptive scores verified; operational failure cause not independently reproduced. Original inference and screening remain unavailable. No substitute bootstrap screening published.')
    else:
        result['failure_reason']=resource['reason'] or 'lifecycle terminal is failed'
    require(checkpoint_evidence(run/'fit-checkpoints',args.source,sha((run/'claim.json').read_bytes()),final_fits=final_fits,allow_pending=structural['status']!='complete' or not resource['clean'])==checkpoints,'checkpoints changed during review')
    require((guard_path.read_bytes() if guard_path.is_file() else b'')==guard_raw,'compute guard changed during review')
    require(terminal_path.read_bytes()==terminal_raw,'terminal changed during review')
    verify_run(run)
    result['passed']=not result['failed_run_evidence_only']
    result['evidence_verification_passed']=True
    result.update(reviewed_at=pd.Timestamp.now(tz='UTC').isoformat(),source=args.source,structural_verification=structural,claim_sha256=sha((run/'claim.json').read_bytes()),terminal_sha256=sha(terminal_raw),output_sha256=terminal['output_sha256'],reviewer_script_sha256=sha(Path(__file__).read_bytes()),execution_resource_sha256=sha(guard_raw) if guard_raw else None,historical_availability_verified=False,financial_admission=False,new_network_requests=0,qualification='Independent input/feature/clock/mask, saved-model replay and inference consistency checks. Saved Booster replay does not independently prove the historical training operation. Retrospective assumed availability; no PnL, execution, strategy validation or fresh confirmation.')
    with report.open('x') as stream: json.dump(clean(result),stream,sort_keys=True,indent=2,allow_nan=False); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    print(json.dumps({k:result[k] for k in ('passed','passing_complete_comparison','failed_run_evidence_only')}))

if __name__=='__main__': main()
