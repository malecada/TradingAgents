import copy,unittest
from prepare01 import eligible
class Checks(unittest.TestCase):
    def setUp(self):
        self.claim={'experiment_id':'synthetic-closed'};self.terminal={'experiment_id':'synthetic-closed','claim_sha256':'a'*64,'status':'complete'}
        self.owner={'experiment':'synthetic-closed'};self.guard={'phase':'complete','child_exit_code':0,'cleanup_verified':True,'limit_reason':None,'owner_identity':self.owner}
    def check(self,week='2024-01-01T00:00:00Z'):
        eligible(self.claim,self.terminal,'a'*64,self.guard,self.owner,week)
    def test_complete_metadata(self):self.check()
    def test_failed_parent_cannot_inherit_component_permission(self):
        self.terminal['status']='failed'
        with self.assertRaises(ValueError):self.check()
    def test_pilot_graph_is_protected(self):
        with self.assertRaises(ValueError):self.check('2022-06-13T00:00:00Z')
    def test_bad_closure_and_owner_refuse(self):
        for key,value in [('cleanup_verified',False),('child_exit_code',1),('owner_identity',{})]:
            self.setUp();self.guard[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.check()
        self.setUp();self.terminal['claim_sha256']='b'*64
        with self.assertRaises(ValueError):self.check()
if __name__=='__main__':unittest.main()
