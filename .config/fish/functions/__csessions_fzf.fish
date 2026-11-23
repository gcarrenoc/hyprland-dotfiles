function __csessions_fzf --description "Session list for cpick / cpurge: prompt, header, extra fzf options"
    fzf --ansi --delimiter=\t --with-nth=2 --no-sort --layout=reverse --height=90% \
        --prompt=$argv[1] --header=$argv[2] \
        --preview='claude-sessions preview {1}' --preview-window='right,55%,wrap' $argv[3..]
end
