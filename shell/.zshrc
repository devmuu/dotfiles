# ==============================================================================
# Program/File:  zshrc
# Description:   Config file to zsh
# Software/Tool: zsh
# ==============================================================================

# Source local environments
source ${HOME}/.userenv

# Aliases
source ${HOME}/.aliases

# Exports
export BROWSER="brave-browser-stable"
export EDITOR="nvim"
# export LANG="en_US.UTF-8"
export LUA_CPATH="${HOME}/.local/share/include/lua/lib/?.so"
export MICRO_TRUECOLOR=1
export PYTHONDONTWRITEBYTECODE=1
export SUDO_EDITOR="nvim"
export TERM="xterm-256color"
export TERMINAL="kitty"
export VISUAL="nvim"

# User Directories
export XDG_CONFIG_HOME="${HOME}/.config"
export XDG_CACHE_HOME="${HOME}/.cache"
export XDG_DATA_HOME="${HOME}/.local/share"

# History config
setopt noextendedhistory
setopt nosharehistory
setopt histexpiredupsfirst
setopt histignorealldups
setopt histignorespace
setopt histfindnodups
setopt histsavenodups

# History variables
export HISTORY_DIR="${HOME}/.shell"
[ ! -d "${HISTORY_DIR}" ] && mkdir ${HISTORY_DIR} 2> /dev/null
export HISTFILE="${HISTORY_DIR}/history"
export HISTFILESIZE=
export HISTSIZE=50000
export SAVEHIST=50000
export HISTDUP=erase
# export HISTORY_IGNORE="(ls|ls *|cd *|history|pwd|htop|bg|fg|clear|reset)"
# export HISTORY_IGNORE="${HISTORY_IGNORE}|(cp *|mv *|rm *)"
# export HISTORY_IGNORE="${HISTORY_IGNORE}|(vim *|wget *|curl *)"
# export HISTORY_IGNORE="${HISTORY_IGNORE}|(man *|dnf *|apt *|imv *|cava)"
# export HISTORY_IGNORE="${HISTORY_IGNORE}|(pip *)"

# Auto cd command
setopt autocd autopushd
setopt extendedglob nomatch menucomplete
setopt interactive_comments
zle_highlight=('paste:none')

# Beeping is annoying
unsetopt BEEP

# Disable ctrl-s
stty -ixon

# emacs mode
set -o emacs

# Export local bin to path
if [ -d "${HOME}/.local/bin" ] ; then
    export PATH="${HOME}/.local/bin":$PATH
fi

# Export local bin to path
if [ -d "${HOME}/.cargo/bin" ] ; then
    export PATH="${HOME}/.cargo/bin":$PATH
fi

# Export luarocks bin to path
if [ -d "${HOME}/.luarocks/bin" ] ; then
    export PATH="${HOME}/.luarocks/bin":$PATH
fi

# Verify asdf-vm folder
if [ -d "${HOME}/.asdf" ] ; then
    . ${HOME}/.asdf/asdf.sh
fi

# Export vim editor in ssh connection
if [[ -n ${SSH_CONNECTION} ]]; then
    export EDITOR="nvim"
else
    export EDITOR="nvim"
fi

# fzf source
[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

# Init starship
eval "$(starship init zsh)"

unsetopt listambiguous
autoload -Uz compinit
compinit -d ${XDG_CACHE_HOME}/zsh
compinit

# Enable no case search
zstyle ':completion:*' matcher-list '' 'm:{a-zA-Z}={A-Za-z}'
# Enable arrows navigation in tab completion
zstyle ':completion:*' menu select

# terminfo keys
key=(
    BackSpace  "${terminfo[kbs]}"
    Home       "${terminfo[khome]}"
    End        "${terminfo[kend]}"
    Insert     "${terminfo[kich1]}"
    Delete     "${terminfo[kdch1]}"
    Up         "${terminfo[kcuu1]}"
    Down       "${terminfo[kcud1]}"
    Left       "${terminfo[kcub1]}"
    Right      "${terminfo[kcuf1]}"
    PageUp     "${terminfo[kpp]}"
    PageDown   "${terminfo[knp]}"
)

# Enable pattern search by typed command
autoload -U up-line-or-beginning-search
autoload -U down-line-or-beginning-search
zle -N up-line-or-beginning-search
zle -N down-line-or-beginning-search

bindkey "\e[1;3C" forward-word
bindkey "\e[1;3D" backward-word

case "${DISTRO}" in
    fedora|arch)
        bindkey "^[[A" up-line-or-beginning-search
        bindkey "^[[B" down-line-or-beginning-search
    ;;
    ubuntu|debian)
        bindkey "${key[Up]}" up-line-or-beginning-search
        bindkey "${key[Down]}" down-line-or-beginning-search
    ;;
    *)
        bindkey "${key[Down]}" down-line-or-beginning-search
        bindkey "${key[Up]}" up-line-or-beginning-search
    ;;
esac

# Source plugins
if [[ "${DISTRO}" == "arch" ]]; then
    if [ -d "/opt/asdf-vm" ] ; then
        . /opt/asdf-vm/asdf.sh
    fi
    source /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
    source /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh
else
    source /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
    source /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh
fi

# Only load gnupg if folder exists
if [ -d ~/.gnupg ]; then
     if [ "${gnupg_SSH_AUTH_SOCK_by:-0}" -ne $$ ]; then
      export SSH_AUTH_SOCK="$(gpgconf --list-dirs agent-ssh-socket)"
    fi
    export GPG_TTY=$(tty)
    gpg-connect-agent updatestartuptty /bye > /dev/null
fi

