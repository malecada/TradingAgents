"""One independent synthetic step reconstruction; no real inputs or run authority."""
from pathlib import Path
import hashlib
import json
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
import torch
from tradingagents.research.onchain_replication import real_pilot_training as helper
from tradingagents.research.onchain_replication.model import ReplicationModel
from tradingagents.research.onchain_replication.checkpoints import seed_all, capture_rng

sha = lambda b: hashlib.sha256(b).hexdigest()
torch.set_num_threads(2)
config = json.loads((ROOT/'research/onchain-paper-replication-2026-09-24/config/model.json').read_bytes())
training = json.loads((ROOT/'research/onchain-paper-replication-2026-09-24/config/training.json').read_bytes())
features = {}
contracts = {}
for i in range(7):
    key = sha(('independent synthetic graph '+str(i)).encode())
    mcm = (torch.arange(128, dtype=torch.float32).reshape(4,32) % 17 + i + 1) / 31
    edges = torch.tensor([[0,1,2,3,0,2],[1,2,3,0,2,0]], dtype=torch.int64)
    features[key] = {'mcm':mcm, 'edge_index':edges}
    contracts[key] = {'nodes':4, 'edges':6,
                      'mcm_sha256':sha(mcm.numpy().tobytes()),
                      'edge_index_sha256':sha(edges.numpy().tobytes())}
keys = list(features)
sequences = [[keys[((row+day)//7)%7] for day in range(28)] for row in range(16)]
prices = (torch.arange(448, dtype=torch.float32).reshape(16,28,1) % 37 - 18) / 19
targets = torch.tensor([int(i % 3 == 0) for i in range(16)], dtype=torch.int64)
inputs = {'prices':prices, 'graph_sequences':[[features[k] for k in row] for row in sequences]}

# Independent direct update follows the existing training algorithm; it does not
# call the helper's phase, clipping, save/readback, or equality implementations.
rng = seed_all(11)
model = ReplicationModel(config, 'classification')
model.train()
optimizer = torch.optim.Adam(model.parameters(), lr=training['learning_rate'],
    betas=tuple(training['betas']), eps=training['epsilon'], weight_decay=training['weight_decay'])
optimizer.zero_grad(set_to_none=True)
output = model(**inputs)
loss = torch.nn.functional.cross_entropy(output, targets)
loss_value = float(loss.detach())
loss.backward()
norm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), training['gradient_clip_norm'], error_if_nonfinite=True))
optimizer.step()
expected = {'model':model.state_dict(), 'optimizer':optimizer.state_dict(), 'rng':capture_rng(rng)}

reads = []
def batch(indices):
    reads.append(indices)
    assert indices == list(range(16))
    return inputs, targets
result = helper.run_one_update(model_factory=lambda:ReplicationModel(config,'classification'),
    batch_factory=batch, indices=list(range(16)), graph_features=features,
    graph_contracts=contracts, graph_sequences=sequences, model_config=config,
    training_config=training, provenance={'scope':'independent synthetic engineering check only'},
    directory=HERE/'synthetic-attempt01', authority_check=lambda:None,
    max_checkpoint_bytes=4*1024**2)
assert reads == [list(range(16))]
actual = torch.load(HERE/'synthetic-attempt01/checkpoint.pt', weights_only=True)
tensor_count = 0
def equal(a,b):
    global tensor_count
    assert type(a) is type(b), (type(a),type(b))
    if isinstance(a, torch.Tensor):
        assert a.dtype == b.dtype and a.shape == b.shape and torch.equal(a,b)
        tensor_count += 1
    elif isinstance(a, dict):
        assert a.keys() == b.keys()
        for k in a: equal(a[k], b[k])
    elif isinstance(a, (tuple,list)):
        assert len(a) == len(b)
        for x,y in zip(a,b): equal(x,y)
    else: assert a == b
for key in expected: equal(expected[key],actual[key])
assert result['loss'] == loss_value
assert all(int(row['step']) == 1 for row in actual['optimizer']['state'].values())
assert result['optimizer_steps'] == 1 and result['financial_fit_complete'] is False and result['paper_financial_fits'] == 0
assert all(result['gradients'][key]['nonzero_elements'] > 0 for key in ('gat','lstm','attention'))
pins = {}
for name in ['tradingagents/research/onchain_replication/real_pilot_training.py',
             'tests/research/onchain_replication/test_real_pilot_training.py']:
    body = (ROOT/name).read_bytes()
    pins[name] = {'sha256':sha(body), 'bytes':len(body)}
    (HERE/('source-'+Path(name).name)).write_bytes(body)
out = {'status':'PASS_INDEPENDENT_SYNTHETIC_STEP', 'source_pins':pins,
       'state_tensors_exactly_equal':tensor_count, 'manual_loss':loss_value,
       'manual_preclip_norm':norm, 'optimizer_steps':1,
       'model_adam_rng_exactly_equal_to_manual_step':True,
       'genuine_authority_exercised':False,'real_data_read':False,
       'synthetic_checkpoint_bytes':result['checkpoint_bytes'],
       'helper_checkpoint_execution':actual.get('model_execution','ABSENT'),
       'helper_result_execution':result.get('model_execution','ABSENT')}
(HERE/'CHECK01.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True))
