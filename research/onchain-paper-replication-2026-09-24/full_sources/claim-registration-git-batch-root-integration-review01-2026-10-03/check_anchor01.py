import pathlib,json,hashlib,subprocess,os
C=pathlib.Path('/home/malecada/master_thesis/onchain-fixture-isolation/neural-cold-proof-native-20261003-02/source');D=pathlib.Path(__file__).parent;a=json.loads((C/'cold_prep/anchor.json').read_bytes());assert len(a['files'])==147 and a['commit']=='fb9fad1d93836b4f92f2be8111da4adf22b7e069'
env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_OPTIONAL_LOCKS':'0','GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'protocol.allow','GIT_CONFIG_VALUE_0':'never'}
for p,h in a['files'].items():
 b=(C/p).read_bytes();assert hashlib.sha256(b).hexdigest()==h and subprocess.check_output(['git','-C',str(C),'show',a['commit']+':'+p],env=env,stderr=subprocess.PIPE)==b
print('PASS all 147 original S2 anchor Git/current package bodies unchanged')
