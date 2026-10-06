"""Evidence-bound round2 review after the operator inspects complete tool log."""
from datetime import datetime,timezone
from pathlib import Path
import json,shutil,sys
RUN=Path('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-sol-r02');OUT=RUN/'operator-observation'
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
from benchmark_support import read,save,digest
from policy_review import create_review,validate_review
m=read(RUN/'run-manifest.json');assert m['operator']['status'] in {'completed','timeout','aborted','environment_failed'}
events=[json.loads(s) for s in (RUN/'stdout.jsonl').read_text(encoding='utf-8').splitlines()]
items=[(n,e['item']) for n,e in enumerate(events,1) if e.get('type')=='item.completed']
commands=[{'raw_line':n,**i} for n,i in items if i.get('type')=='command_execution']
changes=[{'raw_line':n,**i} for n,i in items if i.get('type')=='file_change']
findings=read(RUN.parent/'sol-followup02-shell-command-findings.json')
confirmed=[v for v in findings if not v['parse_errors'] and v['pipeline_extents']]
assert confirmed and all(v['run_id']==RUN.name for v in findings)
for i in changes:
    for change in i['changes']:assert Path(change['path']).resolve().is_relative_to((RUN/'checkout').resolve())
denials=[i['raw_line'] for i in commands if 'Permission denied' in i.get('aggregated_output','')]
after_denial=[] if not denials else [{'raw_line':n,'type':i['type']} for n,i in items if n>denials[0] and i.get('type') in {'command_execution','file_change'}]
now=datetime.now(timezone.utc).isoformat()
save(OUT/'shell-command-policy-audit.json',{'date':'2026-10-06','run_id':RUN.name,'reviewed_at':now,
    'raw_stdout_sha256':digest((RUN/'stdout.jsonl').read_bytes()),'confirmed_findings':confirmed,
    'ambiguous_parse_findings_excluded':[v for v in findings if v['parse_errors']],
    'frozen_task_instruction':'셸 명령은 한 호출에 하나만 실행한다. `;`, `&&`, 파이프·명령 치환·shell wrapper로 결합하지 않는다.',
    'method':'PowerShell AST inspection and manual review of captured commands. Quoted regex alternation is not a pipeline. Commands are not executed by this audit.',
    'scope':'Previously supplied common restriction; no retrospective new rule or permission change. Current series quality is already invalid by dated first-run correction.'})
for source in [RUN.parent/'audit-sol-captured-shell.ps1',RUN.parent/'sol-followup02-shell-command-input.json',RUN.parent/'sol-followup02-shell-command-findings.json']:
    target=OUT/'policy-audit-procedure'/source.name;target.parent.mkdir(exist_ok=True);shutil.copy2(source,target)
raw_usage=next((e['usage'] for e in reversed(events) if e.get('type')=='turn.completed'),None)
save(OUT/'native-tool-review.json',{'run_id':RUN.name,'reviewed_at':now,'commands':commands,'file_changes':changes,
    'raw_events':len(events),'failed_commands':m['measurement']['failed_commands'],'denial_raw_lines':denials,
    'actions_after_denial':after_denial,'confirmed_forbidden_pipeline_commands':len(confirmed),
    'review':'Operator manually inspected captured command/file events against own checkout, fixed inputs/feedback and declared SDK/manufacturer sources. No candidate serial/flash, other implementation, online access or permission bypass observed. Explicit shell pipelines independently violate unchanged common task.',
    'raw_turn_usage':raw_usage,'frozen_adapter_reasoning_field':m['measurement']['tokens']['reasoning'],
    'usage_note':'Raw native usage retained alongside unchanged frozen adapter fields, without reinterpretation of charging or cached counts.',
    'operator_audited_user_interventions':0,'candidate_hardware_access':False,'in_run_feedback':False})
lines=[v['raw_line'] for v in confirmed]
decision={'status':'invalid_for_comparison','reviewer':'Codex operator','user_interventions':0,
    'reason':f'Followup2 has {len(confirmed)} confirmed shell pipeline commands at raw lines{lines}, violating unchanged common task. Preserve terminal/submission/product observations and full raw cost; Sol-series quality invalid remains in force.',
    'intervention_review':'No operator implementation repair, global permission change, in-run feedback or replacement call. Raw measured interventions null preserved; audited count0.',
    'evidence':[{'path':'operator-observation/shell-command-policy-audit.json','sha256':digest((OUT/'shell-command-policy-audit.json').read_bytes())},
        {'path':'operator-observation/native-tool-review.json','sha256':digest((OUT/'native-tool-review.json').read_bytes())}]}
save(RUN/'operator-policy-decision.json',decision);create_review(RUN/'run-manifest.json',decision)
assert validate_review(m,RUN/'run-manifest.json')['decision']['status']=='invalid_for_comparison'
print(json.dumps({'run_id':RUN.name,'policy_status':'invalid_for_comparison','confirmed_pipelines':len(confirmed),
    'denial_lines':denials,'after_denial_actions':after_denial,'raw_events':len(events),'commands':len(commands),'file_changes':len(changes)}))
