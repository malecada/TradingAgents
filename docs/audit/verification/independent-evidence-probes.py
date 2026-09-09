"""Synthetic review only. No market/forecast/result store is opened."""
import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
from scripts import audit_correction_2026_09_09 as correction
from tradingagents.predlab import registry,evidence,runner

out={}
with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    day=pd.date_range('2021-01-01',periods=40,tz='UTC')
    hour=pd.date_range('2021-01-01',periods=40,freq='h',tz='UTC')
    def fake_read(path,hashes):
        ix=hour if '1h' in str(path) else day
        if 'forecasts' in str(path):
            return pd.DataFrame({'pred': .8 if '1h' in str(path) else .04/365},index=ix)
        return pd.DataFrame({'ret':np.tile([.01,-.002],20),'rv':.04/365},index=ix)
    original={'S2':{k:{} for k in ('harq','har_levels','naive20')},
              'S3':{f's3_t{t}_h{s}':{} for t in (.5,.52) for s in (1,24)}}
    with patch.object(correction,'read_development',side_effect=fake_read):
        try:
            result=correction.strategies(root,root,{},original)
            out['truncated_strategy_clock']={'accepted':True,'s2_last':result['S2']['harq']['last'],
                                             's3_n_hours':result['S3']['s3_t0.5_h1']['n_hours']}
        except Exception as exc:
            out['truncated_strategy_clock']={'accepted':False,'error':str(exc)}

with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    (root/'data/predlab').mkdir(parents=True)
    (root/'docs/audit').mkdir(parents=True)
    gate={'fixture':{'development_window':['2024-01-01','2024-12-31']}}
    (root/'data/predlab/gates.json').write_text(json.dumps(gate))
    policy=root/'docs/audit/corrections.jsonl'
    policy.write_text(json.dumps({'id':'stop','claim':'fixture','rerun_requires_new_registration':True})+'\n')
    def git(*args):
        return subprocess.run(['git',*args],cwd=root,check=True,capture_output=True,text=True)
    git('init','-q');git('config','user.name','Synthetic audit');git('config','user.email','audit@example.invalid')
    git('add','.');git('commit','-qm','Synthetic fixture')
    policy.write_text('')
    original_resolve=evidence.resolve
    with patch.object(registry,'PROJECT_ROOT',root),patch.object(registry,'_data_root',return_value=root/'data'),patch.object(evidence,'resolve',side_effect=lambda claim,*args:original_resolve(claim,args[0] if args else policy)):
        try:
            result=registry.preflight('fixture',('2024-01-01','2024-12-31'))
            out['dirty_correction_policy']={'accepted':True,'evidence_policy':result['evidence_policy']}
        except Exception as exc:
            out['dirty_correction_policy']={'accepted':False,'error':str(exc)}

registered=json.loads(Path('data/predlab/gates.json').read_text())['predlab_p2_ml']
with tempfile.TemporaryDirectory() as td,patch.object(correction,'read_development',side_effect=FileNotFoundError('Synthetic missing source')):
    try:
        result=correction.saved_enet(Path(td),Path(td),{},registered)
        out['missing_enet_source']={'returns_cell_statuses':True,'n_statuses':len(result)}
    except Exception as exc:
        out['missing_enet_source']={'returns_cell_statuses':False,'error':str(exc)}

class Base:
    name='base'
    def fit(self,*args): pass
    def predict(self,*args): return 0.
class Nested(Base):
    name='candidate'
    nested=True
    def predict(self,*args): return .05
idx=pd.date_range('2024-01-01',periods=120,tz='UTC')
series=pd.DataFrame({'y':.1+.03*np.sin(np.arange(120))},index=idx)
cell={'cell':'fixture','target':'T1_ret','strong_baseline':'base','horizon_bars':1,
      'min_train':60,'refit_every':1,'loss':'se','nested_models':{'candidate':'base'},
      'registered_nested_test':'clark_west'}
rows=runner.run_cell(cell,series,[Base(),Nested()],'fixture','t2',dry=True)
out['nested_model_metadata']={'exported': 'nested' in rows.columns,
                              'model_declares_nested':Nested.nested,
                              'nested': bool(rows.set_index('model').loc['candidate','nested']),
                              'primary_test': rows.set_index('model').loc['candidate','primary_test'],
                              'inference_eligible': bool(rows.set_index('model').loc['candidate','inference_eligible'])}
print(json.dumps(out,indent=2))
