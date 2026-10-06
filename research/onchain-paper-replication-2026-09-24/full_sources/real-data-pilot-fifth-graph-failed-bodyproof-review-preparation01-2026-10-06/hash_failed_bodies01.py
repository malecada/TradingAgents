"""Root-only one fresh failed-scope byte capture; never replay or decode arrays."""
import argparse,ast,hashlib,json,os,stat
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
GRAPH='eth-paper-real-pilot-graph-20220530-20261005-01'
BASE='research_artifacts/onchain-paper-replication-2026-09-24/sources/'+GRAPH
FILES={BASE+'/aggregation/ledger.sqlite':3189231616,BASE+'/graph-2022-05-30/edge_index.npy':38817824,BASE+'/graph-2022-05-30/node_features.npy':50606240}
FAILED='f5e452d0352424a13db233a914ffb1ce742244a49de0481ef1b011459b2b569b'
def identity(s):return [s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
def header(prefix,extent):
    # Header validity is only an observation. Partial scientific arrays stay partial.
    try:
        if prefix[:6]!=b'\x93NUMPY':raise ValueError('NPY magic unavailable')
        version=list(prefix[6:8]);assert version in ([1,0],[2,0],[3,0])
        width=2 if version==[1,0] else 4;offset=8+width;size=int.from_bytes(prefix[8:offset],'little')
        assert offset+size<=len(prefix)
        m=ast.literal_eval(prefix[offset:offset+size].decode('utf-8' if version==[3,0] else 'latin1'))
        assert type(m) is dict and set(m)=={'descr','fortran_order','shape'}
        return {'status':'observed-header-only','version':version,'header_bytes':offset+size,**m,'observed_file_bytes':extent,'scientific_completion':False}
    except (ValueError,AssertionError,SyntaxError,UnicodeError,TypeError) as error:
        return {'status':'partial-or-invalid-header','error_type':type(error).__name__,'scientific_completion':False}
def main(output):
    output=output.absolute();assert output.parent.resolve(strict=True)==output.parent and output.is_relative_to(ROOT)
    assert output.suffix=='.json' and not os.path.lexists(output)
    progress=output.with_name(output.name+'.progress.jsonl');assert not os.path.lexists(progress)
    terminal=ROOT/'research_runs'/GRAPH/'failed.json'
    assert hashlib.sha256(terminal.read_bytes()).hexdigest()==FAILED and not terminal.with_name('complete.json').exists()
    assert not (ROOT/BASE/'graph-2022-05-30/manifest.json').exists() and not (ROOT/BASE/'aggregation/complete.json').exists()
    before={}
    for rel,size in FILES.items():
        p=ROOT/rel;s=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==size;before[rel]=s
    rows=[]
    with progress.open('x') as log:
        def record(value):log.write(json.dumps(value,sort_keys=True)+'\n');log.flush();os.fsync(log.fileno())
        record({'status':'one-pass-reserved','graph':GRAPH,'bodies':FILES,'no_automatic_retry':True})
        try:
            for rel,size in FILES.items():
                p=ROOT/rel;s=before[rel];digest=hashlib.sha256();count=0;prefix=b''
                with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOFOLLOW),'rb') as stream:
                    assert identity(os.fstat(stream.fileno()))==identity(s)
                    while chunk:=stream.read(1024**2):
                        if not prefix:prefix=chunk[:65536]
                        digest.update(chunk);count+=len(chunk)
                    assert identity(os.fstat(stream.fileno()))==identity(s)
                assert identity(p.lstat())==identity(s) and count==size
                row={'path':rel,'bytes':count,'sha256':digest.hexdigest(),'stat_identity':identity(s),'mode':stat.S_IMODE(s.st_mode)}
                if rel.endswith('.npy'):row['npy_header']=header(prefix,count)
                rows.append(row);record({'status':'body-hashed','row':row})
            assert all(identity((ROOT/rel).lstat())==identity(s) for rel,s in before.items())
            result={'decision':'pass','index_sha256':None,'files':rows,'total_bytes':sum(r['bytes'] for r in rows),'one_streaming_pass_per_body':True,'headers_captured_same_pass':2,'qualification':'Stable bytes of actual failed ledger/two partial arrays only. No prior artifact digest exists for comparison; no valid complete graph or scientific matrix claimed.','numerical_imports':False,'raw_daily_body_reads':False}
            with output.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
            record({'status':'proof-written','path':str(output.relative_to(ROOT)),'sha256':hashlib.sha256(output.read_bytes()).hexdigest()})
        except BaseException as error:
            try:record({'status':'failed','error_type':type(error).__name__,'completed_bodies':len(rows),'no_automatic_retry':True})
            except BaseException as secondary:error.add_note('Proof progress retention failed: '+repr(secondary))
            raise
    print(json.dumps({'proof':str(output.relative_to(ROOT)),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'bytes':result['total_bytes'],'bodies':len(rows)}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
