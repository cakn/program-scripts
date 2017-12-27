import unittest

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import ctor_stub

class TestCtorStub(unittest.TestCase):
  def setUp(self):
    pass
  def runTest(self, data, expected):
    result = ctor_stub.main(data)
    self.assertEqual(result, expected)

  def test_basic(self):
    data = """int test_;"""
    expected = """(int test) :
  test_(test)"""
    self.runTest(data, expected)

  def test_builtInTypes(self):
    data = """int type1_;
              char type2_;
              float type3_;
              double type4_;"""
    expected = """(int type1, char type2, float type3, double type4) :
  type1_(type1),
  type2_(type2),
  type3_(type3),
  type4_(type4)"""
    self.runTest(data, expected)

  def test_customTypes(self):
    data = """Object type1_;"""
    expected = """(const Object& type1) :
  type1_(type1)"""
    self.runTest(data, expected)

  def test_customTypePointer(self):
    data = """Object* type1_;"""
    expected = """(Object* type1) :
  type1_(type1)"""
    self.runTest(data, expected)

  def test_referencedType(self):
    data = """Object& type1_;"""
    expected = """(const Object& type1) :
  type1_(type1)"""
    self.runTest(data, expected)

  def test_constReferencedType(self):
    data = """const Object& type1_;"""
    expected = """(const Object& type1) :
  type1_(type1)"""
    self.runTest(data, expected)

if __name__ == '__main__':
  unittest.main()
