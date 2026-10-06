"""Pure metadata fixtures only; no genuine authority, payload transfer or numerical imports."""
import hashlib
import json
from pathlib import Path
import tempfile
import prepare01 as p


def write(root, name, value):
    path = root/name; path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(value, sort_keys=True).encode(); path.write_bytes(raw)
    return {'path':name, 'sha256':hashlib.sha256(raw).hexdigest()}


def fixture(root, status):
    for r in p.ROOTS: (root/r).mkdir(parents=True)
    claim = write(root,p.ROOTS[0]+'/claim.json',{'experiment_id':p.GRAPH,'program_id':p.PROGRAM,'source':p.SOURCE})
    terminal = write(root,p.ROOTS[0]+'/'+status+'.json',{'experiment_id':p.GRAPH,'source':p.SOURCE,'claim_sha256':claim['sha256'],'status':status,'cells':[]})
    guard = write(root,p.ROOTS[1]+'/guard/final.json',{'cleanup_verified':True,'phase':status,'child_exit_code':0 if status=='complete' else 1})
    index = write(root,p.ROOTS[0]+'/outputs/artifact-index.json',{})
    payload=root/p.ROOTS[2]/'opaque.bin';payload.write_bytes(b'pure fixture')
    s=payload.stat();row={'path':str(payload.relative_to(root)),'bytes':s.st_size,'sha256':hashlib.sha256(b'pure fixture').hexdigest(),'stat_identity':[s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns]}
    bodies=write(root,'bodies.json',{'decision':'pass','index_sha256':index['sha256'],'files':[row],'total_bytes':s.st_size})
    review=write(root,'review.json',{'decision':'accepted','experiment':p.GRAPH,'source':p.SOURCE,'claim_sha256':claim['sha256'],'cleanup':{'guard_cleanup_verified':True,'recorded_cgroup_absent':True},'evidence':{x['path']:x['sha256'] for x in [terminal,guard,index,bodies]}})
    return review,bodies,payload


def refused(call, match):
    try:call()
    except ValueError as e:assert match in str(e), str(e)
    else:raise AssertionError('refusal absent')


def main():
    here=Path(__file__).resolve().parent
    results=[]
    with tempfile.TemporaryDirectory(dir=here) as temp:
        root=Path(temp);refused(lambda:p.select(root,{},{}),'closed unambiguous');results.append('active refuses before evidence/output reads')
    for status in ['complete','failed']:
        with tempfile.TemporaryDirectory(dir=here) as temp:
            root=Path(temp);review,bodies,payload=fixture(root,status)
            original=p.metadata
            def bounded(root,relative,digest=None):
                assert relative!=str(payload.relative_to(root)), 'payload body read'
                return original(root,relative,digest)
            p.metadata=bounded
            try:
                result=p.select(root,review,bodies);assert result['graph_terminal_status']==status and result['graph_terminal_cells']==[];results.append(status+' honest selection without payload reads')
                payload.write_bytes(b'changed');refused(lambda:p.select(root,review,bodies),'payload stat');results.append(status+' changed payload stat refuses')
            finally:p.metadata=original
    with tempfile.TemporaryDirectory(dir=here) as temp:
        root=Path(temp);review,bodies,payload=fixture(root,'complete');refused(lambda:p.select(root,review,{**bodies,'sha256':'0'*64}),'not anchored');results.append('unanchored body evidence refuses')
    with tempfile.TemporaryDirectory(dir=here) as temp:
        root=Path(temp);review,bodies,payload=fixture(root,'failed')
        import shutil
        shutil.rmtree(root/p.ROOTS[2])
        value=json.loads((root/bodies['path']).read_text());value['files']=[];value['total_bytes']=0
        bodies=write(root,bodies['path'],value)
        value=json.loads((root/review['path']).read_text());value['evidence'][bodies['path']]=bodies['sha256'];review=write(root,review['path'],value)
        selected=p.select(root,review,bodies);assert selected['absent_original_roots']==[p.ROOTS[2]] and selected['graph_terminal_status']=='failed';results.append('failed absent source preserved explicitly without fabricated directory')
    inverse=json.loads((here/'INVERSE01.json').read_text());text=(here/'entry01.py').read_text()
    for a,b in reversed(inverse['substitutions']):text=text.replace(b,a)
    assert hashlib.sha256(text.encode()).hexdigest()==inverse['baseline_sha256'];results.append('entry exact literal inverse')
    import keep
    import shutil
    primitives=keep.bind_primitives(Path.cwd())
    class Transport:
        def __init__(self, bad=False): self.objects={}; self.bad=bad
        def put(self, source, target): self.objects[target]=source.read_bytes()
        def get(self, source, target): target.write_bytes(b'bad' if self.bad else self.objects[source])
    for bad in (False, True):
        with tempfile.TemporaryDirectory(dir=here) as temp:
            root=Path(temp); target=root/'recover';target.mkdir(); source=root/'fixture.bin';source.write_bytes(b'tiny synthetic body')
            st=source.stat(); row={'path':'fixture.bin','bytes':st.st_size,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'stat_identity':p.identity(st),'mode':st.st_mode & 0o777,'nlink':1}
            call=lambda:keep.keep_one(root,target,row,0,'synthetic',Transport(bad),primitives=primitives)
            if bad:refused(call,'round-trip mismatch')
            else:
                record=call();assert record['original_retained'] and record['recovered_body_retained'];assert (target/'00-recovered.bin').read_bytes()==source.read_bytes()
            assert source.read_bytes()==b'tiny synthetic body' and sorted(x.name for x in root.iterdir())==['fixture.bin','recover']
            results.append('keep mismatch retains original' if bad else 'keep retains original and successful fresh recovery without sidecar')
    inverse=json.loads((here/'KEEP_INVERSE01.json').read_text());a,b=inverse['substitution'];assert hashlib.sha256((here/'keep.py').read_text().replace(b,a).encode()).hexdigest()==inverse['baseline_sha256'];results.append('keep exact constant inverse')
    print(json.dumps({'checks':results,'passed':len(results),'scientific_claim':False},indent=2))


if __name__=='__main__':main()
