#----------------------------------------------------------------------
# Copyright (c) 2013, Guy Carver
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in the documentation
#       and/or other materials provided with the distribution.
#
#     * The name of Guy Carver may not be used to endorse or promote products # derived#
#       from # this software without specific prior written permission.#
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# FILE    CopyLine.py
# BY      Guy Carver
# DATE    06/15/2013 01:57 PM
#----------------------------------------------------------------------

import sublime, sublime_plugin
import functools

class MarkCollateCommand( sublime_plugin.TextCommand ) :
  def run( self, edit, add = True ) :
    vw = self.view
    if add :
      currs = vw.get_regions("collate")

      sels = vw.sel()
      getsel = lambda x : x if not x.empty() else vw.full_line(x)
      rs = currs + [ getsel(s) for s in sels ]

      if len(rs) :
        vw.add_regions("collate", rs, "selection", "bookmark")
    else:
      vw.erase_regions("collate")

def DoCollate( vw, edit ) :
  currs = vw.get_regions("collate")

  if len(currs) :
    currs.reverse()
  else:
    getsel = lambda x : x if not x.empty() else vw.full_line(x)
    currs = [ getsel(s) for s in vw.sel() ]

  toInsert = [ vw.substr(c) for c in currs ]

  for s in vw.sel() :
    #If selection empty then insert at beginning of line.
    insertPoint = s.begin() if not s.empty() else vw.full_line(s.begin()).begin()
    for s in toInsert :
      vw.insert(edit, insertPoint, s)

class CollateCommand( sublime_plugin.TextCommand ) :
  def run( self, edit ) :
    DoCollate(self.view, edit)

class MarkCopyCommand( sublime_plugin.TextCommand ) :
  def run( self, edit, add = True ) :
    vw = self.view
    if add :
      currs = vw.get_regions("copyline")

      sels = vw.sel()
      rs = [ s for s in sels if not s.empty() ]
      if len(rs) == 0 :
        rs = [ vw.word(vw.sel()[0].begin()) ]

      if len(rs) :
        vw.add_regions("copyline", currs + rs, "selection", "dot")

    else:
      vw.erase_regions("copyline")

class CopyLineCommand( sublime_plugin.TextCommand ) :
  def run( self, edit, cmd = None, onevalue = False ) :
    vw = self.view
    sels = vw.get_regions("copyline")
    viewSel = vw.sel()[0]

    if sels :
      #reduce our regions to a single region encompassing them all.
      src = functools.reduce(lambda a , b: a.cover(b), sels)

      if viewSel.contains(src) : #If have a selection then try and use it for the source
        src = vw.full_line(viewSel)
        destPos = src.b         #Insert after selection
      else:
        src = vw.full_line(src)
        destPos = -1            #Just insert at the current selection.

      srctxt = vw.substr(src)
      curpos = 0
      ind = 0
      newtext = "\n"
      #Replace all of the copyline marks with template stuff.
      for s in sels :
        a = s.a - src.a
        b = s.b - src.b
        newtext += srctxt[curpos:a] #Add text between tags
        #if replacing all tags with same value just add the
        # same index.  But still do ${0:oldtext} for 1st instance.
        if onevalue and ind > 0:
          newtext += '$0'
        else:
          oldtext = srctxt[a:b]
          newtext += '${' + str(ind) + ':' + oldtext + '}'
        ind += 1
        curpos = b

      newtext += srctxt[curpos:] #Add any remaining string.

      #Insert snippet
      if destPos != -1 :
        vw.sel().clear()
        vw.sel().add(sublime.Region(destPos, destPos))
      #insert the snippet.
      vw.run_command("insert_snippet", {"contents": newtext})
    else: #No CopyLine tags so just copy the current line.
      print("No Lines")
      for s in vw.sel() :
        sgrab = self.prevfullline(s)
        src = vw.full_line(sgrab)
        txt = vw.substr(src)
        destPos = sgrab.end() + 1
        vw.insert(edit, destPos, txt)
        vw.sel().clear()
        vw.sel().add(sublime.Region(destPos, destPos))

  def prevfullline( self, aSeg ) :
    p = aSeg.end()
    #if a selection then make sure we don't include the last line if the cursor
    # is at the beginning of it.
    if aSeg.size() > 1 :
      p -= 1

    lastLine = self.view.line(p)
    e = lastLine.end()
    b = min(aSeg.begin(), e)
    return sublime.Region(b, e)
