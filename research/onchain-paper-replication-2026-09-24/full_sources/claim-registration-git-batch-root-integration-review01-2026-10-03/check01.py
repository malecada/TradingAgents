import pathlib,hashlib,json,ast,subprocess,os
R=pathlib.Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';P=F/'claim-registration-git-batch-root-integration01-2026-10-03';D=pathlib.Path(__file__).parent;C=pathlib.Path('/home/malecada/master_thesis/onchain-fixture-isolation/neural-cold-proof-native-20261003-02/source');H=lambda b:hashlib.sha256(b).hexdigest()
env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_OPTIONAL_LOCKS':'0','GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'protocol.allow','GIT_CONFIG_VALUE_0':'never'}
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],env=env,stderr=subprocess.PIPE)
assert H((P/'MANIFEST01.json').read_bytes())=='8db890d0aee6c8b5f07ee38991bdca80783a0212e69ae6015da282a8755d2151'
for r in json.loads((P/'MANIFEST01.json').read_bytes())['files']:b=(P/r['path']).read_bytes();assert len(b)==r['bytes'] and H(b)==r['sha256']
original=(P/'verify.before.py').read_bytes();selected=(P/'verify.selected.py').read_bytes();assert (R/'tradingagents/research/verify.py').read_bytes()==selected
assert H(selected)=='1f14343c7918e3464991b9b57ecdf74425130de5c049a4e401d896116881efce' and H(original)=='3a45746a388307d1b375c885bb2fd7a22c2a60f139df714d2bbe98906d57d7eb'
a=selected.decode();t=ast.parse(a);helper=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='_registration_pair');lines=a.splitlines(keepends=True);del lines[helper.lineno-1:helper.end_lineno+2]
inverse=''.join(lines).replace('    registration_pair = _registration_pair(root, claim)\n    registration = next(registration_pair)','    registration = _blob(root, claim["source"], claim["registration"])').replace('    if next(registration_pair) != registration:','    if _blob(root, claim["design_source"], claim["registration"]) != registration:');assert inverse.encode()==original and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(original))
head=git(R,'rev-parse','HEAD').decode().strip();assert git(R,'show','HEAD:tradingagents/research/verify.py')==original
changed=git(R,'diff','HEAD','--name-only','--','tradingagents').decode().splitlines();assert changed==['tradingagents/research/verify.py']
assert not git(R,'ls-files','--others','--exclude-standard','--','tradingagents')
B='361339125a3f1cd57e7ba8611f5a994ae649fa0b';assert git(C,'rev-parse','HEAD').decode().strip()==B
inv=json.loads((C/'cold_prep/source_inventory.json').read_bytes());rows=inv['source_inventory'];assert len(rows)==195 and inv['package_count']==147
for r in rows:
 b=(C/r['target']).read_bytes();assert H(b)==r['sha256'] and len(b)==r['bytes'] and git(C,'show',B+':'+r['target'])==b
assert (C/'tradingagents/research/verify.py').read_bytes()==original
anchor=json.loads((C/'cold_prep/anchor.json').read_bytes());print('anchor_keys',sorted(anchor))
out={'schema_version':1,'decision':'accepted_exact_main_integration_only','main_head_at_review':head,'main_selected_sha256':H(selected),'full_inverse_original_bytes_and_AST_equal':True,'only_main_tradingagents_diff':changed,'untracked_main_package_files':0,'capsule_head_unchanged':B,'all_195_original_capsule_sources_current_and_Git_equal':True,'package_sources':147,'capsule_verifier_remains_original':True,'no_import_numerical_claim_native_or_network':True,'scope':'HEAD-relative main package change only, plus exact original capsule source/Git. No claim about unrelated concurrent documentation edits; no speed/capacity/execution authority.'}
(D/'READBACK01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
