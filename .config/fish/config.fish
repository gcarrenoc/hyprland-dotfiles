# Fish — the interactive shell inside tmux / Alacritty.
# Bash stays the login shell and runs the scripts (see ~/.config/tmux/tmux.conf, default-shell).
# Functions: ~/.config/fish/functions/  ·  completions: ~/.config/fish/completions/

status is-interactive; or return

set -g fish_greeting                                  # no welcome message

# conda: only its functions (same as `conda init fish`, without starting conda for every shell)
set -l conda ~/anaconda3/etc/fish/conf.d/conda.fish
test -f $conda; and source $conda

# own commands first
fish_add_path --global --move --prepend ~/.local/bin

# zoxide: smarter cd. `z <part of path>` jumps to the best match, `zi` picks with fzf.
type -q zoxide; and zoxide init fish | source
