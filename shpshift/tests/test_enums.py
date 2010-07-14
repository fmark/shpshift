import unittest
#import sys
#sys.path.insert(0, '..')
from shpshift import enums

class TestEnum(unittest.TestCase):
    def test___getattr__(self):
        enum = enums.Enum(['RED', 'GREEN', 'BLUE'])
        self.assertEqual('RED', enum.__getattr__('RED'))
        self.assertEqual('RED', enum.RED)
        self.assertNotEqual('red', enum.RED)
        try:
            e = enum.NOT_A_COLOUR
        except AttributeError:
            pass
        else:
            assert False, 'Excepted an AttributeError'



if __name__ == '__main__':
    unittest.main()
