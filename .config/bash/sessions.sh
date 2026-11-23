# Claude Code sessions — loaded from ~/.bashrc
#   cnew [folder] [options] [prompt]  new conversation (here, or in that folder) — cnew -h
#   cpick                            choose a saved conversation (fzf + preview) and resume it in its folder
#   cpurge                           choose conversations to delete (Tab marks several)
#   cpurge --all                     delete every conversation that isn't open right now
# Helper: ~/.local/bin/claude-sessions (open sessions are never deleted)

cnew() {
    local dir='' opts=() words=()
    if [[ -n ${1-} && -d $1 ]]; then
        dir=$1; shift
    elif [[ ${1-} == ./* || ${1-} == ../* || ${1-} == "$HOME"/* ]] && [[ $1 != *[[:space:]]* ]]; then
        echo "cnew: no such folder: $1" >&2; return 1        # a typo, not a prompt
    fi
    while (( $# )); do
        case $1 in
            -h|--help)
                cat <<'HELP'
cnew [folder] [options] [prompt]   start a new Claude Code conversation

  folder              start in that folder (default: here)
  -n, --name NAME     name the conversation (easier to find in cpick)
  -m, --model MODEL   opus, sonnet, haiku, fable or a full model name
  -e, --effort LEVEL  low, medium, high, xhigh, max
  --plan              start in plan mode
  prompt              first message, no quotes needed unless it has ' " ? * & ; ( )
  other options       given to claude as they are, with everything after them

  cnew ~/thesis -n intro -m opus review the introduction
  cnew -e high --plan
  cnew --add-dir ~/Documents
HELP
                return 0 ;;
            -n|--name|-m|--model|-e|--effort)
                if (( $# < 2 )) || [[ -z $2 || $2 == -* ]]; then
                    echo "cnew: $1 needs a value (cnew -h)" >&2; return 1
                fi
                case $1 in
                    -n|--name)   opts+=(--name "$2") ;;
                    -m|--model)  opts+=(--model "$2") ;;
                    -e|--effort) opts+=(--effort "$2") ;;
                esac
                shift 2 ;;
            --plan) opts+=(--permission-mode plan); shift ;;
            --)     shift; words+=("$@"); break ;;
            -*)     if (( ${#words[@]} )); then words+=("$1"); shift      # a dash inside the prompt
                    else opts+=("$@"); break; fi ;;                       # claude's own option: pass the rest as is
            *)      words+=("$1"); shift ;;
        esac
    done
    if (( ${#words[@]} )); then opts+=(-- "${words[*]}"); fi
    if [[ -n $dir ]]; then
        (cd -- "$dir" && claude "${opts[@]}")
    else
        claude "${opts[@]}"
    fi
}

_cnew() {              # Tab: folders, options and their values
    local cur=${COMP_WORDS[COMP_CWORD]} prev=${COMP_WORDS[COMP_CWORD-1]}
    case $prev in
        -m|--model)  mapfile -t COMPREPLY < <(compgen -W 'opus sonnet haiku fable' -- "$cur"); return ;;
        -e|--effort) mapfile -t COMPREPLY < <(compgen -W 'low medium high xhigh max' -- "$cur"); return ;;
        -n|--name)   COMPREPLY=(); return ;;
    esac
    if [[ $cur == -* ]]; then
        mapfile -t COMPREPLY < <(compgen -W '-n --name -m --model -e --effort --plan -h --help' -- "$cur")
    else
        compopt -o filenames 2>/dev/null
        mapfile -t COMPREPLY < <(compgen -d -- "$cur")
    fi
}
complete -F _cnew cnew

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
