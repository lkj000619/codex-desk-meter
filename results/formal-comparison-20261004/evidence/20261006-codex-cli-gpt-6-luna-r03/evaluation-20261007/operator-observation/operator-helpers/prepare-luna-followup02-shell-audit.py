"""Extract displayed native shell bodies as inert JSON after terminal."""
from pathlib import Path
import json,re,sys
ROOT=Path('C:/meter-followups-20261006');RUN=ROOT/'20261006-codex-cli-gpt-6-luna-r03'
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
from benchmark_support import read,save
m=read(RUN/'run-manifest.json');assert m['operator']['status'] in {'completed','timeout','aborted','environment_failed'}
events=[json.loads(s) for s in (RUN/'stdout.jsonl').read_text(encoding='utf-8').splitlines()]
commands=[]
for n,e in enumerate(events,1):
    if e.get('type')!='item.completed' or e.get('item',{}).get('type')!='command_execution':continue
    command=e['item']['command'];match=re.search(r'\s-Command\s+(.*)$',command,re.S)
    assert match,command
    body=match[1]
    assert body[0] in "\"'" and body[-1]==body[0],command
    body=body[1:-1]
    commands.append({'run_id':RUN.name,'raw_line':n,'body':body,'command':command})
save(ROOT/'luna-followup02-shell-command-input.json',commands)
print(json.dumps({'inert_command_bodies_extracted':len(commands),'commands_executed_by_audit':0}))
