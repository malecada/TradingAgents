from pathlib import Path
import hashlib,json,ast,difflib
D=Path(__file__).resolve().parent;P=Path('tradingagents/research/onchain_replication');B=D.parent/'real-data-pilot-model-entry-composition01-2026-10-05';origin=B/'candidate'/P/'real_pilot_import_caller.py'
sha=lambda b:hashlib.sha256(b).hexdigest();raw=origin.read_bytes()
manifest=json.loads((B/'MANIFEST01.json').read_text());entry=next(r for r in manifest['members'] if r['path']==str(Path('candidate')/P/'real_pilot_import_caller.py'))
assert sha(raw)==entry['sha256']=='e3e5bd544d470e870780305a9ed3bfdb8b669c703a921a34baf9175552272593'
s=raw.decode()
def change(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
change('    terminal = training = None; primary = None',"    from .real_pilot_throughput import MCMMeasurements\n    measurements = MCMMeasurements({key:len(g.node_ids) for key,g in graphs.items()},\n        population_scope=p.get('population_scope','full_fold_input'))\n    terminal = training = None; primary = None")
change('            watch.check()\n            result = compact_mcm.produce_imported', '            watch.check()\n            measurements.begin(key)\n            result = compact_mcm.produce_imported')
change('            targets.append(result); result.check(); resource_fixture.verify_retained(result,owner)', '            targets.append(result); result.check()\n            retained = resource_fixture.verify_retained(result,owner)\n            measurements.completed(key,retained)')
change('    except BaseException as error:\n        primary = error\n        if journal is not None', '    except BaseException as error:\n        primary = error\n        try: measurements.failed(error)\n        except BaseException as later: primary = resource_fixture._preserve_terminal(primary,later)\n        if journal is not None')
change('    # Independently attempt each remaining publication; retain the first fatal.', '    throughput = None\n    try: throughput = measurements.summary(training)\n    except BaseException as later: primary = resource_fixture._preserve_terminal(primary,later)\n    # Independently attempt each remaining publication; retain the first fatal.')
change("'full_graphs':7,'retained_target_count':len(targets),'training':training,'events':events,", "'full_graphs':7,'retained_target_count':len(targets),'training':training,'events':events,\n               'throughput':throughput,")
new=s.encode();ast.parse(new)
(D/'caller.baseline.py').write_bytes(raw);(D/'candidate'/P/'real_pilot_import_caller.py').write_bytes(new)
a=raw.decode().splitlines(True);b=s.splitlines(True);edits=[{'old_start':i,'old_end':j,'new_start':k,'new_end':l,'old':a[i:j],'new':b[k:l]} for op,i,j,k,l in difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes() if op!='equal'];inv=b[:]
for e in reversed(edits):assert inv[e['new_start']:e['new_end']]==e['new'];inv[e['new_start']:e['new_end']]=e['old']
assert ''.join(inv).encode()==raw
(D/'caller.patch').write_text(''.join(difflib.unified_diff(a,b,fromfile='a/'+str(P/'real_pilot_import_caller.py'),tofile='b/'+str(P/'real_pilot_import_caller.py'))))
(D/'SOURCE_DELTA01.json').write_text(json.dumps({'schema_version':1,'origin':str(origin),'origin_sha256':sha(raw),'origin_manifest_sha256':sha((B/'MANIFEST01.json').read_bytes()),'candidate_sha256':sha(new),'helper_sha256':sha((D/'candidate'/P/'real_pilot_throughput.py').read_bytes()),'edits':edits,'execution_authority':False},indent=2,sort_keys=True)+'\n')
print(json.dumps({'caller':sha(new),'helper':sha((D/'candidate'/P/'real_pilot_throughput.py').read_bytes())}))
