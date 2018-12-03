import unittest


class Test(unittest.TestCase):
    def setUp(self):
        print("some text1")

    def test_search_in_python_org(self):
        print("some text2")

    def tearDown(self):
        print("some text3")


if __name__ == "__main__":
    unittest.main()