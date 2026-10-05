"""Offline bounded saved-model replay; synthetic example is not an empirical result."""
import io
import json
from pathlib import Path
import numpy as np
import torch
from .model import ReplicationModel
from .checkpoints import seed_all,save_checkpoint
from .cache import read_artifact
from .provenance import file_hash,canonical_bytes,digest
from ..lifecycle import _immutable

CODE=('model.py','gat.py','pooling.py','temporal.py','replay.py')


def inputs(raw):
    graphs=[{'mcm':torch.tensor(g['mcm'],dtype=torch.float32),'edge_index':torch.tensor(g['edge_index'],dtype=torch.long)} for g in raw['graphs']]
    return [[graphs[i] for i in row] for row in raw['sequences']],torch.tensor(raw['prices'],dtype=torch.float32)


def make_synthetic_fixture(directory,config,source_commit):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    raw={'data_kind':'synthetic_neural_inputs','graphs':[{'mcm':(np.arange(4*32).reshape(4,32)/256+shift).tolist(),'edge_index':[[0,1,2,3,1],[1,2,3,0,0]]} for shift in (0.,.25)],'sequences':[[0]*14+[1]*14,[1]*14+[0]*14],'prices':np.linspace(-1,1,56).reshape(2,28,1).tolist()}
    _immutable(directory/'inputs.json',raw);_immutable(directory/'model.json',config)
    rng=seed_all(314159);model=ReplicationModel(config,'classification');optimizer=torch.optim.Adam(model.parameters(),lr=.001)
    graph,price=inputs(raw);model.train();loss=torch.nn.functional.cross_entropy(model(graph,price),torch.tensor([0,1]));loss.backward();optimizer.step();model.eval()
    with torch.no_grad():expected=model(graph,price).numpy().astype(float)
    provenance={'source_hashes':[file_hash(directory/'inputs.json'),file_hash(directory/'model.json')],'config_hash':digest(canonical_bytes(config)),'input_hash':file_hash(directory/'inputs.json'),'dictionary_hash':digest(b'synthetic MCM inputs; not a fitted empirical dictionary'),'fold_id':'synthetic','cell_id':'synthetic-full-model-replay','source_commit':source_commit}
    checkpoint=save_checkpoint(directory/'checkpoint',model,optimizer,rng,provenance,epoch=1,batch=0,logs=[{'synthetic_loss':float(loss.detach())}])
    _immutable(directory/'expected.json',expected.tolist())
    package=Path(__file__).resolve().parent
    _immutable(directory/'manifest.json',{'data_kind':raw['data_kind'],'provenance':provenance,'checkpoint':str(checkpoint.relative_to(directory)),'files':{str(p.relative_to(directory)):file_hash(p) for p in directory.rglob('*') if p.is_file()},'source_files':{name:file_hash(package/name) for name in CODE},'qualification':'One synthetic optimizer step; validates offline checkpoint inference only, not predictive performance, dictionary fitting or empirical raw recovery.'})
    return directory/'manifest.json'


def replay(directory):
    directory=Path(directory);manifest=json.loads((directory/'manifest.json').read_bytes())
    if manifest['data_kind']!='synthetic_neural_inputs':raise ValueError('fixture kind differs')
    for relative,sha in manifest['files'].items():
        path=directory/relative
        if Path(relative).is_absolute() or not path.resolve().is_relative_to(directory.resolve()) or file_hash(path)!=sha:raise ValueError('replay fixture bytes differ')
    package=Path(__file__).resolve().parent
    if manifest['source_files']!={name:file_hash(package/name) for name in CODE}:raise ValueError('replay source differs')
    model=ReplicationModel(json.loads((directory/'model.json').read_bytes()),'classification')
    data=read_artifact(directory/manifest['checkpoint'],manifest['provenance'])
    state=torch.load(io.BytesIO(data['state.pt']),map_location='cpu',weights_only=True);model.load_state_dict(state['model'],strict=True);model.eval()
    graph,price=inputs(json.loads((directory/'inputs.json').read_bytes()))
    with torch.no_grad():actual=model(graph,price).numpy().astype(float)
    expected=np.array(json.loads((directory/'expected.json').read_bytes()),dtype=float)
    if actual.shape!=expected.shape or not np.isfinite(actual).all() or not np.allclose(actual,expected,atol=1e-5,rtol=1e-4):raise ValueError('saved-model CPU replay exceeds C06 tolerance')
    return {'status':'passed','scope':'synthetic_saved_model_only','predictions':len(actual),'max_absolute_difference':float(np.abs(actual-expected).max()),'atol':1e-5,'rtol':1e-4,'fixture_manifest_sha256':file_hash(directory/'manifest.json')}


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path);args=parser.parse_args()
    torch.set_num_threads(2);print(json.dumps(replay(args.directory),sort_keys=True))
