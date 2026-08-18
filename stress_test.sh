#!/usr/bin/env bash
# clice stress test harness
# Run this on a machine with clice already installed and Docker running.
# Each section is independent - comment out ones you don't want to run.
set -uo pipefail

PASS=0
FAIL=0

ok()   { PASS=$((PASS+1)); printf '  \033[1;32mPASS\033[0m %s\n' "$1"; }
bad()  { FAIL=$((FAIL+1)); printf '  \033[1;31mFAIL\033[0m %s\n' "$1"; }
section() { printf '\n\033[1;36m== %s ==\033[0m\n' "$1"; }

# ── 1. Concurrent settings writes ──────────────────────────────────────
# ~/.clice/settings.json isn't lock-protected. Fire N parallel `clice set`
# calls and confirm the file survives as valid JSON with SOME value set,
# rather than getting corrupted or half-written.
section "Concurrent settings writes"

for i in 1 2 3 4 5 6 7 8; do
  clice set resources.checker_timeout "$((10 + i))" &
done
wait

if python3 -c "import json; json.load(open('$HOME/.clice/settings.json'))" 2>/dev/null; then
  ok "settings.json is still valid JSON after concurrent writes"
else
  bad "settings.json is CORRUPTED after concurrent writes"
fi

FINAL=$(clice get resources.checker_timeout 2>/dev/null)
echo "  final value after the race: $FINAL"

# ── 2. Concurrent registry reads ───────────────────────────────────────
# Confirm N parallel `clice list` calls don't crash or corrupt the cache,
# especially right after clearing it (forces the cold-cache fetch path
# to race across processes).
section "Concurrent registry reads (cold cache)"

rm -rf "$HOME/.clice/cache"
FAILED_READS=0
for i in 1 2 3 4 5 6; do
  clice list > /tmp/stress_list_$i.txt 2>&1 &
done
wait

for i in 1 2 3 4 5 6; do
  if grep -q "hello-clice" /tmp/stress_list_$i.txt 2>/dev/null; then
    :
  else
    FAILED_READS=$((FAILED_READS+1))
    echo "  process $i output:"
    cat /tmp/stress_list_$i.txt | sed 's/^/    /'
  fi
done
rm -f /tmp/stress_list_*.txt

if [ "$FAILED_READS" -eq 0 ]; then
  ok "all 6 concurrent cold-cache reads succeeded"
else
  bad "$FAILED_READS/6 concurrent reads failed or returned bad data"
fi

# ── 3. Interrupt handling - no orphaned containers ─────────────────────
# Launch `clice run` in the background, send SIGINT partway through,
# confirm no container/volume gets left behind.
section "Interrupt handling (SIGINT during container startup)"

BEFORE=$(docker ps -aq | wc -l)

echo "" | timeout 5 clice run hello-clice > /tmp/stress_run_output.txt 2>&1 &
RUN_PID=$!
sleep 2
kill -INT "$RUN_PID" 2>/dev/null
wait "$RUN_PID" 2>/dev/null

sleep 1
AFTER=$(docker ps -aq | wc -l)

if [ "$AFTER" -le "$BEFORE" ]; then
  ok "no orphaned containers after SIGINT (before=$BEFORE, after=$AFTER)"
else
  bad "possible orphaned container(s) after SIGINT (before=$BEFORE, after=$AFTER)"
  echo "  run: docker ps -a   to inspect"
fi

# ── 4. Rapid repeated run+interrupt ─────────────────────────────────────
# Same as above, but repeated several times back to back - catches races
# that only show up under repetition, not a single interrupt.
section "Repeated interrupt cycles (5x)"

ORPHANS=0
for i in 1 2 3 4 5; do
  BEFORE=$(docker ps -aq | wc -l)
  echo "" | timeout 4 clice run hello-clice > /dev/null 2>&1 &
  RPID=$!
  sleep 1
  kill -INT "$RPID" 2>/dev/null
  wait "$RPID" 2>/dev/null
  sleep 1
  AFTER=$(docker ps -aq | wc -l)
  if [ "$AFTER" -gt "$BEFORE" ]; then
    ORPHANS=$((ORPHANS+1))
    echo "  cycle $i: container count grew ($BEFORE -> $AFTER)"
  fi
done

if [ "$ORPHANS" -eq 0 ]; then
  ok "no orphaned containers across 5 repeated interrupt cycles"
else
  bad "$ORPHANS/5 cycles left an orphaned container - run: docker ps -a"
fi

# ── summary ──────────────────────────────────────────────────────────
echo
echo "================================"
echo "  $PASS passed, $FAIL failed"
echo "================================"
[ "$FAIL" -eq 0 ]