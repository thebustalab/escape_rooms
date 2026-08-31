#!/bin/bash
# Wait until ComfyUI has NO running and NO pending jobs.
# Gating on the python process exiting is wrong: a sweep that hits its poll timeout exits while its
# renders are still queued, so the next stage starts and its own polls then time out waiting behind
# them. That cascade is what turned stages T and W into false TIMEOUTs. The queue is the truth.
while :; do
  n=$(curl -s http://127.0.0.1:8289/queue \
      | python3 -c "import json,sys;q=json.load(sys.stdin);print(len(q.get('queue_running',[]))+len(q.get('queue_pending',[])))" 2>/dev/null)
  [ "$n" = "0" ] && break
  sleep 30
done
