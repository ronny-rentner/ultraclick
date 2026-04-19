import sys
import unittest


unittest.main(module=None, argv=[sys.argv[0], "discover", "-s", "tests", "-t", ".", "-b", *sys.argv[1:]])
