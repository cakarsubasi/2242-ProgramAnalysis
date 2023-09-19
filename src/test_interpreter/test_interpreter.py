import unittest

class TestInterpreter(unittest.TestCase):

    def test_one(self):
        self.assertTrue(True)

    def test_two(self):
        self.assertFalse(True)

if __name__ == "__main__":
    unittest.main()