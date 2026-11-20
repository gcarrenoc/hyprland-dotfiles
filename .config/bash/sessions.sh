# Claude Code sessions — loaded from ~/.bashrc
#   cnew [folder] [claude options]   new conversation (here, or in that folder)
#   cpick                            choose a saved conversation (fzf + preview) and resume it in its folder
#   cpurge                           choose conversations to delete (Tab marks several)
#   cpurge --all                     delete every conversation that isn't open right now
# Helper: ~/.local/bin/claude-sessions (open sessions are never deleted)

cnew() {
    if [[ -n $1 && -d $1 ]]; then
        (cd "$1" && shift && claude "$@")
    else
        claude "$@"
    fi
}

_csessions_fzf() {     # shared list: $1 = prompt, $2 = header, rest = extra fzf options
    local prompt=$1 header=$2; shift 2
    fzf --ansi --delimiter=$'\t' --with-nth=2 --no-sort --layout=reverse --height=90% \
        --prompt="$prompt" --header="$header" \
        --preview='claude-sessions preview {1}' --preview-window='right,55%,wrap' "$@"
}

cpick() {
    local line id dir answer
    line=$(claude-sessions list | _csessions_fzf 'resume › ' 'Enter: resume · ● = open right now') || return
    id=${line%%$'\t'*}
    dir=$(claude-sessions cwd "$id")
    if [[ -z $dir || ! -d $dir ]]; then
        echo "The session's folder no longer exists (${dir:-unknown}); resuming here instead."
        dir=$PWD
    fi
    if claude-sessions running "$id"; then
        read -rp "That conversation is open right now. Continue it as a copy (fork)? [Y/n] " answer
        [[ ${answer,,} == n ]] && return
        (cd "$dir" && claude --resume "$id" --fork-session)
    else
        (cd "$dir" && claude --resume "$id")
    fi
}

cpurge() {
    local ids answer
    if [[ $1 == --all ]]; then
        mapfile -t ids < <(claude-sessions list --deletable | cut -f1)
    else
        mapfile -t ids < <(claude-sessions list --deletable |
            _csessions_fzf 'delete › ' 'Tab: mark · Enter: delete the marked ones (open conversations are not listed)' --multi |
            cut -f1)
    fi
    if (( ${#ids[@]} == 0 )); then
        echo "Nothing to delete."
        return
    fi
    read -rp "Delete ${#ids[@]} conversation(s) for good? [y/N] " answer
    [[ ${answer,,} == y ]] || { echo "Cancelled."; return; }
    claude-sessions delete "${ids[@]}"
}
