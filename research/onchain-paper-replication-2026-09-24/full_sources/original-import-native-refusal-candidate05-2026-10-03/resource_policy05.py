"""Finite declared resource policy; scalar checks only, not RSS proof."""
CONSTRUCTOR_PATH='tradingagents/research/onchain_replication/array_neighborhoods.py'
CONSTRUCTOR_SHA256='4130af3869fb6615ba0898c5b25f1297f236e2df6b4dbe37d705dc2459982d6d'
NUMERIC={'schema_version':1,'max_buffer_bytes':1048576,'edge_chunk':4096,'max_output_bytes':1048576,'max_numeric_bytes':2097152}
def validate(numeric,n,e,node_width,edge_width):
    if type(numeric) is not dict or set(numeric)!=set(NUMERIC) or any(type(numeric[k]) is not int or numeric[k]!=v for k,v in NUMERIC.items()):raise ValueError('exact declared refusal numeric policy required')
    if any(type(x) is not int or x<0 for x in (n,e,node_width,edge_width)) or (n,e,node_width,edge_width) not in ((2,2,32,16),(3,3,32,16)):raise ValueError('exact registered tiny graph extents required')
    edge_chunk=numeric['edge_chunk']
    allowance=16*(e+n+1)+16*e+40*(n+1)+4*n+edge_chunk*(64+2*node_width+2*edge_width)
    if allowance>numeric['max_buffer_bytes']:raise ValueError('neighborhood index buffer allowance exceeded')
    return allowance
