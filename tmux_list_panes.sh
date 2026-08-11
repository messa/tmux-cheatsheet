#!/bin/bash
exec tmux list-panes -a -F '#{p22:#{session_name}:#{window_index}.#{pane_index}} #{p28:window_name} #{s|#{HOME}|~|:pane_current_path}'
