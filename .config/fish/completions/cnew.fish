complete -c cnew -f -n 'test (count (commandline -opc)) -eq 1' -a '(__fish_complete_directories)'
complete -c cnew -f
complete -c cnew -s n -l name -x -d "Name the conversation"
complete -c cnew -s m -l model -x -a 'opus sonnet haiku fable' -d Model
complete -c cnew -s e -l effort -x -a 'low medium high xhigh max' -d "Effort level"
complete -c cnew -l plan -d "Start in plan mode"
complete -c cnew -s h -l help -d Help
