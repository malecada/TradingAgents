"""One bounded resource component; execution requires the parent's live guard."""
from pathlib import Path
import argparse
import json
import os
import sys
import time
import signal
import traceback
import resource
import numpy as np
import torch
from tradingagents.research.lifecycle import _immutable
from tradingagents.research.onchain_replication.resources import assert_guarded_worker
from tradingagents.research.onchain_replication.provenance import file_hash,digest
from tradingagents.research.onchain_replication.eth_source import decode_eth
from tradingagents.research.onchain_replication.weekly import build_weekly
from tradingagents.research.onchain_replication.graph_store import save_graph,load_graph
from tradingagents.research.onchain_replication.neighborhoods import sample_neighborhoods
from tradingagents.research.onchain_replication.serialization import samples_to_record,samples_from_record,dictionary_to_record,dictionary_from_record
from tradingagents.research.onchain_replication.dictionary import fit_dictionary
from tradingagents.research.onchain_replication.matching import match_batch
from tradingagents.research.onchain_replication.mcm import mcm_features
from tradingagents.research.onchain_replication.model import ReplicationModel
from tradingagents.research.onchain_replication.checkpoints import seed_all,save_checkpoint
from tradingagents.research.onchain_replication.cache import cache_key

ROOT=Path(__file__).resolve().parents[3];STUDY=Path(__file__).resolve().parent.parent


BINDINGS=None

def load(path):
    path=Path(path);body=path.read_bytes()
    if BINDINGS is not None and BINDINGS.get(str(path))!=digest(body):raise ValueError('unbound or changed parsed bytes: '+str(path))
    return json.loads(body)


def perform(phase,week,directory,artifacts,index,bindings):
    for path,sha in bindings.items():
        if file_hash(Path(path))!=sha:raise ValueError("upstream artifact bytes differ: "+path)
    def verified_graph(path):
        if str(path) not in bindings:raise ValueError("unbound graph manifest")
        return load_graph(path,bindings[str(path)])
    begin=time.monotonic();details={};cfg=load(STUDY/'config/dictionary.json');matching=load(STUDY/'config/matching-stable.json')
    graph_path=artifacts/week/'decode_graph'/'graph'/'manifest.json'
    if phase=='decode_graph':
        manifest={**index['weeks'][week],'scratch':str(directory)};decode_seconds=0.;count=0
        stream=iter(decode_eth(manifest,index['expected_schema']))
        def timed():
            nonlocal decode_seconds,count
            while True:
                start=time.monotonic()
                try:event=next(stream)
                except StopIteration:decode_seconds+=time.monotonic()-start;break
                decode_seconds+=time.monotonic()-start;count+=1
                yield event
        graph=next(build_weekly(timed(),load(STUDY/'config/graph.json'),coverage=[(manifest['start_utc'],manifest['end_utc'])],scratch=directory))
        elapsed=time.monotonic()-begin;path=save_graph(directory/'graph',graph)
        details={'rows':count,'decode_seconds':decode_seconds,'aggregate_seconds':elapsed-decode_seconds,'nodes':len(graph.node_ids),'edges':graph.edge_index.shape[1],'raw_count':graph.raw_count,'admitted_count':graph.admitted_count,'exclusion_counts':dict(graph.exclusion_counts),'graph_manifest':str(path),'graph_manifest_sha256':file_hash(path),'graph_bytes':sum(p.stat().st_size for p in path.parent.iterdir())}
    elif phase in ('neighborhoods','matching','dictionary'):
        if phase=='neighborhoods':
            graph=verified_graph(graph_path);sample=sample_neighborhoods([graph],{**cfg,'train_start':graph.start_utc,'train_end':'2026-01-01T00:00:00Z'},11)
            _immutable(directory/'samples.json',samples_to_record(sample));details={'samples':len(sample.graphs),'identity':sample.identity,'max_nodes':max(len(g.node_ids) for g in sample.graphs)}
        else:
            sample=samples_from_record(load(artifacts/week/'neighborhoods'/'samples.json'))
            if phase=='matching':
                scores=match_batch(list(zip(sample.graphs[:32],sample.graphs[32:64],strict=True)),matching)
                details={'pairs':len(scores),'scores':[float(s.score) for s in scores]}
            else:
                cursor=[0]
                def checkpoint(state):
                    cursor[0]+=1;_immutable(directory/f'partial-distance-{cursor[0]:05d}.json',state)
                dictionary=fit_dictionary(sample,matching,cfg,checkpoint=checkpoint)
                _immutable(directory/'dictionary.json',dictionary_to_record(dictionary));details={'motifs':len(dictionary.representatives),'identity':dictionary.identity,'resource_only':True}
    elif phase=='mcm':
        graph=verified_graph(graph_path);dictionary=dictionary_from_record(load(artifacts/'2022-01-03'/'dictionary'/'dictionary.json'))
        output=np.lib.format.open_memmap(directory/'mcm.npy',mode='w+',dtype=np.float32,shape=(len(graph.node_ids),32))
        def checkpoint(count,values):
            output.flush()
            with (directory/'mcm.npy').open('rb') as stream:os.fsync(stream.fileno())
            prefix=directory/f'prefix-{count:010d}.npy'
            with prefix.open('xb') as stream:
                np.save(stream,np.asarray(output[:count]),allow_pickle=False);stream.flush();os.fsync(stream.fileno())
            _immutable(directory/f'prefix-{count:010d}.json',{'complete_nodes':count,'total_nodes':len(graph.node_ids),'dictionary_hash':dictionary.identity,'graph_hash':load(graph_path)['graph_hash'],'matching_config_hash':cache_key(matching),'shape':list(output.shape),'dtype':str(output.dtype),'prefix_array':str(prefix),'array_sha256':file_hash(prefix),'source_commit':os.environ['PAPER_SOURCE_COMMIT'],'bindings':bindings,'qualification':'Immutable completed prefix; full output is a separate working array. Continuation requires verified prefix plus separately registered successor.'})
        mcm_features(graph,dictionary,matching,output=output,checkpoint=checkpoint);output.flush()
        details={'nodes':len(graph.node_ids),'motifs':32,'sha256':file_hash(directory/'mcm.npy')}
    elif phase=='neural_checkpoint':
        graph=verified_graph(graph_path);rng=seed_all(11);model=ReplicationModel(load(STUDY/'config/model.json'),'classification')
        # Conservative explicit memory forecast for dense edge/head intermediates.
        estimate=graph.edge_index.shape[1]*4*64*8+len(graph.node_ids)*32*4*16
        limits=load(STUDY/'pilot_successor_02/resource-contract-v4.json')
        if estimate>limits['neural_intermediate_allowance_bytes']:raise ValueError('capacity: neural intermediate estimate exceeds registered working allowance '+str(limits['neural_intermediate_allowance_bytes'])+' under cap '+str(limits['memory_max_bytes'])+': '+str(estimate))
        item={'mcm':torch.from_numpy(rng.random((len(graph.node_ids),32),dtype=np.float32)),'edge_index':torch.tensor(graph.edge_index.copy(),dtype=torch.long)}
        prices=torch.linspace(-1,1,16*28).reshape(16,28,1);labels=torch.arange(16)%2;optimizer=torch.optim.Adam(model.parameters(),lr=.001)
        forward=time.monotonic();out=model([[item]*28 for _ in range(16)],prices);loss=torch.nn.functional.cross_entropy(out,labels);loss.backward();optimizer.step();forward=time.monotonic()-forward
        config_hash=cache_key({'model':load(STUDY/'config/model.json'),'resource_only':'synthetic inputs and labels'})
        provenance={'source_hashes':list(graph.source_hashes),'config_hash':config_hash,'input_hash':load(graph_path)['graph_hash'],'dictionary_hash':cache_key({'synthetic_mcm':True}),'fold_id':'resource_only','cell_id':'neural/'+week,'source_commit':os.environ['PAPER_SOURCE_COMMIT']}
        io=time.monotonic();path=save_checkpoint(directory/'checkpoint',model,optimizer,rng,provenance,epoch=1,batch=0,logs=[{'loss':float(loss.detach())}]);io=time.monotonic()-io
        details={'synthetic':True,'unique_graphs':1,'batch':16,'lookback':28,'forward_backward_step_seconds':forward,'checkpoint_seconds':io,'checkpoint_bytes':sum(p.stat().st_size for p in path.parent.iterdir()),'intermediate_estimate_bytes':estimate}
    else:raise ValueError('unknown pilot phase')
    return {'phase':phase,'week':week,'status':'complete','elapsed_seconds':time.monotonic()-begin,'details':details}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--intent',required=True);args=parser.parse_args();intent_path=Path(args.intent);intent=load(intent_path)
    global BINDINGS
    BINDINGS=intent['bindings']
    limits=load(STUDY/'pilot_successor_02/resource-contract-v4.json')
    command=intent['guard_command'];assert_guarded_worker(intent['guard_receipt'],command,required_paths=[ROOT,intent_path.parent,Path('/home/malecada/Data')],wall_seconds=28800,
        memory_max_bytes=limits['memory_max_bytes'],memory_high_bytes=limits['memory_high_bytes'])
    if intent['worker_command']!=[sys.executable,'-B',str(Path(__file__).resolve()),'--intent',str(intent_path)]:raise ValueError('phase command differs')
    if os.getppid()!=intent['owner_pid']:raise ValueError('phase owner differs')
    def stop(signum,frame):raise TimeoutError('registered phase stop signal '+str(signum))
    signal.signal(signal.SIGTERM,stop);torch.set_num_threads(2)
    directory=intent_path.parent;begin=time.monotonic()
    try:result=perform(intent['phase'],intent['week'],directory,Path(intent['artifacts']),load(STUDY/'pilot_successor_02/source-index.json'),intent['bindings'])
    except BaseException as error:
        text=str(error);status='unavailable' if isinstance(error,TimeoutError) or 'capacity' in text else 'failed'
        result={'phase':intent['phase'],'week':intent['week'],'status':status,'elapsed_seconds':time.monotonic()-begin,'reason':type(error).__name__+': '+text,'traceback':traceback.format_exc()}
    result['peak_worker_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    _immutable(directory/'result.json',result)
    return 0 if result['status']!='failed' else 1

if __name__=='__main__':raise SystemExit(main())
