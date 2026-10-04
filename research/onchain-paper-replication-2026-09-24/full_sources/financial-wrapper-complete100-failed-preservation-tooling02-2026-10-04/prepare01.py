from pathlib import Path
import ast,hashlib,json,shutil
D=Path(__file__).resolve().parent;O=D.parent/'financial-wrapper-complete100-failed-preservation-tooling01-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();shutil.copytree(O/'utilities',D/'utilities');records={}
for name in ('recover01.py','restore01.py'):
 raw=(O/name).read_bytes();(D/('ORIGINAL_'+name)).write_bytes(raw);s=raw.decode();ed=[]
 def change(old,new):
  global s
  assert s.count(old)==1,(old[:80],s.count(old));s=s.replace(old,new);ed.append({'old':old,'new':new})
 if name=='recover01.py':
  change('import time\n','import time\nimport resource\nimport watch01 as W\n')
  change('CALLS = []','CALLS = []\nWATCHES = []\nBASELINE = None\n\ndef watch():\n    global BASELINE\n    require(len(WATCHES) < W.POLICY[\'samples\'] and time.monotonic()-START < 600, \'finite whole-tree supervision\')\n    row = W.census(HERE)\n    if BASELINE is None: BASELINE = dict(row)\n    WATCHES.append(row)\n    return row')
  change("    require(len(body) <= FILE, 'per selected body bound')","    watch()\n    require(len(body) <= FILE, 'per selected body bound')")
  change("    require(path.read_bytes() == body, 'actual saved-byte readback')","    require(path.read_bytes() == body, 'actual saved-byte readback')\n    watch()")
  change('    child = poller = None','    child = poller = None\n    ready_read = ready_write = None\n    ready = None')
  change("    try:\n        child = subprocess.Popen(['git', *args], cwd=cwd, env=env,", "    try:\n        watch()\n        ready_read, ready_write = os.pipe()\n        def limits():\n            resource.setrlimit(resource.RLIMIT_FSIZE, (FILE, FILE))\n            actual = resource.getrlimit(resource.RLIMIT_FSIZE)\n            require(actual == (FILE, FILE), 'actual child hard/soft FSIZE')\n            os.write(ready_write, encode({'pid':os.getpid(),'fsize':list(actual)}))\n            os.close(ready_write)\n        child = subprocess.Popen(['git', *args], cwd=cwd, env=env,")
  change('stderr=subprocess.PIPE, start_new_session=True)','stderr=subprocess.PIPE, start_new_session=True, preexec_fn=limits, pass_fds=(ready_write,))\n        os.close(ready_write); ready_write = None\n        ready_raw = os.read(ready_read, 512)\n        os.close(ready_read); ready_read = None\n        ready = json.loads(ready_raw)\n        require(ready == {\'pid\':child.pid,\'fsize\':[FILE, FILE]}, \'genuine child OS limit readback\')')
  change('        while poller.get_map():','        while poller.get_map():\n            watch()')
  change("        require(code == 0, 'actual Git operation failed')","        require(code == 0, 'actual Git operation failed')\n        watch()")
  change('    failures = []\n    for action in actions:','    if ready_read is not None: actions.append(lambda: os.close(ready_read))\n    if ready_write is not None: actions.append(lambda: os.close(ready_write))\n    actions.append(watch)\n    failures = []\n    for action in actions:')
  change("'exit': code, 'seconds': time.monotonic() - begun,","'exit': code, 'seconds': time.monotonic() - begun, 'actual_child_limits':ready,")
  change('fresh-complete100-failed-outcome02-01.git','fresh-complete100-failed-outcome02-02.git')
  change("    git(['fetch', '--no-tags', 'origin', *wanted], repo)","    for oid in wanted:\n        git(['fetch', '--no-tags', 'origin', oid], repo)")
  change("len(CALLS) == 11 + 2*len(rows)","len(CALLS) == 10 + len(wanted) + 2*len(rows)")
  change("    receipt = {'schema_version': 1,", "    watch()\n    receipt = {'whole_tree_policy':dict(W.POLICY),'initial_owned_allocation':BASELINE,'whole_tree_observations':list(WATCHES),'unique_selected_objects':len(wanted),'expected_operations':10+len(wanted)+2*len(rows),'schema_version': 1,")
  change('fresh-actual-remote-complete100-failed-outcome02-recovered','fresh-actual-remote-complete100-failed-outcome02-supervised-recovered')
  change('Selected bodies are bounded4MiB; writable Git pack extents are not universally bounded4MiB and require separate actual readback.','Every receiver child inherits actual-readback hard/soft4MiB FSIZE; entire owned tree including baseline sampled at fixed64MiB logical/96MiB allocated/32768members/depth32. Single-blob fetches and exact dynamic unique-object operation denominator; transient aggregate/physical wire not measured.')
 else:
  change('fresh-actual-remote-complete100-failed-outcome02-recovered','fresh-actual-remote-complete100-failed-outcome02-supervised-recovered')
  change("len(remote['operations']) == 11 + 2 * len(rows)","len(remote['operations']) == remote['expected_operations'] == 10 + len({row['git_object'] for row in records}) + 2 * len(rows) and remote['unique_selected_objects'] == len({row['git_object'] for row in records})")
 (D/name).write_text(s);inverse=s
 for e in reversed(ed):assert inverse.count(e['new'])==1;inverse=inverse.replace(e['new'],e['old'])
 assert inverse.encode()==raw and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(raw));records[name]={'original_sha256':sha(raw),'candidate_sha256':sha(s.encode()),'edits':ed,'whole_byte_AST_inverse':True}
(D/'SOURCE_INVERSE01.json').write_text(json.dumps(records,indent=2)+'\n');(D/'REQUIRED_BODIES01.json').write_bytes((O/'REQUIRED_BODIES01.json').read_bytes());print('source built')
