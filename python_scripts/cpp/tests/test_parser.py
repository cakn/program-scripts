import unittest

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cpp_parser import *

class TestParser(unittest.TestCase):
  cppTypeConstInt = CppType("int", const = True)
  debug_mode = False

  @staticmethod
  def setDebug():
    TestParser.debug_mode = True

  def setUp(self):
    pass

  def runTest(self, data, expected_list):
    result = parseVariables(data, debug= TestParser.debug_mode)
    self.assertListEqual(result, expected_list)

  def test_intType(self):
    data = 'int test_;'
    expected_list = [CppVariable(CppType("int"), "test_")]
    self.runTest(data, expected_list)

  def test_pointerType(self):
    data = 'int* test_;'
    expected_list = [CppVariable(CppType("int", pointer = True), "test_")]
    self.runTest(data, expected_list)

  def test_pointerPointerType(self):
    data = 'int** test_;'
    expected_list = [CppVariable(CppType(CppType("int", pointer = True), pointer = True), "test_")]
    self.runTest(data, expected_list)

  def test_multiDeclare(self):
    data = '''int test_;
              int test2_;
              char asdf;'''
    expected_list = [
        CppVariable(CppType("int"), "test_"),
        CppVariable(CppType("int"), "test2_"),
        CppVariable(CppType("char"), "asdf"),
        ]
    self.runTest(data, expected_list)

  def test_constType(self):
    data = 'const int test_;'
    expected_list = [CppVariable(CppType("int", const=True), "test_")]
    self.runTest(data, expected_list)

  def test_refType(self):
    data = 'int& test_;'
    expected_list = [CppVariable(CppType("int", reference=True), "test_")]
    self.runTest(data, expected_list)

  def test_constRefType(self):
    data = 'const int& test_;'
    expected_list = [CppVariable(CppType("int", const=True, reference=True), "test_")]
    self.runTest(data, expected_list)

  def test_constPointer(self):
    data = 'const int* test_;'
    expected_list = [CppVariable(CppType(TestParser.cppTypeConstInt, pointer=True), "test_")]
    self.runTest(data, expected_list)

  def test_typePtrConst(self):
    data = 'int* const test_;'
    expected_list = [CppVariable(CppType("int", pointer=True, const=True), "test_")]
    self.runTest(data, expected_list)

  def test_typeConstPtr(self):
    data = 'int const * test_;'
    expected_list = [CppVariable(CppType(TestParser.cppTypeConstInt, pointer=True), "test_")]
    self.runTest(data, expected_list)

  def test_typeConstPtrConst(self):
    data = 'int const * const test_;'
    expected_list = [CppVariable(CppType(TestParser.cppTypeConstInt, pointer=True, const=True), "test_")]
    self.runTest(data, expected_list)

  def test_scope(self):
    data = 'std::string test_;'
    expected_list = [CppVariable(CppType("string", namespace="std"), "test_")]
    self.runTest(data, expected_list)

  def test_scopeDefault(self):
    data = '::string test_;'
    expected_list = [CppVariable(CppType("string"), "test_")]
    self.runTest(data, expected_list)

  def test_scopeDefaultThenScope(self):
    data = '::std::string test_;'
    expected_list = [CppVariable(CppType("string", namespace="std"), "test_")]
    self.runTest(data, expected_list)

  def test_templateType(self):
    data = 'vector<int> test_;'
    expected_list = [CppVariable(CppType("vector", template_params=[CppType("int")]), "test_")]
    self.runTest(data, expected_list)

  def test_templateTypeWithScope(self):
    data = 'std::vector<int> test_;'
    expected_list = [CppVariable(CppType("vector", namespace="std", template_params=[CppType("int")]), "test_")]
    self.runTest(data, expected_list)

  def test_templateTypeMultiple(self):
    data = 'tuple<int, char, float> test_;'
    expected_list = [CppVariable(CppType("tuple", template_params=[CppType("int"), CppType("char"), CppType("float")]), "test_")]
    self.runTest(data, expected_list)

  def test_defaultValue(self):
    data = 'int test_ = 0;'
    expected_list = [CppVariable(CppType("int"), "test_", defaultValue=0)]
    self.runTest(data, expected_list)

  def test_nestedTypes(self):
    data = 'std::map<int, std::unique_ptr<Object>> test_;'
    expected_list = [CppVariable(CppType("map", namespace="std",
      template_params=[
        CppType("int"),
        CppType("unique_ptr", namespace="std", template_params=[CppType("Object")])]), "test_")]
    self.runTest(data, expected_list)

  def test_noEndingSemi(self):
    data = 'int test_'
    expected_list = [CppVariable(CppType("int"), "test_")]
    self.runTest(data, expected_list)

if __name__ == '__main__':
  # TestParser.setDebug()
  # unittest.main(defaultTest="TestParser.test_intType")
  unittest.main()
