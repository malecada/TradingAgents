from pathlib import Path
p=Path(__file__).parent
f=p/'archive_non_tail.py';s=f.read_text()
s=s.replace('def validate_policy(p):\n', '''def validate_policy(p):
 if type(p) is dict and type(p.get('schema_version')) is int and p['schema_version']==3:
  require(p.get('kind')=='non-tail-produced-f32-population-v1','explicit completed f32 population required')
  base=dict(p);base.update(schema_version=2,kind='non-tail-durable-selected-population-v2');validate_policy(base)
  require(all(row['role']=='mcm-output' and row['max_members']==2 for row in p['slots']),'completed raw-only manifest/matrix slots required; NPY refused')
  return json.loads(encode(p))
''')
s=s.replace("if self.policy['schema_version']==2:","if self.policy['schema_version'] in (2,3):")
s=s.replace("  require(type(source) is api.HeldBatches,'genuine held score-batch adapter required; raw/NPY typed authority not implemented')", """  if context.policy['schema_version']==3:
   from .completed_f32 import CompletedF32
   require(type(source) is CompletedF32,'actual completed Produced adapter required; HeldBatches/NPY refused');role='mcm-output'
  else:
   require(type(source) is api.HeldBatches,'genuine held score-batch adapter required; raw/NPY typed authority not implemented');role='score-batches'""")
s=s.replace("s['role']=='score-batches'];require(len(slots)==1", "s['role']==role];require(len(slots)==1")
s=s.replace("'role':'score-batches','scope':target.derive_scope()", "'role':role,'scope':target.derive_scope()")
s=s.replace("with api.content.open_local(root,kind='score-batches',document_sha256=source._reader.reference)","with api.content.open_local(root,kind=self.ledger.record['role'],document_sha256=source._reader.reference)")
s=s.replace("if self.ledger.context.policy['schema_version']==2:","if self.ledger.context.policy['schema_version'] in (2,3):")
f.write_text(s)
f=p/'selected_non_tail_transport.py';s=f.read_text()
s=s.replace('def policy(value,context):\n', '''def policy(value,context):
 if type(value) is dict and type(value.get('schema_version')) is int and value['schema_version']==2:
  require(value.get('kind')=='selected-produced-f32-ssh-plaintext-channel-v1' and context.get('schema_version')==3 and all(row['role']=='mcm-output' for row in context['slots']),'explicit completed raw-only transport selection')
  legacy=dict(value);legacy.update(schema_version=1,kind='selected-non-tail-ssh-plaintext-channel-v1')
  shape=dict(context);shape['slots']=[dict(row,role='score-batches') for row in context['slots']]
  policy(legacy,shape);return json.loads(encoded(value))
 require(context.get('schema_version')!=3,'raw Context cannot select f64 transport schema')
''')
s=s.replace("c.policy['schema_version']==2,'genuine explicitly", "c.policy['schema_version'] in (2,3),'genuine explicitly")
s=s.replace("c.policy['schema_version']==2,'legacy unselected", "c.policy['schema_version'] in (2,3),'legacy unselected")
s=s.replace("  require(type(source) is api.HeldBatches and operation.ledger.record['role']=='score-batches','genuine f64 HeldBatches only; raw-f32/NPY live adapters absent')", """  if c.policy['schema_version']==3:
   from .completed_f32 import CompletedF32
   require(type(source) is CompletedF32 and operation.ledger.record['role']=='mcm-output','actual completed raw Produced adapter required; NPY refused')
  else:
   require(type(source) is api.HeldBatches and operation.ledger.record['role']=='score-batches','genuine f64 HeldBatches only; raw-f32/NPY live adapters absent')""")
s=s.replace("'kind':'selected-f64-transfer-attempt'", "'kind':('selected-produced-f32-transfer-attempt' if self.c.policy['schema_version']==3 else 'selected-f64-transfer-attempt')")
s=s.replace("'kind':'selected-f64-remote-roundtrip'", "'kind':('selected-produced-f32-remote-roundtrip' if self.c.policy['schema_version']==3 else 'selected-f64-remote-roundtrip')")
f.write_text(s)
f=p/'compact_mcm.py';s=f.read_text();needle='        result._check(); return result'
assert s.count(needle)==1
s=s.replace(needle,'''        result._check()
        if _imported(dictionary):
            selected=dictionary.execution._stage.prepared._selection_now()['selected']
            name=selected.get('non_tail_transport_input')
            if name is not None:
                raw=owner.bound._run.read_input(name)
                require(len(raw)<=8192,'completed transport policy metadata bound')
                if json.loads(raw).get('schema_version')==3:
                    from .completed_f32 import consume_if_selected
                    consume_if_selected(result,held)
        return result''')
f.write_text(s)
