"""Selected finite geometry metadata publication; no scientific authority."""
import json
from .geometry_summary import BINS,NAMES,LIMIT,raw,require
FORMAT='provisional-pair-geometry-v1'
POLICY={'format':FORMAT,'max_body_bytes':1536}
def policy(value):
    if value is None or value is False:return None
    require(type(value) is dict and set(value)==set(POLICY) and type(value['format']) is str and type(value['max_body_bytes']) is int and value==POLICY,'explicit geometry publication policy required')
    return dict(value)
def check(value,selected,start,stop,computed,reused):
    selected=policy(selected);require(selected is not None,'geometry selection required')
    require(type(value) is dict and set(value)=={'format','start','stop','computed','reused','bins_upper_inclusive','metrics','static_shape_only','runtime_eligibility_proved','scientific_authority','end_batch_attested'},'geometry fields differ')
    require(len(raw(value))<=selected['max_body_bytes'],'geometry body cap')
    require(value['format']==FORMAT and value['bins_upper_inclusive']==list(BINS) and all(type(x) is int for x in value['bins_upper_inclusive']),'geometry format/bins')
    require(all(type(value[k]) is int for k in ('start','stop','computed','reused')) and (value['start'],value['stop'],value['computed'],value['reused'])==(start,stop,computed,reused) and 0<=start<stop<=LIMIT and 0<stop-start<=4096 and computed>=0 and reused>=0 and computed+reused==stop-start,'geometry range/disposition')
    require(value['runtime_eligibility_proved'] is False and value['scientific_authority'] is False and value['end_batch_attested'] is True,'geometry qualification differs')
    count=stop-start
    require(type(value['metrics']) is dict and set(value['metrics'])==set(NAMES),'geometry metric names')
    for metric in value['metrics'].values():
        require(type(metric) is dict and set(metric)=={'sum','max','histogram'} and all(type(metric[k]) is int and 0<=metric[k]<=LIMIT for k in ('sum','max')),'geometry metric fields')
        h=metric['histogram'];require(type(h) is list and len(h)==len(BINS) and all(type(n) is int and 0<=n<=count for n in h) and sum(h)==count,'geometry histogram cardinality')
        require(metric['max']<=metric['sum']<=count*metric['max'],'geometry sum/max bounds')
        bucket=next(i for i,bound in enumerate(BINS) if metric['max']<=bound)
        require(h[bucket]>0 and not any(h[bucket+1:]),'geometry maximum histogram mismatch')
    shapes=value['static_shape_only'];require(type(shapes) is dict and set(shapes)=={'batched02_two_pair_scratch','compiled04_matrix_shape'} and all(type(n) is int and 0<=n<=count for n in shapes.values()),'geometry static counts')
    return value

def completed(body,selected,start,stop,computed,reused):
    selected=policy(selected)
    require(type(body) is bytes and len(body)<=selected['max_body_bytes'],'completed geometry bytes required')
    value=json.loads(body);require(raw(value)==body,'completed geometry canonical bytes differ')
    return check(value,selected,start,stop,computed,reused)
