# Sublime Text CopyLine Package to copy a line and query for replacement text of marked fields.

## Install

    $ https://github.com/GuyCarver/CopyLine

## Instructions

A common mistake in programming is to copy and repeat a line making minor changes to each line but forgetting to change a field.

This package is used to mark sections of text on a line and query for replacement text when the line is copied.

### Key Bindings:

* alt-enter = Copy the line with marks on it and ask for replacement text for each mark.  If no marks copy the line with the cursor.  If any selections on the line query for replacement text for them.
* ctrl+k, m = Mark current selection(s) or word under cursor.
* ctrl+k, n = Clear all marks
* On text input the up/down arrows go through text input history (Max 20 deep)

## TODO:
* Tab completion from history for replacement text input.
* Option to move marks to the copied line rather than than staying on the copied line.