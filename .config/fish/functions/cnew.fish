function cnew --description "New Claude Code conversation: cnew [folder] [options] [prompt]"
    # Same as the Bash one in ~/.config/bash/sessions.sh
    set -l dir
    set -l opts
    set -l words
    if test -n "$argv[1]"; and test -d "$argv[1]"
        set dir $argv[1]
        set -e argv[1]
    else if string match -qr -- '^(\./|\.\./|'(string escape --style=regex -- $HOME)'/)\S*$' "$argv[1]"
        echo "cnew: no such folder: $argv[1]" >&2           # a typo, not a prompt
        return 1
    end
    while set -q argv[1]
        switch $argv[1]
            case -h --help
                echo 'cnew [folder] [options] [prompt]   start a new Claude Code conversation

  folder              start in that folder (default: here)
  -n, --name NAME     name the conversation (easier to find in cpick)
  -m, --model MODEL   opus, sonnet, haiku, fable or a full model name
  -e, --effort LEVEL  low, medium, high, xhigh, max
  --plan              start in plan mode
  prompt              first message, no quotes needed unless it has \' " ? * & ; ( ) $ #
  other options       given to claude as they are, with everything after them

  cnew ~/thesis -n intro -m opus review the introduction
  cnew -e high --plan
  cnew --add-dir ~/Documents'
                return 0
            case -n --name -m --model -e --effort
                if test -z "$argv[2]"; or string match -q -- '-*' $argv[2]
                    echo "cnew: $argv[1] needs a value (cnew -h)" >&2
                    return 1
                end
                switch $argv[1]
                    case -n --name
                        set -a opts --name $argv[2]
                    case -m --model
                        set -a opts --model $argv[2]
                    case -e --effort
                        set -a opts --effort $argv[2]
                end
                set -e argv[1..2]
            case --plan
                set -a opts --permission-mode plan
                set -e argv[1]
            case --
                set -e argv[1]
                set -a words $argv
                break
            case '-*'
                if set -q words[1]                          # a dash inside the prompt
                    set -a words $argv[1]
                    set -e argv[1]
                else                                        # claude's own option: pass the rest as is
                    set -a opts $argv
                    break
                end
            case '*'
                set -a words $argv[1]
                set -e argv[1]
        end
    end
    set -q words[1]; and set -a opts -- (string join ' ' -- $words | string collect)
    if set -q dir[1]
        __csessions_in $dir claude $opts
    else
        claude $opts
    end
end
