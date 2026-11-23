function __csessions_in --description "Run a command in a folder, then come back"
    set -l back $PWD
    builtin cd -- $argv[1]; or return
    $argv[2..]
    set -l st $status
    builtin cd -- $back
    return $st
end
