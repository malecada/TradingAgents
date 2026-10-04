"""Frozen graph comparators; capacity failures are explicit, never subsampled."""
import time
import numpy as np
import torch
from torch import nn
from scipy import sparse
from scipy.sparse.linalg import expm_multiply
from .temporal import initialize_linear
from .pooling import mean_pool
from .checkpoints import seed_all,capture_rng,restore_rng
from .cache import cache_key
from .provenance import digest


def _embedding_identity(edge_index,n,config,seed):
    edges=np.ascontiguousarray(edge_index,dtype=np.int64)
    return cache_key({'edge_bytes':digest(memoryview(edges).cast('B')),'shape':edges.shape,'n':n,'config':config,'seed':seed})


def adjacency(edge_index,n,*,weak=False):
    edges=np.asarray(edge_index)
    if edges.shape[0]!=2 or not np.issubdtype(edges.dtype,np.integer) or n<=0 or (edges.size and (edges.min()<0 or edges.max()>=n)):raise ValueError('invalid graph dimensions')
    a=sparse.csr_matrix((np.ones(edges.shape[1]),(edges[0],edges[1])),shape=(n,n))
    if weak:a=a.maximum(a.T)
    a.data[:]=1
    return a


def graphwave(edge_index,n,config,*,max_entries=None,checkpoint=None,resume_state=None,checkpoint_seconds=600.):
    if max_entries is None:raise ValueError('explicit resource-derived allocation ceiling required')
    if n*(2*len(config['scales'])*len(config['evaluation_points']))>max_entries:raise ValueError('GraphWave representation capacity exceeded')
    a=adjacency(edge_index,n,weak=True);lap=sparse.diags(np.asarray(a.sum(1)).ravel())-a
    result=np.empty((n,2*len(config['scales'])*len(config['evaluation_points'])),dtype=np.float32)
    if not 0<checkpoint_seconds<=600:raise ValueError('checkpoint interval exceeds protocol')
    identity=_embedding_identity(edge_index,n,config,0);start=0;last=time.monotonic()
    if resume_state is not None:
        if resume_state['identity']!=identity:raise ValueError('embedding checkpoint identity mismatch')
        start=resume_state['next_node'];result[:start]=resume_state['completed']
    for node in range(start,n):
        basis=np.zeros(n);basis[node]=1.;values=[]
        for scale in config['scales']:
            heat=expm_multiply(-scale*lap,basis)
            for point in config['evaluation_points']:
                z=np.exp(1j*point*heat).mean();values.extend([z.real,z.imag])
        result[node]=values
        if checkpoint and (node+1==n or time.monotonic()-last>=checkpoint_seconds):
            checkpoint(node+1,{'identity':identity,'next_node':node+1,'completed':result[:node+1]});last=time.monotonic()
    return result


def align_embeddings(node_ids,current,previous_ids,previous):
    current=np.asarray(current);previous=np.asarray(previous)
    if current.shape!=(len(node_ids),previous.shape[1]) or len(previous)!=len(previous_ids):raise ValueError('embedding identity dimensions')
    if len(set(node_ids))!=len(node_ids) or len(set(previous_ids))!=len(previous_ids):raise ValueError('duplicate alignment IDs')
    positions={name:i for i,name in enumerate(previous_ids)};pairs=[(i,positions[name]) for i,name in enumerate(node_ids) if name in positions]
    if not pairs:raise ValueError('no historical alignment anchors')
    left=np.array([i for i,j in pairs]);right=np.array([j for i,j in pairs])
    u,_,vt=np.linalg.svd(current[left].T@previous[right],full_matrices=False)
    return current@(u@vt)


def walks(edge_index,n,*,walk_length,walks_per_node,seed):
    a=adjacency(edge_index,n,weak=True);rng=np.random.Generator(np.random.PCG64(seed))
    for _ in range(walks_per_node):
        for start in range(n):
            walk=[start]
            while len(walk)<walk_length:
                choices=a.indices[a.indptr[walk[-1]]:a.indptr[walk[-1]+1]]
                if not len(choices):break
                walk.append(int(rng.choice(choices)))
            yield walk


def node2vec(edge_index,n,config,seed,*,max_entries=None,checkpoint=None,resume_state=None,checkpoint_seconds=600.):
    if max_entries is None:raise ValueError('explicit resource-derived allocation ceiling required')
    if not 0<checkpoint_seconds<=600:raise ValueError('checkpoint interval exceeds protocol')
    if config['p']!=1 or config['q']!=1:raise ValueError('only frozen p=q=1 random walks admitted')
    width=config['dimensions']
    if n*width*2>max_entries:raise ValueError('Node2Vec parameter capacity exceeded')
    rng=seed_all(seed);a=adjacency(edge_index,n,weak=True)
    degree=np.asarray(a.sum(1)).ravel()**.75
    if not degree.sum():raise ValueError('Node2Vec has no positive contexts')
    negative_distribution=degree/degree.sum()
    left=nn.Embedding(n,width);right=nn.Embedding(n,width)
    nn.init.uniform_(left.weight,-.5/width,.5/width);nn.init.uniform_(right.weight,-.5/width,.5/width)
    optimizer=torch.optim.SGD([*left.parameters(),*right.parameters()],lr=config['learning_rate'])
    identity=_embedding_identity(edge_index,n,config,seed)
    logs=[];epoch=0;processed=0;total=0.;last=time.monotonic()
    if resume_state is not None:
        if resume_state['identity']!=identity:raise ValueError('embedding checkpoint identity mismatch')
        left.load_state_dict(resume_state['left']);right.load_state_dict(resume_state['right']);optimizer.load_state_dict(resume_state['optimizer'])
        restore_rng(resume_state['rng'],rng);logs=list(resume_state['logs']);epoch=resume_state['epoch'];processed=resume_state['processed'];total=resume_state['loss_sum']
    def save():
        nonlocal last
        if checkpoint:checkpoint(epoch,{'identity':identity,'left':left.state_dict(),'right':right.state_dict(),'optimizer':optimizer.state_dict(),'rng':capture_rng(rng),'logs':logs,'epoch':epoch,'processed':processed,'loss_sum':total})
        last=time.monotonic()
    while epoch<config['epochs']:
        pairs=[];seen=0
        def update(pairs):
            values=torch.tensor(pairs);neg=torch.tensor(rng.choice(n,size=(len(pairs),config['negative_samples']),p=negative_distribution))
            x=left(values[:,0]);pos=(x*right(values[:,1])).sum(1);negative=(x[:,None,:]*right(neg)).sum(2)
            loss=-(torch.nn.functional.logsigmoid(pos)+torch.nn.functional.logsigmoid(-negative).sum(1)).mean()
            optimizer.zero_grad();loss.backward();optimizer.step();return float(loss.detach())*len(pairs)
        for walk in walks(edge_index,n,walk_length=config['walk_length'],walks_per_node=config['walks_per_node'],seed=seed):
            for i,node in enumerate(walk):
                for j in range(max(0,i-config['context']),min(len(walk),i+config['context']+1)):
                    if i==j:continue
                    seen+=1
                    if seen<=processed:continue
                    pairs.append((node,walk[j]))
                    if len(pairs)==config['batch_size']:
                        total+=update(pairs);processed+=len(pairs);pairs=[]
                        if time.monotonic()-last>=checkpoint_seconds:save()
        if pairs:total+=update(pairs);processed+=len(pairs)
        logs.append({'epoch':epoch,'loss':total/processed,'positive_pairs':processed});epoch+=1;processed=0;total=0.;save()
    return left.weight.detach().numpy().copy(),logs


def watchyourstep_objective(left,right,q,powers,adjacency,walks_per_node=10.,attention_l2=.01):
    expected=walks_per_node*torch.einsum('k,kij->ij',torch.softmax(q,0),powers)
    score=left@right.T
    return attention_l2*q.square().sum()-(expected*torch.nn.functional.logsigmoid(score)+(adjacency==0)*torch.nn.functional.logsigmoid(-score)).sum()


def watchyourstep(edge_index,n,config,seed,*,max_entries=None,checkpoint=None,resume_state=None,checkpoint_seconds=600.):
    if max_entries is None:raise ValueError('explicit resource-derived allocation ceiling required')
    if not 0<checkpoint_seconds<=600:raise ValueError('checkpoint interval exceeds protocol')
    horizon=config['walk_horizon'];width=config['dimensions']//2
    if n*width*2>max_entries or n*horizon>max_entries:raise ValueError('WatchYourStep state capacity exceeded')
    rng=seed_all(seed);a=adjacency(edge_index,n);degree=np.asarray(a.sum(1)).ravel();isolated=degree==0
    transition=a+sparse.diags(isolated.astype(float));degree=np.asarray(transition.sum(1)).ravel();transition=sparse.diags(1/degree)@transition
    left=nn.Parameter(torch.randn(n,width)*.1);right=nn.Parameter(torch.randn(n,width)*.1);q=nn.Parameter(torch.zeros(horizon))
    optimizer=torch.optim.Adam([left,right,q],lr=config['learning_rate'])
    block=max(1,min(128,max_entries//(n*horizon)));identity=_embedding_identity(edge_index,n,{**config,'block_rows':block},seed)
    logs=[];epoch=0;start=0;total=0.;last=time.monotonic()
    if resume_state is not None:
        if resume_state['identity']!=identity:raise ValueError('embedding checkpoint identity mismatch')
        with torch.no_grad():left.copy_(resume_state['left']);right.copy_(resume_state['right']);q.copy_(resume_state['q'])
        optimizer.load_state_dict(resume_state['optimizer']);restore_rng(resume_state['rng'],rng)
        logs=list(resume_state['logs']);epoch=resume_state['epoch'];start=resume_state['next_row'];total=resume_state['loss_sum']
        for parameter,name in ((left,'left'),(right,'right'),(q,'q')):
            parameter.grad=None if resume_state['grads'][name] is None else resume_state['grads'][name].clone()
    def save():
        nonlocal last
        if checkpoint:checkpoint(epoch,{'identity':identity,'left':left.detach(),'right':right.detach(),'q':q.detach(),'grads':{'left':left.grad,'right':right.grad,'q':q.grad},'optimizer':optimizer.state_dict(),'rng':capture_rng(rng),'logs':logs,'epoch':epoch,'next_row':start,'loss_sum':total})
        last=time.monotonic()
    while epoch<config['epochs']:
        if start==0:
            optimizer.zero_grad();penalty=config['attention_l2']*q.square().sum();penalty.backward();total=float(penalty.detach())
        while start<n:
            end=min(start+block,n);power=sparse.eye(n,format='csr')[start:end];powers=[]
            for _ in range(horizon):
                power=power@transition
                if power.shape[0]*n*horizon>max_entries:raise ValueError('WatchYourStep powers capacity exceeded')
                powers.append(power.toarray())
            p=torch.tensor(np.stack(powers),dtype=torch.float32);adj=torch.tensor(a[start:end].toarray(),dtype=torch.float32)
            loss=watchyourstep_objective(left[start:end],right,q,p,adj,config['walks_per_node'],0.)
            loss.backward();total+=float(loss.detach());start=end
            if start<n and time.monotonic()-last>=checkpoint_seconds:save()
        optimizer.step();logs.append({'epoch':epoch,'objective_sum':total});epoch+=1;start=0;total=0.;save()
    return torch.cat([left,right],1).detach().numpy().copy(),logs


class GINEncoder(nn.Module):
    def __init__(self):
        super().__init__();self.epsilon=nn.ParameterList([nn.Parameter(torch.zeros(())) for _ in range(2)])
        self.layers=nn.ModuleList()
        for width in (4,32):
            first=nn.Linear(width,32);second=nn.Linear(32,32)
            initialize_linear(first);initialize_linear(second);self.layers.append(nn.Sequential(first,nn.ReLU(),second,nn.ReLU()))

    def forward(self,mcm,edge_index,node_mask=None,batch=None):
        valid=torch.ones(len(mcm),dtype=torch.bool,device=mcm.device) if node_mask is None else node_mask
        h=mcm.masked_fill(~valid[:,None],0.)
        if not torch.isfinite(h).all():raise ValueError('nonfinite GIN input')
        source,target=edge_index
        keep=(source!=target)&valid[source]&valid[target];source=source[keep];target=target[keep]
        if batch is not None and (batch[source]!=batch[target]).any():raise ValueError('edge crosses graph batch')
        for epsilon,layer in zip(self.epsilon,self.layers):
            incoming=torch.zeros_like(h).index_add_(0,target,h[source]);h=layer((1+epsilon)*h+incoming);h=h.masked_fill(~valid[:,None],0.)
        return mean_pool(h,valid,batch)
