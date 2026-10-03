"""Uninstalled stdlib literal full-scope coverage check; no fit/budget authority."""
from collections import Counter
ASSETS=('BTC','ETH');FOLDS=tuple(range(2018,2025));SEEDS=(11,23,37,51,71)
PRICE=('proposed','lstm','hlstm','gru','svm');GRAPH=('proposed','node2vec','graphwave','gin','watchyourstep')
DIAGNOSTICS=('constant_graph','mcm_without_gat','gat_without_mcm','training_label_permutation')
def require(v,m):
 if not v:raise ValueError(m)
def literal_rows():
 rows=[]
 for table,assets,task,arms,variant in [(1,ASSETS,'regression',PRICE,'whole'),(2,ASSETS,'direction',PRICE,'whole'),(3,ASSETS,'direction',GRAPH,'whole'),(4,ASSETS,'regression',('proposed',),'whole'),(4,ASSETS,'regression',('proposed',),'whale'),(5,('ETH',),'regression',PRICE,'fund'),(6,('ETH',),'direction',PRICE,'fund')]:
  rows.extend((table,a,task,arm,variant) for a in assets for arm in arms)
 return tuple(rows)
def check(table_rows,training):
 expected=Counter(literal_rows());actual=Counter((r['table'],r['asset'],r['task'],r['arm'],r['variant']) for r in table_rows)
 require(actual==expected,'literal44 printed row membership differs')
 cells={};table_members={}
 for r in table_rows:
  require(tuple(r['folds'])==FOLDS and tuple(r['seeds'])==SEEDS,'exact reconstructed7fold/5seed membership differs')
  rowkey='|'.join(str(r[k]) for k in ('table','asset','task','arm','variant'));members=[]
  for fold in FOLDS:
   for seed in SEEDS:
    identity='/'.join(('paper_reconstruction',r['asset'],str(fold),str(seed),r['task'],r['arm'],r['variant']))
    require(r['cell_pattern'].format(fold=fold,seed=seed)==identity,'pattern does not encode exact scientific cell')
    cells.setdefault(identity,[]).append(r['table']);members.append(identity)
  table_members[rowkey]=members
 expected_diag={f'paper_reconstruction/ETH/2024/{s}/direction/{a}/whole' for s in SEEDS for a in DIAGNOSTICS}
 require(len(training['diagnostic_cells'])==20 and set(training['diagnostic_cells'])==expected_diag,'exact20 diagnostics differ')
 require(tuple(training['seeds'])==SEEDS,'training seed configuration differs')
 require(len(cells)==1400 and not set(cells)&expected_diag,'paper/diagnostic overlap or denominator')
 for identity in expected_diag:cells[identity]=[]
 initial={i for i in cells if i.split('/')[1:3]==['ETH','2024'] and i.split('/')[4]=='direction' and i.split('/')[5] in set(PRICE)|set(DIAGNOSTICS) and i.endswith('/whole')}
 batches=[{'id':'initial-ETH-2024','cell_ids':sorted(initial)}]
 for a in ASSETS:
  for fold in FOLDS:
   batches.append({'id':f'{a}-{fold}','cell_ids':sorted(i for i in cells if i.split('/')[1:3]==[a,str(fold)] and i not in initial)})
 assigned=[i for b in batches for i in b['cell_ids']];require(len(assigned)==len(set(assigned))==1420 and set(assigned)==set(cells),'exact15 batch partition failed')
 return {'status':'COVERAGE_METADATA_ONLY_NOT_ADMITTED','printed_rows':44,'paper_fits':1400,'diagnostic_fits':20,'total_fits':1420,'initial_fits':len(initial),'asset_counts':dict(Counter(i.split('/')[1] for i in cells)),'batches':batches,'cells':[{'id':i,'tables':cells[i]} for i in sorted(cells)],'table_members':table_members,'financial_execution_credit':0,'budget_authority':None}
