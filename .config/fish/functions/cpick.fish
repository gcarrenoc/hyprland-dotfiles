function cpick --description "Choose a saved Claude Code conversation and resume it in its folder"
    set -l line (claude-sessions list | __csessions_fzf 'resume › ' 'Enter: resume · ● = open right now')
    test -n "$line"; or return
    set -l id (string split -f1 \t -- $line)
    set -l dir (claude-sessions cwd $id)
    if not test -d "$dir"
        echo "The session's folder no longer exists ($dir); resuming here instead."
        set dir $PWD
    end
    if claude-sessions running $id
        read -l -P "That conversation is open right now. Continue it as a copy (fork)? [Y/n] " answer; or return
        string match -qi n -- $answer; and return
        __csessions_in $dir claude --resume $id --fork-session
    else
        __csessions_in $dir claude --resume $id
    end
end
