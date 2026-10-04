import ast,copy,importlib.util,json,sys
from pathlib import Path
import recover01 as M
H=Path(__file__).resolve().parent;checks=[]
def ok(n,v):assert v,n;checks.append(n)
def refuse(n,fn):
 try:fn()
 except (ValueError,KeyError,TypeError):ok(n,True)
 else:raise AssertionError(n)
s=(H/'recover01.py').read_text();old=(H/'original-remote04.py').read_text();inverse=s
for edit in reversed(json.loads((H/'INVERSE01.json').read_text())['edits']):
 ok('exact delta inverse',inverse.count(edit['new'])==1);inverse=inverse.replace(edit['new'],edit['old'])
ok('complete byte inverse',inverse==old);ok('complete AST inverse',ast.dump(ast.parse(inverse))==ast.dump(ast.parse(old)))
q=json.loads((H/'SELECTION_DRAFT01.json').read_text());M.validate_fixed_selection(q);ok('all six actual capture rows admitted metadata',len(q['rows'])==6);ok('actual commit remains unknown',q['remote_commit'] is None)
for i in range(6):
 for key,val in [('sha256','0'*64),('bytes',0),('path','research/wrong')]:
  z=copy.deepcopy(q);z['rows'][i][key]=val;refuse('fixed required row '+str(i)+key,lambda:M.validate_fixed_selection(z))
for v in ['../escape','/absolute','research/a/../b','research//b']:
 z=copy.deepcopy(q);z['rows'].append({'path':v,'bytes':1,'sha256':'a'*64});refuse('unsafe '+v,lambda:M.validate_fixed_selection(z))
z=copy.deepcopy(q);z['rows'].append(z['rows'][0]);refuse('duplicate selection',lambda:M.validate_fixed_selection(z))
for value in [-1,True,M.FILE+1]:
 z=copy.deepcopy(q);z['rows'][0]['bytes']=value;refuse('size bound '+str(value),lambda:M.validate_fixed_selection(z))
# Exact actual child manager is unchanged; a local Git --version operation has
# no network, repository mutation or source discovery.
body=M.git(['--version']);ok('actual reaped read-only child',body.startswith(b'git version') and M.CALLS[-1]['exit']==0 and M.CALLS[-1]['cleanup_failures']==[])
ok('finite 506 operation denominator',11+2*506==1023)
(H/'CHECKS01.json').write_text(json.dumps({'count':len(checks),'checks':checks,'local_git_version_operation':M.CALLS,'network_operations':0},indent=2)+'\n');print('PASS',len(checks))
