# Context logger for bash (4.4 or later).
#
# Records every command with the context it was typed in, so the context signals
# in the requirements (working directory, Git state, exit status of the previous
# command, host, time) can be measured on real use. Public datasets do not record
# exit status or Git state, so this is the only source for them.
#
# Install: add this line to ~/.bashrc, then open a new terminal:
#     source /path/to/context-terminal-assistant/scripts/cta-log.bash
#
# Output: one JSON object per line in $CTA_LOG
#   (default ~/.local/share/cta/log.jsonl), readable only by you (mode 600).
#
# Privacy: the log stays on this machine and is never committed or shared.
# A command typed with a leading space is not logged (bash's HISTCONTROL=ignorespace).
# Set CTA_LOG_OFF=1 to pause logging in the current shell.

[ -n "${BASH_VERSION:-}" ] || return 0
case $- in *i*) ;; *) return 0 ;; esac   # interactive shells only

: "${CTA_LOG:=${XDG_DATA_HOME:-$HOME/.local/share}/cta/log.jsonl}"
HISTCONTROL="ignorespace${HISTCONTROL:+:$HISTCONTROL}"
__cta_session="${HOSTNAME:-host}-$$-$(printf '%(%s)T' -1)"
__cta_last_histnum=""

__cta_json() {
    # Escape a string for JSON: backslash, quote and common control characters.
    local s=$1
    s=${s//\\/\\\\}
    s=${s//\"/\\\"}
    s=${s//$'\n'/\\n}
    s=${s//$'\r'/\\r}
    s=${s//$'\t'/\\t}
    printf '"%s"' "$s"
}

__cta_context() {
    # Context at the moment the next command is typed: directory and Git state.
    __cta_cwd=$PWD
    __cta_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null) || __cta_branch=""
    __cta_dirty=""
    if [ -n "$__cta_branch" ]; then
        if git diff --no-ext-diff --quiet HEAD -- 2>/dev/null; then
            __cta_dirty=false
        else
            __cta_dirty=true
        fi
    fi
}

__cta_log() {
    local status=$?            # must be the first statement: exit status of the command just run
    local entry num cmd
    if [ -z "${CTA_LOG_OFF:-}" ]; then
        entry=$(HISTTIMEFORMAT='' builtin history 1)
        if [[ $entry =~ ^[[:space:]]*([0-9]+)[*]?[[:space:]]+(.*)$ ]]; then
            num=${BASH_REMATCH[1]}
            cmd=${BASH_REMATCH[2]}
            # Skip the first prompt of a shell (its history entry is from an earlier session),
            # and skip when there is no new entry (empty line, or a command starting with a space).
            if [ -n "${__cta_cwd+x}" ] && [ "$num" != "$__cta_last_histnum" ]; then
                local dir=${CTA_LOG%/*}
                [ -d "$dir" ] || (umask 077; mkdir -p "$dir")
                (umask 077
                 printf '{"t":%s,"host":%s,"session":%s,"cwd":%s,"git_branch":%s,"git_dirty":%s,"exit":%s,"cmd":%s}\n' \
                    "$(printf '%(%s)T' -1)" \
                    "$(__cta_json "${HOSTNAME:-}")" \
                    "$(__cta_json "$__cta_session")" \
                    "$(__cta_json "$__cta_cwd")" \
                    "$( [ -n "$__cta_branch" ] && __cta_json "$__cta_branch" || printf null)" \
                    "${__cta_dirty:-null}" \
                    "$status" \
                    "$(__cta_json "$cmd")" >> "$CTA_LOG")
            fi
            __cta_last_histnum=$num
        fi
    fi
    __cta_context
    return "$status"
}

case ";${PROMPT_COMMAND:-};" in
    *";__cta_log;"*) ;;
    *) PROMPT_COMMAND="__cta_log${PROMPT_COMMAND:+;$PROMPT_COMMAND}" ;;
esac
