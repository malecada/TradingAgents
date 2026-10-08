from pathlib import Path
exec(compile((Path(__file__).parent/'verify.py').read_text().split('for budgets in')[0],__file__,'exec'))
for mode in ['signed-zero','underflow','large-pair']:
 if mode=='large-pair':left=graph(9);right=graph(9,.2);assert left.edge_index.shape[1]*right.edge_index.shape[1]>4096
 else:
  left=graph(4);right=graph(3)
  lf=np.zeros_like(left.edge_features);rf=np.zeros_like(right.edge_features)
  lf[:,0]=-0. if mode=='signed-zero' else math.sqrt(1490.)
  left=AttributedGraph(left.node_ids,left.node_features,left.edge_index,lf,left.parent_hash,left.center_id)
  right=AttributedGraph(right.node_ids,right.node_features,right.edge_index,rf,right.parent_hash,right.center_id)
 x=seed(left,right);y=copy.deepcopy(x)
 assert B.advance(x,left,right,config,max_operations=100000)==C.advance(y,left,right,config,max_operations=100000);equal(x,y)
 assert B.result(x,left,right,config).score.hex()==C.result(y,left,right,config).score.hex()
print(json.dumps({'status':'PASS','additional_cases':['signed-zero','underflow','large-pair-fallback'],'bitwise_boundaries':checks}))
