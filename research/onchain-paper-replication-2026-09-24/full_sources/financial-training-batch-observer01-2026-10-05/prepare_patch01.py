"""Exact optional observer patch, preserving all original scientific expressions."""
from pathlib import Path
import ast, hashlib, json
H=Path(__file__).resolve().parent;ROOT=H.parents[3]
source=ROOT/'tradingagents/research/onchain_replication/evaluation.py'
old=source.read_bytes();text=old.decode();edits=[]
def replace(a,b):
 global text
 assert text.count(a)==1;text=text.replace(a,b);edits.append({'old':a,'new':b})
replace('def batch_factory(arm,task,examples,scaler,features,*,permuted=False):','def batch_factory(arm,task,examples,scaler,features,*,permuted=False,observation=None):')
replace('        return inputs,targets[indices]','        if observation is not None:\n            from .training_batch_observer import observe\n            observe(observation[0],observation[1],indices,examples,inputs,features)\n        return inputs,targets[indices]')
replace("        train=batch_factory(arm,task,examples.train,scaler,features,permuted=arm=='training_label_permutation')", "        from .training_batch_observer import prepare\n        observation=prepare(run,registered_id,provenance,examples,feature_binding,training_config,features)\n        train=batch_factory(arm,task,examples.train,scaler,features,permuted=arm=='training_label_permutation',observation=None if observation is None else (run,observation))")
back=text
for e in reversed(edits):assert back.count(e['new'])==1;back=back.replace(e['new'],e['old'])
assert back.encode()==old and ast.dump(ast.parse(back))==ast.dump(ast.parse(old))
for name,b in [('original_evaluation.py',old),('evaluation.py',text.encode())]:
 with (H/name).open('xb') as f:f.write(b)
rows=[]
for name in ('evaluation.py','training.py','model.py','dataset.py','calendar.py','feature_residency.py','compact_training.py','compact_native_features.py','compact_terminal.py','compact_owner.py','matching_owner.py'):
 p=ROOT/'tradingagents/research/onchain_replication'/name;b=p.read_bytes();rows.append({'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
inverse={'original_sha256':hashlib.sha256(old).hexdigest(),'candidate_sha256':hashlib.sha256(text.encode()).hexdigest(),'edits':edits,'full_byte_inverse':True,'full_ast_inverse':True}
for name,value in [('INVERSE01.json',inverse),('SOURCE_BODIES01.json',rows)]:
 with (H/name).open('xb') as f:f.write((json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode())
print(json.dumps({'literal_edits':len(edits),'inverse':True,'source':inverse['original_sha256'],'candidate':inverse['candidate_sha256']}))
