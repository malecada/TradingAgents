# Compact graph tensor boundary

The adapter consumes an actual compact MCM producer result. It binds both
registered plan/job selections, source-admits the existing bounded conversion
kernel and creates independent CPU float32 MCM and int64 edge tensors. The MCM
is fixed input to the existing downstream trainable MLP/GAT. No learned encoder
is evaluated or detached here.

The numeric cap is per conversion: twice the MCM plus edge payload, plus nine
bytes per configured chunk entry. It does not reserve repeated conversions,
caller-expanded tensor backing storage, graph attributes, samples/dictionary,
Python objects, model state, whole-process RSS or physical filesystem use.
A future representation owner must account for every retained tensor population.

Current-owner leases, full saved MCM byte admission and callback-free original
ancestry/output checks protect the conversion boundary. This is an in-process
contract under the existing sampled mutation model, not an adversarial Python
security boundary or atomic filesystem snapshot.

Graph artifact publication/admission, complete calendar/price admission,
representation closure, native terminal handoff and empirical release are
separate. No completed empirical run is repeated and no financial fit is added.
