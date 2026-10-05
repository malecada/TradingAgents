"""Exact lane entry; requires genuine later actual-remote and flat release evidence."""
import argparse,json
from outcome01 import HERE,R,run
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--request',required=True);p.add_argument('--sha256',required=True);a=p.parse_args();raw=R.read(HERE,a.request);R.require(R.digest(raw)==a.sha256,'actual request pin');q=json.loads(raw);ref=q['release'];R.path_name(ref['name']);run(a.request,a.sha256,ref['name'],ref['sha256'])
