from pathlib import Path
import hashlib,json,difflib,ast
D=Path(__file__).resolve().parent;M=D.parents[3];P=Path('tradingagents/research/onchain_replication');rows=[]
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def replace(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
for name in ['model.py','real_pilot_training.py']:
 old=(M/P/name).read_bytes();s=old.decode()
 if name=='model.py':
  s=replace(s,"    if type(value) is not dict or set(value)!={'schema_version','backend','block_edges'}:\n        raise ValueError('model execution policy fields differ')\n    if type(value['schema_version']) is not int or value['schema_version']!=1 or value['backend']!='streamed-gat-mulsum-v1':", "    checkpointed=type(value) is dict and type(value.get('schema_version')) is int and value['schema_version']==2\n    fields={'schema_version','backend','block_edges'} | ({'graph_activation_checkpointing'} if checkpointed else set())\n    if type(value) is not dict or set(value)!=fields:\n        raise ValueError('model execution policy fields differ')\n    if checkpointed and value['graph_activation_checkpointing'] is not True:\n        raise ValueError('explicit activation checkpointing selection required')\n    if type(value['schema_version']) is not int or value['schema_version'] not in (1,2) or value['backend']!='streamed-gat-mulsum-v1':")
  s=replace(s,"        super().__init__();self._configure(config,task)\n        self.execution=selected", "        super().__init__();self._configure(config,task)\n        if selected is not None and selected['schema_version']==2:\n            if self.graph_activation_checkpointing:\n                raise ValueError('checkpoint execution must not change scientific config')\n            if type(config.get('gat_dropout')) not in (int,float) or config['gat_dropout']!=0:\n                raise ValueError('checkpoint execution requires original zero GAT dropout')\n            self.graph_activation_checkpointing=True\n        self.execution=selected")
 else:
  s=replace(s,"    model_execution defaults to eager (None); a known streamed policy must be\n    explicitly registered by the caller. Policy selection itself is not admission.","    model_execution defaults to eager (None). Known streamed and explicit\n    checkpointed-streamed policies must be registered by the caller; neither\n    changes the frozen scientific config or grants execution admission.")
  s=replace(s,"        selected_execution = None if validated_execution is None else dict(validated_execution)","        selected_execution = None if validated_execution is None else dict(validated_execution)\n        selected_checkpointing = selected_execution is not None and selected_execution.get('graph_activation_checkpointing',False)")
  s=replace(s,"and model.task == task and model.graph_activation_checkpointing is False, 'original trainable model/config required')", "and model.task == task and model.graph_activation_checkpointing is selected_checkpointing, 'original trainable model/config or selected checkpoint execution differs')")
 new=s.encode();ast.parse(new);put(D/'baseline'/name,old);put(D/'candidate'/P/name,new)
 a=old.decode().splitlines(True);b=s.splitlines(True);edits=[{'old_start':i,'old_end':j,'new_start':k,'new_end':l,'old':a[i:j],'new':b[k:l]} for op,i,j,k,l in difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes() if op!='equal']
 inv=b[:]
 for e in reversed(edits):assert inv[e['new_start']:e['new_end']]==e['new'];inv[e['new_start']:e['new_end']]=e['old']
 assert ''.join(inv).encode()==old
 put(D/(name+'.patch'),''.join(difflib.unified_diff(a,b,fromfile='a/'+str(P/name),tofile='b/'+str(P/name))).encode())
 rows.append({'path':str(P/name),'baseline_sha256':hashlib.sha256(old).hexdigest(),'candidate_sha256':hashlib.sha256(new).hexdigest(),'edits':edits})
put(D/'SOURCE_DELTA01.json',(json.dumps({'schema_version':1,'files':rows,'empirical_selection':False},indent=2,sort_keys=True)+'\n').encode())
print(json.dumps({r['path']:r['candidate_sha256'] for r in rows}))
