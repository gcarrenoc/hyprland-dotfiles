function cpurge --description "Delete saved Claude Code conversations (--all: every one that isn't open)"
    set -l ids
    if test "$argv[1]" = --all
        set ids (claude-sessions list --deletable | string split -f1 \t)
    else
        set ids (claude-sessions list --deletable |
            __csessions_fzf 'delete › ' 'Tab: mark · Enter: delete the marked ones (open conversations are not listed)' --multi |
            string split -f1 \t)
    end
    if not set -q ids[1]
        echo "Nothing to delete."
        return
    end
    read -l -P "Delete "(count $ids)" conversation(s) for good? [y/N] " answer
    if not string match -qi y -- $answer
        echo "Cancelled."
        return
    end
    claude-sessions delete $ids
end
