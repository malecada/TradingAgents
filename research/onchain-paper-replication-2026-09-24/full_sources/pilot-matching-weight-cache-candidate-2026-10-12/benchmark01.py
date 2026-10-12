"""Root-only unexecuted baseline-v1/selected-v2 synthetic solver benchmark."""
import argparse,json,resource,hashlib
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--config-sha256',required=True);p.add_argument('--budget',type=int,default=1000000);args=p.parse_args()
 from numeric_harness import config,graph,solve,compare,P
 c=config(args.config,args.config_sha256);rows=[]
 for left,right in ((32,32),(128,128),(256,512),(1024,1024)):
  a=graph(left);b=graph(right,.031);old=solve(a,b,c,1,budget=args.budget);new=solve(a,b,c,2,budget=args.budget)
  row=compare(old,new);row.update(left_edges=left,right_edges=right,edge_products=left*right,v1=old[2],v2=new[2]);rows.append(row)
 print(json.dumps({'scope':'synthetic original48-temperature full-solver only; no empirical authority',
  'config_sha256':args.config_sha256,'candidate_sha256':hashlib.sha256((P/'matching_numeric_policy.py').read_bytes()).hexdigest(),
  'cases':rows,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'native_caps_changed':False},sort_keys=True,indent=2))
if __name__=='__main__':main()
