function open --description "Open files, folders or URLs with their default app (no argument: this folder)"
    set -q argv[1]; or set argv .
    for f in $argv
        xdg-open $f >/dev/null 2>&1 &
        disown
    end
end
