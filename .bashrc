#
# ~/.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

alias ls='ls --color=auto'
alias grep='grep --color=auto'
PS1='[\u@\h \W]\$ '

# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/home/gcarreno/anaconda3/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/home/gcarreno/anaconda3/etc/profile.d/conda.sh" ]; then
        . "/home/gcarreno/anaconda3/etc/profile.d/conda.sh"
    else
        export PATH="/home/gcarreno/anaconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<

export PATH="$HOME/.local/bin:$PATH"

# macOS-style `open`: open files, folders or URLs with their default app.
#   open            -> current folder in Files (Nautilus)
#   open a.pdf b.png https://example.com
open() {
    [ $# -eq 0 ] && set -- .
    local f
    for f in "$@"; do
        xdg-open "$f" >/dev/null 2>&1 &
        disown
    done
}

# Jump to this semester's university folder
alias uni='cd "$HOME/Insync/YOUR-GOOGLE-ACCOUNT/Google Drive/University/2026/spring"'

# zoxide: smarter cd. `z <part of path>` jumps to the best match, `zi` picks with fzf.
# Keep this at the end of .bashrc.
eval "$(zoxide init bash)"
