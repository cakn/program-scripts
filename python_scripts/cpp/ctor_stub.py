import argparse
import cpp_parser
import re
import sys

def camelToWords(name):
  return re.findall('[a-zA-Z][^A-Z!_]*', name)

def wordsToUnderscoreLower(words):
  return '_'.join(map(lambda x : x.lower(), words))

kCopyTypes = [
  'int',
  'char',
  'float',
  'double',
]

def paramName(name):
  return wordsToUnderscoreLower(camelToWords(name))

def varToParam(cppVar, paramNameFunc):
  use_const_ref = cppVar.getType().name not in kCopyTypes
  if cppVar.getType().isPointer():
    use_const_ref = False

  cppType = cppVar.getType()
  name = paramNameFunc(cppVar.name)
  type_name = cppType.rawName()
  keys = {
      "const"     : "",
      "type_name" : type_name,
      "reference" : "",
      "name"      : name
  }
  if use_const_ref:
    if not cppType.isConst():
      keys["const"] = "const "
    if not cppType.isReference():
      keys["reference"] = "&"
  return "{const}{type_name}{reference} {name}".format(**keys)

def varToCtor(cppVar, paramNameFunc):
  name = cppVar.name
  param_name = paramNameFunc(name)
  keys  = { 'name' : name, 'param_name' : param_name }
  return "{name}({param_name})".format(**keys)

def main(text, debug = False, logger = None):
  # sys.stdout.writelines("text " + args.text)
  var_list = cpp_parser.parseVariables(text, debug = debug, logger = logger)
  if var_list is None:
    logger.error("Error parsing text")
    return
  params = ", ".join(map(lambda x: varToParam(x, paramName), var_list))
  ctor_init = ",\n".join(map(lambda x: "  " + varToCtor(x, paramName), var_list))
  keys = {"params" : params, "ctor" : ctor_init}
  ret = "({params}) :\n{ctor}".format(**keys)
  return ret

if __name__ == "__main__":
  arg_parser = argparse.ArgumentParser(description='', add_help=False)
  arg_parser.add_argument('--help', action='help',
                          help='Show help message')
  arg_parser.add_argument('text', type=str,
                          help='')
  args = arg_parser.parse_args()
  text = args.text
  sys.stdout.write(main(text))

