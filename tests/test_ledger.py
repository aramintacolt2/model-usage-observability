import pathlib,sys,tempfile,unittest
sys.path.insert(0,str(pathlib.Path(__file__).parents[1]))
from usage.ledger import init,record,export
class T(unittest.TestCase):
 def test_roundtrip(self):
  with tempfile.TemporaryDirectory() as d:
   db=pathlib.Path(d)/'x.db';init(db);record(db,('1','gpt-5.4',2,3,.0001,'done'));out=pathlib.Path(d)/'x.csv';export(db,out);self.assertIn('gpt-5.4',out.read_text())
if __name__=='__main__':unittest.main()
