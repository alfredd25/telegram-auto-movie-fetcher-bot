
import unittest
from app.db.queries import normalize_query

class TestSearchLogic(unittest.TestCase):
    def test_normalize_query(self):
        # Test case from user report
        self.assertEqual(normalize_query("Fast+and+Furious"), "fast and furious")
        
        # Test basic cases
        self.assertEqual(normalize_query("Hello.World"), "hello world")
        self.assertEqual(normalize_query("Test_Movie"), "test movie")
        
        # Test already clean
        self.assertEqual(normalize_query("fast and furious"), "fast and furious")

if __name__ == '__main__':
    unittest.main()
