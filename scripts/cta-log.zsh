# Context logger for zsh (5.8 or later).
#
# Records every command with the context it was typed in, so the context signals
# in the requirements (working directory, Git state, exit status of the previous
# command, host, time) can be measured on real use. Public datasets do not record
# exit status or Git state, so this is the only source for them.
#
# Install: add this line to ~/.zshrc, then open a new terminal:
#     source /path/to/context-terminal-assistant/scripts/cta-log.zsh
#
# Output: one JSON object per line in $CTA_LOG
#   (default ~/.local/share/cta/log.jsonl), readable only by you (mode 600).
#   The format is the same as scripts/cta-log.bash.
#
# Privacy: the log stays on this machine and is never committed or shared.
# A command typed with a leading space is not logged.
# Set CTA_LOG_OFF=1 to pause logging in the current shell.

[[ -n ${ZSH_VERSION:-} ]] || return 0
[[ -o interactive ]] || return 0

zmodload zsh/datetime
autoload -Uz add-zsh-hook

: ${CTA_LOG:=${XDG_DATA_HOME:-$HOME/.local/share}/cta/log.jsonl}
typeset -g __cta_session="${HOST:-host}-$$-$EPOCHSECONDS"
typeset -g __cta_cmd="" __cta_cwd="" __cta_branch="" __cta_dirty=""
typeset -gi __cta_pending=0

__cta_json() {
    # Escape a string for JSON: backslash, quote and common control characters.
    local s=$1
    s=${s//\\/\\\\}
    s=${s//\"/\\\"}
    s=${s//$'\n'/\\n}
    s=${s//$'\r'/\\r}
    s=${s//$'\t'/\\t}
    print -rn -- "\"$s\""
}

__cta_context() {
    # Context at the moment the next command is typed: directory and Git state.
    __cta_cwd=$PWD
    __cta_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null) || __cta_branch=""
    __cta_dirty=""
    if [[ -n $__cta_branch ]]; then
        if git diff --no-ext-diff --quiet HEAD -- 2>/dev/null; then
            __cta_dirty=false
        else
            __cta_dirty=true
        fi
    fi
}

__cta_preexec() {
    # $1 is the command line exactly as typed.
    __cta_pending=0
    [[ -n ${CTA_LOG_OFF:-} ]] && return
    [[ $1 == ' '* ]] && return          # leading space: do not record
    [[ -z ${1//[[:space:]]/} ]] && return
    __cta_cmd=$1
    __cta_pending=1
}

__cta_precmd() {
    local exit_status=$?   # must be the first statement: exit status of the command just run
    if (( __cta_pending )) && [[ -n $__cta_cwd ]]; then
        local dir=${CTA_LOG:h}
        [[ -d $dir ]] || (umask 077; mkdir -p -- "$dir")
        (umask 077
         print -r -- "{\"t\":$EPOCHSECONDS,\"host\":$(__cta_json "${HOST:-}"),\"session\":$(__cta_json "$__cta_session"),\"cwd\":$(__cta_json "$__cta_cwd"),\"git_branch\":$( [[ -n $__cta_branch ]] && __cta_json "$__cta_branch" || print -rn null),\"git_dirty\":${__cta_dirty:-null},\"exit\":$exit_status,\"cmd\":$(__cta_json "$__cta_cmd")}" >> "$CTA_LOG")
    fi
    __cta_pending=0
    __cta_context
    return $exit_status
}

add-zsh-hook preexec __cta_preexec
add-zsh-hook precmd __cta_precmd
