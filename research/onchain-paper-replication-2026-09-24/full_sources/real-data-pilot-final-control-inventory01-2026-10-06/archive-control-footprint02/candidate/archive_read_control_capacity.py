"""Pure scalar schema bounds for selected exact packed archive read receipts."""
def require(value,message):
    if not value:raise ValueError(message)
POLICY={'schema_version':1,'format':'packed-archive-read-controls-v1','shard_bytes':4194304}
ROLE_BYTES={'intent.json':748,'verified.json':204,'complete.json':134}
# Names are chunk- +12 decimal digits + '-' + longest leaf(13), <=32B.
FRAME_OVERHEAD=72 # 8 lengths + <=32 name bytes +32 hash

def policy(value):
    require(type(value) is dict and value==POLICY and type(value['schema_version']) is int,'exact packed archive read policy required')
    return dict(value)

def capacity(chunks, selection):
    require(type(chunks) is int and 0<chunks<10**12,'finite archive read chunk bound')
    if selection is None:return {'logical_bytes':(3*chunks+8)*8192,'files':3*chunks+8,'directories':chunks,'journal_bytes':None}
    p=policy(selection)
    size=chunks*(sum(ROLE_BYTES.values())+3*FRAME_OVERHEAD)+4*(8192+FRAME_OVERHEAD)
    # A next largest frame may close a shard. Failure markers remain full8192.
    shards=1+size//(p['shard_bytes']-(8192+FRAME_OVERHEAD))
    return {'logical_bytes':size+8*8192,'files':shards+8,'directories':1,'journal_bytes':size}
