from pathlib import Path
import hashlib,json,difflib,ast
P=Path(__file__).resolve().parent;R=P.parents[3];source=R/'tradingagents/research/onchain_replication/matching_annealing.py';a=source.read_bytes()
old=b'                    u,v=a.edge_index[:,left];i,j=b.edge_index[:,right]\n'
new=b'''                    if (type(a.edge_index) is np.ndarray and type(b.edge_index) is np.ndarray
                            and type(left) is np.ndarray and type(right) is np.ndarray
                            and not a.edge_index.flags.writeable and not b.edge_index.flags.writeable):
                        u=a.edge_index[0,left];v=a.edge_index[1,left]
                        i=b.edge_index[0,right];j=b.edge_index[1,right]
                    else:
                        u,v=a.edge_index[:,left];i,j=b.edge_index[:,right]
'''
assert a.count(old)==1;b=a.replace(old,new);assert b.replace(new,old)==a
(P/'BASELINE_matching_annealing.py').write_bytes(a);(P/'matching_annealing.py').write_bytes(b)
for name,x,y,xf,yf in [('CANDIDATE01.diff',a,b,'a/'+str(source.relative_to(R)),'b/'+str(source.relative_to(R))),('INVERSE01.diff',b,a,'b/'+str(source.relative_to(R)),'a/'+str(source.relative_to(R)))]:
 (P/name).write_text(''.join(difflib.unified_diff(x.decode().splitlines(True),y.decode().splitlines(True),fromfile=xf,tofile=yf)))
compile(b,str(P/'matching_annealing.py'),'exec')
