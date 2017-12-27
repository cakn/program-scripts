import ply.lex as lex

# List of token names.   This is always required
tokens = [
   'NUMBER',
   # 'PLUS',
   # 'MINUS',
   # 'DIVIDE',
   # 'LPAREN',
   # 'RPAREN',
   'ID',
   'COMMENT',
   'SCOPE',
   'LANGLED',
   'RANGLED',
   'EQUAL',
   'EOF',
]

# List of keywords
reserved_list = [
  'const',
  # 'float',
  # 'char',
]
reserved = {}
for key in reserved_list:
  reserved[key] = 'KEY_' + key.upper()

tokens = tokens + list(reserved.values())

literals = [ '*', '&', ';', ',' ]

# Regular expression rules for simple tokens
# t_PLUS    = r'\+'
# t_MINUS   = r'-'
# t_DIVIDE  = r'/'
# t_LPAREN  = r'\('
# t_RPAREN  = r'\)'
t_SCOPE  = r'::'
t_LANGLED  = r'\<'
t_RANGLED  = r'\>'
t_EQUAL  = r'='

# A regular expression rule with some action code
def t_NUMBER(t):
  r'\d+'
  t.value = int(t.value)
  return t

# Define a rule so we can track line numbers
def t_newline(t):
  r'\n+'
  t.lexer.lineno += len(t.value)

def t_ID(t):
  r'[a-zA-Z_][a-zA-Z_0-9]*'
  t.type = reserved.get(t.value,'ID')    # Check for reserved words
  return t

t_ignore_COMMENT = r'//.*'

# A string containing ignored characters (spaces and tabs)
t_ignore  = ' \t'

# Error handling rule
def t_error(t):
  print("Illegal character '%s'" % t.value[0])
  t.lexer.skip(1)


# Proxy lexer for EOF token
class ProxyLexer(object):
  def __init__(self, lexer, eoftoken):
    self.end = False
    self.lexer = lexer
    self.eof = eoftoken
  def token(self):
    tok = self.lexer.token()
    if tok is None:
      if self.end :
        self.end = False
      else:
        self.end = True
        tok = lex.LexToken()
        tok.type = self.eof
        tok.value = None
        tok.lexpos = self.lexer.lexpos
        tok.lineno = self.lexer.lineno
    return tok
  def __getattr__(self, name):
    return getattr(self.lexer, name)

import ply.yacc as yacc

def isTypeOfString(o):
  return type(o) == str or type(o) == unicode

class CppNamespace(object):
  def __init__(self, name):
    self.parent = None
    if type(name) is CppType:
      self.copy(name.namespace)
      self.appendNamespace(name.name)
    else:
      self.name = name

  def __str__(self):
    parent = ""
    if self.parent:
      parent = self.parent
    return "CppNamespace({parent}{})".format(self.name, parent = parent)

  def __repr__(self):
    return str(self)

  def __eq__(self, other):
    if type(other) is not type(self):
      return False
    return self.__dict__ == other.__dict__

  def copy(self, other):
    self.name = other.name
    self.parent = other.parent

  def isDefaultNamespace(self):
    return self.name == ''

  def getRoot(self):
    ret = self
    while ret.parent:
      ret = ret.parent
    return ret

  def appendFront(self, namespace):
    if namespace.isDefaultNamespace():
      return
    front_namespace = self.getRoot()
    if self.isDefaultNamespace():
      self.copy(namespace)
    else:
      front_namespace.parent = namespace

  def appendNamespace(self, namespace):
    def getNamespace(namespace):
      if type(namespace) is CppNamespace:
        return namespace
      elif isTypeOfString(namespace):
        return CppNamespace(namespace)
      else:
        raise Exception("Unknown type " + str(namespace) + str(type(namespace)))
    nsp = getNamespace(namespace)
    if self.isDefaultNamespace():
      self.name = nsp.name
      self.parent = nsp.parent
    else:
      self.parent = CppNamespace(self.name)
      self.name = nsp.name

class CppType(object):
  def __init__(self, name, pointer = False, const = False, reference = False, namespace='', template_params=None):
    self.pointer = pointer
    self.const = const
    self.reference = reference

    if template_params:
      self.template_params = template_params
    else:
      self.template_params = []

    if pointer and isTypeOfString(name):
      self.name = CppType(name)
    else:
      self.name = name
    if isTypeOfString(namespace):
      self.namespace = CppNamespace(namespace)
    else:
      self.namespace = namespace

  def rawName(self):
    values = {'name': self.name}
    defaults = ['const', 'reference', 'pointer', 'namespace', 'template_params']
    for x in defaults:
      values[x] = ''

    if type(self.name) == type(self):
      values['name'] = "{}".format(self.name.rawName())
    if self.const:
      values['const'] = "const "
    if self.reference:
      values['reference'] = "&"
    if self.pointer:
      values['pointer'] = "*"
    if self.namespace and self.namespace.name != '':
      values['namespace'] = self.namespace.name + "::"
    if len(self.template_params) > 0:
      values['template_params'] = "<{}>".format(",".join(map(lambda x: x.rawName(), self.template_params)))

    return "{const}{namespace}{name}{template_params}{pointer}{reference}".format(**values)

  def __str__(self):
    return "CppType({})".format(self.rawName())

  def __repr__(self):
    return str(self)

  def __eq__(self, other):
    if type(other) is not type(self):
      return False
    return self.__dict__ == other.__dict__

  def isPointer(self):
    return bool(self.pointer)

  def isConst(self):
    return self.const

  def setConst(self):
    self.const = True
    return self

  def isReference(self):
    return self.reference

  def setReference(self):
    self.reference = True
    return self

  def appendFrontNamespace(self, namespace):
    self.namespace.appendFront(namespace)
    return self

  def addTemplateParams(self, params):
    if type(params) is list:
      self.template_params += params
    else:
      self.template_params.append(params)
    return self

class CppVariable(object):
  def __init__(self, t, name, defaultValue=None):
    self.t = t
    self.name = name
    self.defaultValue = defaultValue

  def __str__(self):
    ret = ["type: " + str(self.t), "name: " + self.name]
    if self.defaultValue is not None:
      ret.append("defaultValue: " + str(self.defaultValue))
    return "CppVariable({})".format(", ".join(ret))

  def __repr__(self):
    return str(self)

  def __eq__(self, other):
    if type(other) is not type(self):
      return False
    return self.__dict__ == other.__dict__

  def setDefaultValue(self, value):
    self.defaultValue = value
    return self

  def getType(self):
    return self.t

precedence = (
    ('left', 'ID'),
    ('left', 'KEY_CONST'),
    ('left', '*'),
    ('left', 'SCOPE'),
)

def p_statement_list(p):
  'statement_list : statement_list statement'
  p[1].append(p[2])
  p[0] = p[1]

def p_statements_single(p):
  'statement_list : statement'
  p[0] = [p[1]]

def p_statement(p):
  '''statement : var_declare line_terminate'''
  p[0] = p[1]

def p_var_declare_default_value(p):
  'var_declare : var_declare EQUAL default_value'
  p[0] = p[1].setDefaultValue(p[3])

def p_default_value(p):
  '''default_value : ID
                   | NUMBER'''
  p[0] = p[1]

def p_var_declare(p):
  '''var_declare : type ID
                 | qualified_type ID'''
  p[0] = CppVariable(p[1], p[2])

def p_qualified_type_const(p):
  'qualified_type : KEY_CONST type'
  p[0] = p[2].setConst()

def p_qualified_type_type_const_ptr(p):
  'qualified_type : type KEY_CONST'
  p[0] = p[1].setConst()

def p_qualified_const_type_ptr(p):
  'qualified_type : KEY_CONST type "*"'
  # Special case
  p[2].setConst()
  p[0] = CppType(p[2], pointer = True)

def p_qualified_type_const_type_ptr(p):
  'qualified_type : qualified_type "*"'
  p[0] = CppType(p[1], pointer = True)

def p_qualified_type_type_ptr_const(p):
  '''qualified_type : type "*" KEY_CONST
                    | qualified_type "*" KEY_CONST'''
  p[0] = CppType(p[1], pointer = True, const = True)

def p_qualified_type_const_ref(p):
  'qualified_type : KEY_CONST type "&"'
  p[0] = p[2].setConst().setReference()

def p_qualified_type_ref(p):
  'qualified_type : type "&"'
  p[0] = p[1].setReference()

def p_type_pointer(p):
  '''type : type "*"'''
  p[0] = CppType(p[1], pointer = True)

def p_scoped_type(p):
  'type : namespace type'
  p[0] = p[2].appendFrontNamespace(p[1])

def p_default_scope(p):
  'namespace : SCOPE'
  p[0] = CppNamespace('')

def p_namespace(p):
  'namespace : type SCOPE'
  p[0] = CppNamespace(p[1])

def p_template_params(p):
  '''type : type LANGLED type RANGLED
          | type LANGLED qualified_type RANGLED'''
  p[0] = p[1].addTemplateParams(p[3])
def p_template_params_multi(p):
  '''type : type LANGLED type_list RANGLED'''
  p[0] = p[1].addTemplateParams(p[3])

def p_type_list_start(p):
  'type_list : type "," type'
  p[0] = [p[1], p[3]]

def p_type_list_append(p):
  'type_list : type_list "," type'
  p[1].append(p[3])
  p[0] = p[1]

def p_type(p):
  'type : ID'
  p[0] = CppType(p[1])

def p_line_terminate_collapse(p):
  '''line_terminate : line_terminate line_terminate'''
  pass

def p_eof(p):
  '''line_terminate : ";"
                    | EOF'''
  pass

# Error rule for syntax errors
def p_error(p):
  print("Syntax error in input!", p)

lexer = None
parser = None
def build(logger = None, debug = False):
  global lexer
  global parser
  if logger is None:
    logger = lex.NullLogger()

  if lexer is None:
    orig_lexer = lex.lex(debug = debug, debuglog = logger, errorlog = logger)
    # Build the lexer
    # Remember to use lexer=lexer when calling parse
    lexer = ProxyLexer(orig_lexer, 'EOF')
  if parser is None:
    # Build the parser
    parser = yacc.yacc(debug = debug, debuglog = logger, errorlog = logger)

def parseVariables(text, debug=False, logger = None):
  if logger is None:
    logger = lex.NullLogger()
  logger.debug("parseVariable with text: " + text)
  build(logger = logger, debug = debug)
  out = parser.parse(text, lexer = lexer, debug = debug)
  logger.debug("parseVariable result: " + str(out))
  return out
