import sys
sys.path.append("D:\dev\lib\pythonnet")

import clr
from System.Collections import *
from System import String, Char, Int32
from System.Diagnostics import Trace
clr.AddReference("Microsoft.VisualStudio.TextManager.Interop")
from Microsoft.VisualStudio.TextManager.Interop import *
import stream_parser
import importlib
import traceback
import logging

out_int = 1
out_str = ""

class ClrHandler(logging.Handler):
  def __init__(self):
    logging.Handler.__init__(self)

  def emit(self, record):
    if type(record.msg) == tuple:
      Trace.WriteLine(" ".join(map(lambda x : str(x), record.msg)))
    else:
      Trace.WriteLine(record.msg % record.args)

  def write(self, string):
    pass

  def flush(self):
    pass

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.handlers = []
logger.addHandler(ClrHandler())
logger.setLevel(logging.DEBUG)

def log(*args):
  Trace.WriteLine(" ".join(map(lambda x : str(x), args)))

def msvcMain(vsTextView, textBuffer, module_name, inner):
  try:
    module = importlib.import_module(module_name)
    ret, line, column = vsTextView.GetCaretPos(out_int, out_int)
    text = textBuffer.currentSnapshot.GetText()
    text_buffer = stream_parser.Buffer(text)
    # column may include virtual space, move it so it does not
    column = min(len(text_buffer.text[line]), column)
    cursor = stream_parser.Cursor(line, column)
    span = module.main(cursor, text_buffer, inner=inner, logger = logger)
    # log(span)
    return span
  except Exception as e:
    log(traceback.format_exc())
    raise e

def msvcMainSelectionAppend(text, module_name):
  try:
    module = importlib.import_module(module_name)
    # file output stream for parser seems to not work when streaming output with debug mode
    out_text = module.main(text, debug = False, logger = logger)
    return out_text
  except Exception as e:
    log(traceback.format_exc())
    raise e
