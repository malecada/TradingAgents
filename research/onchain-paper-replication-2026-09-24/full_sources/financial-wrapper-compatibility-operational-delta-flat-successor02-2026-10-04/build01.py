from pathlib import Path
import json,hashlib,ast
O=Path(__file__).resolve().parent;F=O.parent;T=F/'financial-wrapper-compatibility-operational-delta-flat-tooling01-2026-10-04';C=F/'financial-wrapper-compatibility-operational-delta-failed-remote-capture02-2026-10-04';R=F.parents[2];h=lambda b:hashlib.sha256(b).hexdigest();old=(T/'restore01.py').read_text();assert h(old.encode())=='b8c16007f3945e30d1a1a4889504f1ed5cfc77256f4c03f7cbd8a4a7ac28659d'
(O/'ORIGINAL_restore01.py').write_text(old);U=O/'utilities';U.mkdir(mode=0o700)
for n in ['recovery_pax01.py','owned_io.py','bounded_git01.py']:(U/n).write_bytes((T/'utilities'/n).read_bytes())
req=json.loads((T/'ORIGINAL_REMOTE_REQUIRED_BODIES01.json').read_bytes())
for n in ['CAPTURE01.json','FAILED_PAYLOAD_MANIFEST01.json','failed-remote02.tar.gz','ORIGINAL_FAILED_ROOT_SCOPE43.json','root_remote_failure_capture02.py']:
 p=C/n;b=p.read_bytes();req[p.relative_to(R).as_posix()]={'bytes':len(b),'sha256':h(b)}
req=dict(sorted(req.items()));total=sum(x['bytes'] for x in req.values());assert len(req)==15
s=old;tree=ast.parse(s);node=next(x for x in tree.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='REQUIRED' for t in x.targets));lines=s.splitlines(True);lines[node.lineno-1:node.end_lineno]=['REQUIRED = '+repr(req)+'\n'];s=''.join(lines)
s=s.replace('cd2200b071cf14c8191c7b7e95ee660b6bc9a10c49a6de252e77f9832ede8673','bdeacaadc053e615245b3e2175089842708719448ec7da970d981e5dc077ca18')
s=s.replace("OUTPUT = 'flat-operational-delta01'","OUTPUT = 'flat-operational-delta01'\nFAILED_OUTPUT = 'flat-failed-remote02-01'\nFAILED_REL = '"+C.relative_to(R).as_posix()+"'\nFAILED_CAPTURE = '58d76ef3d7da87994ec7052e1d16c6facadcfd53535c15fe7532956515eab740'")
s=s.replace('== len(REQUIRED) == 10','== len(REQUIRED) == 15').replace('exact ten selected rows','exact fifteen selected rows').replace('451691',str(total)).replace('len(records) == 10','len(records) == 15').replace("remote['selected_count'] == 10","remote['selected_count'] == 15").replace("['cat-file','cat-file'] * 10","['cat-file','cat-file'] * 15").replace('fresh-operational-source-policy01.git','fresh-operational-source-policy02.git')
# Typed pins must not accept int/float/bool aliases from caller metadata.
s=s.replace("    R.require(rows == expected,", "    R.require(all(type(row) is dict and set(row)=={'path','bytes','sha256'} and type(row['path']) is str and type(row['bytes']) is int and type(row['sha256']) is str for row in rows), 'strict selected field types')\n    R.require(rows == expected,")
insert='''
def load_failed_capture(bundle):
    raw = R.read(bundle, 'CAPTURE01.json')
    R.require(R.digest(raw) == FAILED_CAPTURE, 'exact failed capture pin')
    capture = json.loads(raw)
    R.require(capture['status'] == 'COMPLETE_ORIGINAL_FAILED_FORENSIC_ROOT02_LOCAL_CAPTURE_NO_EXTERNAL_RECOVERY' and capture['actual_external_or_flat_receipt'] is None and capture['native_or_ResearchRun_claim_started'] is False, 'failed capture status and nulls')
    R.require((capture['original_typed_including_root'],capture['payload_descendants'],capture['regular_bodies'],capture['logical_original_body_bytes']) == (43,42,31,114237), 'failed complete original and descendant denominators')
    R.require(capture['Root_outer_exit'] == 1 and capture['original_init_observed_exit'] is None and capture['separate_init_actual_reaped_exit'] == 0 and capture['historical_changed_directory_path_or_field'] is None and capture['permanent_disposition'] == 'FAILED_SPENT_FORENSIC_NAMESPACE_NO_NUMERICAL_CLAIM', 'original failure observations unchanged')
    manifest_raw = R.read(bundle,'FAILED_PAYLOAD_MANIFEST01.json')
    manifest = json.loads(manifest_raw); R.validate(manifest)
    R.require(R.digest(manifest_raw) == capture['manifest_sha256'] == capture['archive']['manifest_sha256'] and R.encode(manifest) == manifest_raw, 'failed canonical manifest pin')
    R.require(len(manifest['members']) == 42 and sum(x['kind']=='file' for x in manifest['members']) == 31 and sum(x.get('bytes',0) for x in manifest['members']) == 114237, 'failed complete body population')
    original_raw = R.read(bundle,'ORIGINAL_FAILED_ROOT_SCOPE43.json')
    R.require(R.digest(original_raw) == capture['original_scope_sha256'], 'original failed full scope pin')
    original = json.loads(original_raw)
    roots = [x for x in original['members'] if x['path']=='.']
    R.require(len(roots)==1 and roots[0]['kind']=='directory' and roots[0]['mode']==manifest['root_mode'], 'original root mode retained separately')
    projected = [{k:v for k,v in x.items() if k!='allocated_bytes'} for x in original['members'] if x['path']!='.']
    R.require(projected == manifest['members'] and len(original['members'])==43, 'every original descendant kind/path/mode/body retained')
    archive = R.read(bundle,'failed-remote02.tar.gz')
    R.require(len(archive)==capture['archive']['bytes'] <= R.FILE and R.digest(archive)==capture['archive']['sha256'], 'failed archive full byte pin')
    return capture, manifest


def restore_failed_delta(bundle, capture, manifest, root, boundary):
    destination = root / FAILED_OUTPUT
    R.require(root.is_absolute() and root.resolve()==root and not os.path.lexists(destination), 'fresh canonical failed flat namespace')
    boundary()
    destination.mkdir(mode=0o700)
    R.require(destination.resolve()==destination and stat.S_IMODE(destination.lstat().st_mode)==0o700, 'existing private failed destination')
    result = R.restore(bundle/'failed-remote02.tar.gz',capture['archive'],manifest,destination)
    verify_flat(destination,result,capture,manifest,boundary)
    return result

'''
s=s.replace('\ndef run(remote_sha256, selection_sha256):',insert+'\ndef run(remote_sha256, selection_sha256):')
s=s.replace("(OUTPUT,'FLAT_INTENT01.json'","(OUTPUT,FAILED_OUTPUT,'FLAT_INTENT01.json'")
s=s.replace('    capture,manifest = load_capture(bundle)\n    boundary()',"    capture,manifest = load_capture(bundle)\n    failed_bundle = HERE/'selected'/FAILED_REL\n    failed_capture,failed_manifest = load_failed_capture(failed_bundle)\n    boundary()")
s=s.replace("'capture_sha256':CAPTURE,'remote_receipt_sha256'","'capture_sha256':CAPTURE,'failed_capture_sha256':FAILED_CAPTURE,'remote_receipt_sha256'")
s=s.replace('    restored = restore_delta(bundle,capture,manifest,HERE,boundary)','    restored = restore_delta(bundle,capture,manifest,HERE,boundary)\n    failed_restored = restore_failed_delta(failed_bundle,failed_capture,failed_manifest,HERE,boundary)')
s=s.replace('    capture2,manifest2 = load_capture(bundle)','    capture2,manifest2 = load_capture(bundle)\n    failed_capture2,failed_manifest2 = load_failed_capture(failed_bundle)\n    R.require(failed_capture2 == failed_capture and failed_manifest2 == failed_manifest, \'original failed capture retained\')')
s=s.replace('    verify_flat(HERE/OUTPUT,restored,capture,manifest,boundary)\n    result', '    verify_flat(HERE/OUTPUT,restored,capture,manifest,boundary)\n    verify_flat(HERE/FAILED_OUTPUT,failed_restored,failed_capture,failed_manifest,boundary)\n    result')
s=s.replace("'COMPLETE_OPERATIONAL_SOURCE_POLICY_DELTA_FLAT_BYTES'","'COMPLETE_OPERATIONAL_DELTA_AND_FAILED_ROOT_FLAT_BYTES'").replace("'restored':restored,","'restored':restored,'failed_restored':failed_restored,")
s=s.replace('Exact41 typed/33 body operational source-policy delta only.','Exact41 typed/33 body operational delta plus failedRoot42 descendants/31 bodies (43 including original root) preserved. Original failed init observed exit null, separately reaped0, Root exit1 and unknown directory component remain unchanged. No failed namespace replay.')
s=s.replace("'regular_bodies':restored['regular_bodies']","'regular_bodies':restored['regular_bodies']+failed_restored['regular_bodies']")
ast.parse(s);(O/'restore01.py').write_text(s);(O/'REQUIRED_BODIES01.json').write_text(json.dumps(req,sort_keys=True,indent=2)+'\n');(O/'PREPARATION_STATUS01.json').write_text(json.dumps({'status':'DRAFT_WATCH04_FREEZE_AND_INDEPENDENT_SOURCE_RELEASE_REQUIRED','watch_source_sha256':'bdeacaadc053e615245b3e2175089842708719448ec7da970d981e5dc077ca18','watch_frozen_manifest':None,'independent_review':None,'actual_remote_receipt':None,'actual_execution_permitted':False},indent=2)+'\n');print(len(req),total,h(s.encode()))
