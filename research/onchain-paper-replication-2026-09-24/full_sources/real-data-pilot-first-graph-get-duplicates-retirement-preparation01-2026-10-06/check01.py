"""Finite metadata controls; never invokes execute, unlink, systemd or payload hashing."""
from pathlib import Path
import copy, json, os, tempfile
import retire01 as r


def refuses(call, text):
    try:call()
    except ValueError as e:assert text in str(e),str(e)
    else:raise AssertionError('expected refusal')


def main():
    here=Path(__file__).resolve().parent;c=json.loads((here/'SELECTION_DRAFT01.json').read_text())
    original,gets=r.selected(Path.cwd(),c)
    assert len(original)==len(gets)==5 and sum(x['recovered']['bytes'] for x in c['rows'])==509060512
    changed=copy.deepcopy(c);changed['rows'][0]['recovered']['path']=changed['rows'][0]['original']['path']
    refuses(lambda:r.selected(Path.cwd(),changed),'only exact array gets')
    changed=copy.deepcopy(c);changed['rows'][0]['index']=11
    refuses(lambda:r.selected(Path.cwd(),changed),'fixed five indices')
    with tempfile.TemporaryDirectory(dir=here) as t:
        root=Path(t);p=root/'tiny';p.write_bytes(b'fixture');s=p.stat()
        row={'path':'tiny','bytes':s.st_size,'mode':s.st_mode&0o777,'stat_identity':r.identity(s)}
        assert r.current(root,row)==p
        os.link(p,root/'alias');refuses(lambda:r.current(root,row),'stat/mode/nlink');(root/'alias').unlink()
        s=p.stat();row['stat_identity']=r.identity(s);p.write_bytes(b'changed fixture');refuses(lambda:r.current(root,row),'stat/mode/nlink')
    print(json.dumps({'passed':5,'checks':['actual exact five stat-only joins','original substitution refuses','ledger index refuses','tiny hardlink refuses','tiny mutation refuses'],'actual_retirement':False,'actual_payload_body_reads':False},indent=2))


if __name__=='__main__':main()
