from pathlib import Path
from types import SimpleNamespace
P=Path(__file__).resolve().parent
exec(compile((P/'verify02.py').read_text().split('checks=[];traces=[]')[0],str(P/'verify02.py'),'exec'))
checks=[]
for mode in ('ann_module','hard_module','np_module','hard_create_function','matrix_identity_function','normalization_function'):
 c=copy.deepcopy(config);s=session.ImmutablePairSession(a,b,c,engine=engine,annealing=ann);state=engine.create(a,b,c,**policy);called=[]
 if mode=='ann_module':module,name=engine,'ann';old=getattr(module,name);replacement=SimpleNamespace(**vars(old));replacement._advance_checked=lambda *a,**k:called.append('bad')
 elif mode=='hard_module':module,name=engine,'hard';old=getattr(module,name);replacement=SimpleNamespace(**vars(old))
 elif mode=='np_module':module,name=engine,'np';old=getattr(module,name);replacement=SimpleNamespace(**vars(old))
 elif mode=='hard_create_function':module,name=engine.hard,'create';old=getattr(module,name);replacement=lambda *a,**k:None
 elif mode=='matrix_identity_function':module,name=engine,'matrix_identity';old=getattr(module,name);replacement=lambda *a,**k:'0'*64
 else:module,name=ann,'normalization_policy';old=getattr(module,name);replacement=lambda *a,**k:None
 setattr(module,name,replacement)
 try:
  try:s.advance(state,max_operations=1)
  except ValueError as error:assert not called;checks.append({'case':mode,'refused':True,'error':str(error)})
  else:raise AssertionError('redirected dependency accepted')
 finally:setattr(module,name,old);engine.close(state);s.close()
result={'status':'PASS','checks':checks,'scope':'Specific immutable-session01 dependency RED now refused; no numerical rerun or empirical authority.'}
(P/'SUPPLEMENT03.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
