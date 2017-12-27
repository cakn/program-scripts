import argparse
import cpp_parser
import re
import sys
import logging

def convertVar(cppVar):
  name = cppVar.name
  return "  if (a.{var} != b.{var}) {{ return false; }}".format(var = name)

def main(text, debug = False, logger = None):
  if logger is None:
    logging.basicConfig()
    logger = logging.getLogger(__name__)
  var_list = cpp_parser.parseVariables(text, debug = debug, logger = logger)
  if var_list is None:
    logger.error("Error parsing text")
    return
  if_conds = "\n".join(map(lambda x: convertVar(x), var_list))
  template = \
"""bool operator==(const VarType& a, const VarType& b)
{{
{if_conds}
  return true;
}}
bool operator!=(const VarType& a, const VarType& b)
{{
  return !(a == b);
}}"""
  return template.format(if_conds = if_conds)

if __name__ == "__main__":
  arg_parser = argparse.ArgumentParser(description='', add_help=False)
  arg_parser.add_argument('--help', action='help',
                          help='Show help message')
  arg_parser.add_argument('text', type=str,
                          help='')
  args = arg_parser.parse_args()
  text = args.text
  sys.stdout.write(main(text))

