import vim
import sys
import importlib
import stream_parser
import logging

reloadModules = False
def setReloadModules(x):
  reloadModules = x

class VimBuffer(stream_parser.Buffer):
  def __init__(self, text):
    self.text = text

  def getChar(self, cursor):
    if stream_parser.inRange(cursor.row, self.text):
      if stream_parser.inRange(cursor.column, self.text[cursor.row]):
        return self.text[cursor.row][cursor.column]
      elif cursor.column == len(self.text[cursor.row]):
        return '\n'
    return None

  def getSpan(self, text_span):
    chars = []
    cursor_it = text_span.start.clone()
    c = self.getChar(cursor_it)
    while c is not None and cursor_it != text_span.end:
      chars.append(c)
      cursor_it.moveForward(self)
      c = self.getChar(cursor_it)
    return ''.join(chars)

class VimUtil(object):
  @staticmethod
  def selectTextSpan(span):
    vim.eval('cursor({}, {})'.format(span.start.row + 1, span.start.column + 1))
    vim.command('normal! v')
    vim.eval('cursor({}, {})'.format(span.end.row + 1, span.end.column))

  @staticmethod
  def insertAboveSelection(text):
    lines = text.split('\n')
    (selected_line, selected_column) = vim.current.buffer.mark("<")
    vim.current.buffer.append(lines, selected_line - 1)

def vimMainTextObject(module_name, inner=True):
  module = importlib.import_module(module_name)
  if reloadModules:
    reload(stream_parser)
    reload(module)
  (row,col) = vim.current.window.cursor
  cursor = stream_parser.Cursor(row - 1, col)
  buf = VimBuffer(vim.current.buffer)
  span = module.main(cursor, buf, inner=inner)
  if span:
    VimUtil.selectTextSpan(span)

def vimMainAppendSelection(module_name, text):
  module = importlib.import_module(module_name)
  if reloadModules:
    reload(module)
  out_text = module.main(text)
  VimUtil.insertAboveSelection(out_text)
