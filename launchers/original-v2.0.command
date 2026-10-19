#!/bin/zsh
# FlyAggression Analyzer Version 2.0 — raw-video research prototype.
# Uses the current workspace, pinned Python environment and unchanged frozen model.
cd -- '/Users/adityasinghchauhan/Documents/Codex/2026-10-16/fi/outputs/drosophila-aggression' || exit 1
if [[ ! -x .venv/bin/python || ! -f ../raw-video-integration/day6/video_to_lunges.py ]]; then
  print 'Version 2.0 files or Python environment are missing. Restore the project workspace first.'
  read '?Press Return to close.'
  exit 1
fi
print 'Starting FlyAggression Analyzer v2.0 (experimental raw video + MATLAB features)…'
mkdir -p ../../work/gui
if ! .venv/bin/python -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8501/_stcore/health", timeout=2)' >/dev/null 2>&1; then
  nohup .venv/bin/python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --browser.gatherUsageStats false > ../../work/gui/desktop-server.log 2>&1 &
  disown
fi
if .venv/bin/python - <<'READY'
import time, urllib.request
for attempt in range(60):
    try:
        with urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=1) as response:
            if response.status == 200:
                raise SystemExit(0)
    except (OSError, TimeoutError):
        time.sleep(.5)
raise SystemExit(1)
READY
then
  /usr/bin/open 'http://127.0.0.1:8501/?version=2.0'
else
  print 'Could not start FlyAggression Analyzer. See work/gui/desktop-server.log in the project workspace.'
  read '?Press Return to close.'
fi
