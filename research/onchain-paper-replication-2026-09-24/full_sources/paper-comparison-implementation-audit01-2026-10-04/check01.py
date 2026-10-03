import copy,json
from pathlib import Path
from coverage_contract01 import check
H=Path(__file__).resolve().parent;R=H.parents[1];rows=json.loads((R/'table-map.json').read_bytes());training=json.loads((R/'config/training.json').read_bytes());checks=[]
def ok(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def refusal(n,mutate):
 a=copy.deepcopy(rows);t=copy.deepcopy(training);mutate(a,t)
 try:check(a,t)
 except ValueError:checks.append(n)
 else:raise AssertionError(n)
v=check(rows,training);ok('1420 exact total',v['total_fits']==1420);ok('BTC525 ETH895',v['asset_counts']=={'BTC':525,'ETH':895});ok('15 batches initial45',len(v['batches'])==15 and v['initial_fits']==45);ok('all paper350 fund retained',sum(c['id'].endswith('/fund') for c in v['cells'])==350)
refusal('missing printed row',lambda a,t:a.pop());refusal('duplicate printed row',lambda a,t:a.append(copy.deepcopy(a[0])));refusal('graph comparator renamed',lambda a,t:next(r for r in a if r['arm']=='graphwave').update(arm='generic_gat'));refusal('lost BTC',lambda a,t:a.__setitem__(0,{**a[0],'asset':'ETH'}));refusal('sixfold shortcut',lambda a,t:a[0]['folds'].pop());refusal('duplicate fold same count',lambda a,t:a[0]['folds'].__setitem__(0,2019));refusal('four seed shortcut',lambda a,t:a[0]['seeds'].pop());refusal('seed substitution',lambda a,t:a[0]['seeds'].__setitem__(0,13));refusal('pattern wrong asset',lambda a,t:a[0].update(cell_pattern=a[0]['cell_pattern'].replace('BTC','ETH')));refusal('pattern hidden second lane',lambda a,t:a[0].update(cell_pattern=a[0]['cell_pattern'].replace('paper_reconstruction','second_lane')));refusal('duplicate diagnostic same count',lambda a,t:t['diagnostic_cells'].__setitem__(0,t['diagnostic_cells'][1]));refusal('missing diagnostic',lambda a,t:t['diagnostic_cells'].pop());refusal('training seed drift',lambda a,t:t['seeds'].__setitem__(0,13))
for c in v['cells']:
 if c['id'].split('/')[5]=='proposed' and c['id'].endswith('/whole') and c['tables']:
  ok('shared same original fit tables',sorted(c['tables'])==([1,4] if '/regression/' in c['id'] else [2,3]))
(H/'CHECKS01.json').write_text(json.dumps({'count':len(checks),'checks':checks,'numerical_imports':False,'empirical_execution':False,'budget_authority':None},indent=2)+'\n');print(len(checks),'passed')
