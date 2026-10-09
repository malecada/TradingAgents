"""Finite provisional geometry only; no feature reads or runtime eligibility claim."""
import json
LIMIT=2**63-1
BINS=(0,4,16,64,256,1024,4096,65536,LIMIT)
NAMES=('left_nodes','right_nodes','left_edges','right_edges','matrix_product','edge_product')
def require(ok,message):
    if not ok:raise ValueError(message)
def raw(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
class Geometry:
    def __init__(self,max_bytes):
        require(type(max_bytes) is int and 1<=max_bytes<=8192,'geometry summary byte bound required')
        self.max_bytes=max_bytes;self.data=None
    def begin(self,ordinal):
        require(type(ordinal) is int and 0<=ordinal<=LIMIT,'geometry ordinal bound')
        self.data={'format':'provisional-pair-geometry-v1','start':ordinal,'stop':ordinal,'computed':0,'reused':0,'bins_upper_inclusive':list(BINS),'metrics':{k:{'sum':0,'max':0,'histogram':[0]*len(BINS)} for k in NAMES},'static_shape_only':{'batched02_two_pair_scratch':0,'compiled04_matrix_shape':0},'runtime_eligibility_proved':False,'scientific_authority':False,'end_batch_attested':False}
    def add(self,a,b,receipt):
        d=self.data;require(d is not None,'geometry batch unavailable')
        ordinal=receipt['ordinal'];mode=receipt['mode']
        require(type(ordinal) is int and ordinal==d['stop'] and ordinal<LIMIT and ordinal-d['start']<4096,'geometry occurrence range bound')
        require(type(mode) is str and mode in ('computed','reused'),'geometry disposition')
        dims=(len(a.node_ids),len(b.node_ids),a.edge_index.shape[1],b.edge_index.shape[1])
        require(all(type(x) is int and 0<=x<=LIMIT for x in dims),'geometry dimension bound')
        n,m,ea,eb=dims;values=(*dims,n*m,ea*eb)
        require(all(x<=LIMIT and d['metrics'][k]['sum']<=LIMIT-x for k,x in zip(NAMES,values)),'geometry product/sum bound')
        for k,x in zip(NAMES,values):
            metric=d['metrics'][k];metric['sum']+=x;metric['max']=max(metric['max'],x)
            metric['histogram'][next(i for i,bound in enumerate(BINS) if x<=bound)]+=1
        d[mode]+=1;d['stop']+=1
        d['static_shape_only']['batched02_two_pair_scratch']+=int(1<=n<=16 and 1<=m<=16 and 0<ea*eb<=1024 and 65536+2*(536*n*m+64*ea*eb+8)<=262144)
        d['static_shape_only']['compiled04_matrix_shape']+=int(1<=n<=4 and 1<=m<=4)
    def finish(self,stop,computed,reused):
        d=self.data;require(d is not None and (d['stop'],d['computed'],d['reused'])==(stop,computed,reused),'geometry completed disposition mismatch')
        d['end_batch_attested']=True
        body=raw(d);require(len(body)<=self.max_bytes,'geometry serialized summary exceeds bound')
        self.data=None;return body
    def poison(self):self.data=None
