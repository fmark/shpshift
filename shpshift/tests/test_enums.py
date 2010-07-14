import unittest
#import sys
#sys.path.insert(0, '..')
from shpshift import enums

class TestEnum(unittest.TestCase):
    def test___getattr__(self):
        enum = enums.Enum(['RED', 'GREEN', 'BLUE'])
        self.assertEqual('RED', enum.__getattr__('RED'))
#        assert False # TODO: implement your test here

if __name__ == '__main__':
    unittest.main()
