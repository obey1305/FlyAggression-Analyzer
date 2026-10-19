#!/bin/zsh
# FlyAggression Analyzer 2.1 integration build; original 2.0 release preserved.
APP='/Users/adityasinghchauhan/Documents/Codex/2026-10-16/fi/outputs/flyaggression-v2.1/app.py'
PYTHON='/Users/adityasinghchauhan/Documents/Codex/2026-10-16/fi/outputs/drosophila-aggression/.venv/bin/python'
RUNTIME='/Users/adityasinghchauhan/Documents/Codex/2026-10-16/fi/outputs/flyaggression-v2.1/.runtime'
mkdir -p "$RUNTIME"
cd -- '/Users/adityasinghchauhan/Documents/Codex/2026-10-16/fi/outputs/flyaggression-v2.1' || exit 1
if [[ ! -x "$PYTHON" || ! -f "$APP" ]]; then
 print 'Version 2.1 app or its pinned Python environment is missing.'
 exit 1
fi
owned=false
if [[ -f "$RUNTIME/server.pid" ]]; then
 server_pid=$(cat "$RUNTIME/server.pid")
 command_line=$(/bin/ps -p "$server_pid" -o command= 2>/dev/null)
 if [[ "$command_line" == *"$APP"* ]]; then owned=true; fi
fi
if [[ "$owned" != true ]]; then
 if /usr/sbin/lsof -nP -iTCP:8502 -sTCP:LISTEN >/dev/null 2>&1; then
  print 'Port 8502 is occupied by another process. Close it before launching Version 2.1.'
  exit 1
 fi
 nohup "$PYTHON" -m streamlit run "$APP" --server.address 127.0.0.1 --server.port 8502 --server.headless true --browser.gatherUsageStats false < /dev/null > "$RUNTIME/server.log" 2>&1 &
 print $! > "$RUNTIME/server.pid"
 disown
fi
if "$PYTHON" - <<'READY'
import time,urllib.request
for attempt in range(60):
 try:
  with urllib.request.urlopen('http://127.0.0.1:8502/_stcore/health',timeout=1) as response:
   if response.status==200:raise SystemExit(0)
 except (OSError,TimeoutError):time.sleep(.5)
raise SystemExit(1)
READY
then
 /usr/bin/open 'http://127.0.0.1:8502/?version=2.1'
else
 print 'Could not start Version 2.1. Check .runtime/server.log in the Version 2.1 folder.'
 exit 1
fi
