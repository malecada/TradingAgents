"""Necessary evaluation seam, preserving Main's treatment and observation behavior."""
import ast,json
from pathlib import Path
H=Path(__file__).resolve().parent;REL=Path('tradingagents/research/onchain_replication')
MAIN=H.parents[3]/REL
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')/REL
def replace(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def put(p,s):
 with p.open('xb') as f:f.write(s if isinstance(s,bytes) else s.encode())
raw=(MAIN/'evaluation.py').read_bytes();put(H/'origins/Main/evaluation.py',raw);put(H/'origins/CAP/evaluation.py',(CAP/'evaluation.py').read_bytes());s=raw.decode()
s=replace(s,'from .training import fit_cell,predict_cell,_reserve','from . import financial_execution as financial\nfrom .training import fit_cell,predict_cell,_reserve')
s=replace(s,'completed_fit=None,treatment_reference=None):','completed_fit=None,treatment_reference=None,execution=None):')
s=replace(s,'    examples.require_test_mask(expected_test_mask)',"    execution=financial.for_run(run,execution)\n    if financial.identity(provenance.get('model_execution'))!=execution or ('model_execution' in provenance)!=(execution is not None):raise ValueError('evaluation execution provenance differs')\n    examples.require_test_mask(expected_test_mask)")
s=replace(s,'factory=lambda:build_model(arm,task,model_config)','factory=lambda:build_model(arm,task,model_config) if execution is None else build_model(arm,task,model_config,execution=execution)')
s=replace(s,"            else:\n                output=predict_cell(model,test,len(examples.test),training_config['batch_size'])","            else:\n                financial.check_model(model,execution)\n                output=predict_cell(model,test,len(examples.test),training_config['batch_size'])")
s=replace(s,"            output=predict_cell(fitted.model,test,len(examples.test),training_config['batch_size']);checkpoint_hash=fitted.checkpoint_hash","            financial.check_model(fitted.model,execution)\n            output=predict_cell(fitted.model,test,len(examples.test),training_config['batch_size']);checkpoint_hash=fitted.checkpoint_hash")
s=replace(s,"        model=factory();model.load_state_dict(state['model'],strict=True)","        financial.validate_state(state,old)\n        model=factory();financial.check_state_model(state,model,old);model.load_state_dict(state['model'],strict=True)")
ast.parse(s);put(H/'candidate/evaluation.py',s)
print(json.dumps({'prepared':'evaluation.py','Main_treatment_observer_detached_features_retained':True,'actual_numerical_import':False}))
