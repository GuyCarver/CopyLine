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
import os, functools, collections
from Edit.edit import Edit

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

      rs = currs + rs

      copyLine, _ = vw.rowcol(rs[0].begin())
      self.showMessage = False

      def OnLine( s ) :
        row, _ = vw.rowcol(s.begin())
        ok = (row == copyLine)
        self.showMessage |= ok
        return ok

      #Filter out any selections not on same line.
      rs = [ s for s in rs if OnLine(s) ]

      if len(rs) :
        vw.add_regions("copyline", currs + rs, "selection", "dot")

      if self.showMessage :
        sublime.status_message("selection(s) not on copy line.")
    else:
      vw.erase_regions("copyline")

class CopyLineCommand( sublime_plugin.TextCommand ) :
  Active = None                 #Currently active text input.
  Commands = { "" : None }      #Dictionary of commands.

  def __init__( self, aView ) :
    super(CopyLineCommand, self).__init__(aView)
    self.inputView = None
    self.History = collections.deque([""], 21) #20 entries but don't count the "".
    self.HistIndex = -1

  def IsInputView( self, aView ) :
    return (aView and self.inputView and aView.id() == self.inputView.id())

  def FindInsertRegion( self, copyPoint, aRegions ) :
    row, _ = self.view.rowcol(copyPoint)
    for r in aRegions :
      rrow, _ = self.view.rowcol(r.begin())
      if rrow != row :
        return r

    return None

  def DoCopy( self, edit , onevalue ) :
    self.HistIndex = -1
    vw = self.view
    sels = vw.get_regions("copyline")
    self.OneValue = onevalue;

    insertr = None

    #if copyline regions not empty insert at cursor and copy from points.
    if sels :
      insertr = vw.sel()[0]
      copyPoint = sels[0].begin()
      # If insertr is on same line as copyPoint then move to next line.
      r1, c1 = vw.rowcol(insertr.begin())
      r2, c2 = vw.rowcol(copyPoint)
      if r1 == r2 :
        tp = vw.text_point(r1 + 1, 0)
        insertr = sublime.Region(tp, tp)
    else: #If no copyline regions just use the regular regions.
      sels = [ s for s in vw.sel() ]
      #assume 1st item in list is on the copy line.
      copyPoint = sels[0].begin()
      slen = len(sels)
      if slen > 1 :
        # If more than 2 items assume 2nd item is on the copy line.  Most likely
        # either the 1st or last item will be the insert point and on a separate line.
        if slen > 2 :
          copyPoint = sels[1].begin()

        insertr = FindInsertRegion(vw, copyPoint, sels)

        #if we found an insert point remove from the list of copy regions.
        if insertr != None :
          sels.remove(insertr)

    #Get the full line for the point we have selected to copy.
    copyLine = vw.full_line(copyPoint)
    #start point of the line used to adjust regions after string insert.
    srcStart = copyLine.begin()

    #Get the string for the line.
    str = vw.substr(copyLine)

    #If no insert point, set at the beginning of the copy line
    # so it will adjust the cursor position to the next line
    # but modify the values on the next line.
    if insertr == None :
      modifyPoint = copyLine.end()
      insertPos = srcStart
    else: #otherwise just insert and modify at the same location.
      modifyPoint = insertr.begin()
      insertPos = modifyPoint

    #Insert the strings.
    vw.insert(edit, insertPos, str)

    #if no selections or only the cursor then just exit after we copy the line.
    if not sels or (len(sels) == 1 and sels[0].empty()) :
      return

    #Reverse the list because we need to modify in reverse orde.
    # If we don't a change in length for the fields would cause subsequent
    # fields to replace the wrong text.
    sels.reverse()

    #Need to find out how much to adjust the regions to put them on the inserted line.
    adj = modifyPoint - srcStart

    #Create new reagions adjusted by the change in the buffer from the line we inserted.
    selList = [ sublime.Region(r.begin() + adj, r.end() + adj) for r in sels ]

    self.Replace( selList, None )

  def run( self, edit, cmd = None, onevalue = False ) :
    if cmd == None : #If no special command just copy the line.
      if len(self.view.get_regions("copyline")) :
        CopyLineCommand.Active = self
        self.DoCopy(edit, onevalue)
      else:
        DoCollate(self.view, edit)
    else: #Otherwise try and run special command on active view.
      theCommand = CopyLineCommand.Commands[cmd]
      if theCommand and CopyLineCommand.Active != None:
        theCommand(CopyLineCommand.Active)

  def UpdateHistory( self, aEntry ) :
    if len(aEntry) : #Don't do anything with empty entries.
      try:
        self.History.remove(aEntry)
      except:
        pass
      self.History.appendleft(aEntry)
      self.HistIndex = -1

  def Replace( self, aList, aReplacement ) :
    if len(aList) : #If anyting in list
      #If no replacement given we are just starting so skip replace.
      if aReplacement != None :
        self.view.erase_regions("cpy")    #Clear cpy region from previous query.
        self.UpdateHistory(aReplacement)  #Add new text to history.
        with Edit(self.view) as edit :
          if self.OneValue:               #If single input value for all marks.
            for r in aList :  #Iterate marks and replace with text.
              edit.replace(r, aReplacement)
              aList = []                  #Clear list as we are done.
          else: #Just process 1 entry.
            r = aList[0]                  #Get 1st entry in list.
            edit.replace(r, aReplacement) #Replace text.
            aList = aList[1:]             #Remove entry from the list.

      if len(aList) : #If anyting in list then request replacement text.
        r = aList[0]
        txt = self.view.substr(r)         #Get text for replacement.

        #Mark text to replace so we can see where it is at.
        self.view.add_regions("cpy", aList if self.OneValue else [r], "green")
        #Open input view.
        self.inputView = self.view.window().show_input_panel("Set:",
          txt, functools.partial(self.Replace, aList), None, self.OnCancel)
        self.inputView.set_name("CopyLine")
        self.inputView.run_command("select_all")
      else:
        CopyLineCommand.Active = None

  def OnCancel( self ) :
    CopyLineCommand.Active = None

  def MoveHist( self, aDir ) :
    #Wrap the index around the history queue.
    self.HistIndex = (self.HistIndex + aDir) % (len(self.History) - 1)
    #Get history string from queue.
    hstr = self.History[self.HistIndex]
    #If not empty replace text in view with history.
    if len(hstr) :
      vw = CopyLineCommand.Active.inputView
      with Edit(vw) as edit:
        edit.replace(sublime.Region(0, vw.size()), hstr)

  def HistUp( self ) :
    self.MoveHist(1)

  def HistDown( self ) :
    self.MoveHist(-1)

  @classmethod
  def IsActive( aClass, aView, aKey, aOperator, aOperand ) :
    ###Return true if the given view is the copyline inputpanel.
    return (aKey == "CopyLine" and aClass.Active and aClass.Active.IsInputView(aView))

#List of run command types (Note show is not in this list  It is parsed separately).
CopyLineCommand.Commands = { "hist_up" : CopyLineCommand.HistUp,
                             "hist_down" : CopyLineCommand.HistDown,
                           }

class RecipientEventListener( sublime_plugin.EventListener ) :
  def on_query_context( self, aView, aKey, aOperator, aOperand, match_all ) :
    return(CopyLineCommand.IsActive(aView, aKey, aOperator, aOperand))

