#!/usr/bin/env zsh
# Task 4 benchmark: how long does one suggestion take, as seen from zsh?
# Usage: zsh bench/engine_latency.zsh SOCKET_PATH [N]
#
# A. Start a new Python process per keystroke (what a naive plugin would do).
# B. Ask a resident engine over a Unix socket with zsh's built-in zsocket (no new process).
# C. B, but from a forked subshell, as zsh-autosuggestions' async mode does.
zmodload zsh/datetime zsh/net/socket
sock=$1; n=${2:-200}
prefixes=(n nm nma nmap ls cd s ssh g gi git c ca cat p py pyt sudo e ec echo m)

stats() {  # print median and 95th percentile of the numbers in $times (ms)
  local -a s; s=(${(on)times})
  printf "%-46s median %7.2f ms   p95 %7.2f ms   (n=%d)\n" "$1" \
    ${s[$(( (${#s}+1)/2 ))]} ${s[$(( (${#s}*95+99)/100 ))]} ${#s}
}

typeset -a times
times=()
for i in {1..$(( n / 10 ))}; do
  t0=$EPOCHREALTIME; python3 -c 'pass'; t1=$EPOCHREALTIME
  times+=($(( (t1 - t0) * 1000 )))
done
stats "A1. python3 -c pass (bare start-up)"

times=()
for i in {1..$(( n / 10 ))}; do
  t0=$EPOCHREALTIME; python3 -c 'import sys; sys.path.insert(0,"src"); import cta.analysis.predictors'; t1=$EPOCHREALTIME
  times+=($(( (t1 - t0) * 1000 )))
done
stats "A2. python3 importing the engine code only"

zsocket $sock || { print "cannot connect to $sock"; exit 1 }
fd=$REPLY
times=()
for i in {1..$n}; do
  p=${prefixes[$(( i % ${#prefixes} + 1 ))]}
  t0=$EPOCHREALTIME; print -r -- $p >&$fd; read -r reply <&$fd; t1=$EPOCHREALTIME
  times+=($(( (t1 - t0) * 1000 )))
done
stats "B.  resident engine via zsocket"
exec {fd}>&-   # close this connection so the next test can connect

times=()
for i in {1..$n}; do
  p=${prefixes[$(( i % ${#prefixes} + 1 ))]}
  t0=$EPOCHREALTIME
  reply=$( zsocket $sock && { print -r -- $p >&$REPLY; read -r r <&$REPLY; print -r -- $r } )
  t1=$EPOCHREALTIME
  times+=($(( (t1 - t0) * 1000 )))
done
stats "C.  resident engine from a forked subshell"
