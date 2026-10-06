"""Evidence-bound terminal policy review; never execute captured commands."""
from datetime import datetime, timezone
from pathlib import Path
import json, shutil, sys
ROOT=Path('C:/meter-followups-20261007');RUN=ROOT/'20261007-codex-cli-gpt-6-luna-r01';OUT=RUN/'operator-observation'
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
from benchmark_support import read, save, digest
from policy_review import create_review, validate_review
m=read(RUN/'run-manifest.json');f=read(RUN/'operator-source-freeze.json')
assert digest((RUN/'run-manifest.json').read_bytes())==f['original_terminal_manifest_sha256']
events=[json.loads(s) for s in (RUN/'stdout.jsonl').read_bytes().splitlines()]
commands=[dict(raw_line=n,**e['item']) for n,e in enumerate(events,1) if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='command_execution']
changes=[dict(raw_line=n,**e['item']) for n,e in enumerate(events,1) if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='file_change']
findings=read(ROOT/'luna-followup03-shell-command-findings.json')
confirmed=[v for v in findings if not v['parse_errors'] and (v['pipeline_extents'] or v['separator_extents'])]
assert len(commands)==104 and len(changes)==5 and len(events)==229
assert [v['raw_line'] for v in confirmed]==[] and not any(v['separator_extents'] for v in confirmed)
assert all(v['run_id']==RUN.name for v in findings)
for item in changes:
    for change in item['changes']:assert Path(change['path']).resolve().is_relative_to((RUN/'checkout').resolve())
denials=[i['raw_line'] for i in commands if 'permission denied' in i.get('aggregated_output','').lower() or 'access is denied' in i.get('aggregated_output','').lower()]
assert not denials
now=datetime.now(timezone.utc).isoformat()
save(OUT/'shell-command-policy-audit.json',{'date':'2026-10-07','run_id':RUN.name,'reviewed_at':now,
    'raw_stdout_sha256':digest((RUN/'stdout.jsonl').read_bytes()),'confirmed_findings':confirmed,
    'ambiguous_parse_findings_excluded':[v for v in findings if v['parse_errors']],
    'frozen_task_instruction':'셸 명령은 한 호출에 하나만 실행한다. `;`, `&&`, 파이프·명령 치환·shell wrapper로 결합하지 않는다.',
    'method':'Inert PowerShell AST/token inspection and manual review of all 104 captured command bodies. Quoted regex alternation and native launcher wrapper excluded.',
    'confirmed_pipeline_calls':0,'confirmed_semicolon_composition_calls':0,
    'scope':'Unchanged supplied task restriction. No inert AST findings. All104 command bodies reviewed manually; quoted regex patterns and native launcher wrapper are not command composition. No retrospective permission change.'})
procedure=OUT/'policy-audit-procedure';procedure.mkdir(exist_ok=False)
shutil.copy2(Path('C:/meter-runs-20261006/audit-luna-captured-shell.ps1'),procedure/'audit-luna-captured-shell.ps1')
for name in ['luna-followup03-shell-command-input.json','luna-followup03-shell-command-findings.json']:shutil.copy2(ROOT/name,procedure/name)
save(OUT/'native-tool-review.json',{'run_id':RUN.name,'reviewed_at':now,'raw_events':len(events),'commands':commands,'file_changes':changes,
    'failed_commands':sum(i.get('exit_code') not in (None,0) for i in commands),'denial_raw_lines':denials,'confirmed_forbidden_composition_calls':0,
    'review':'All captured commands and own-checkout changes reviewed. No observed candidate serial/flash, other implementation/diagnostic source access, credential collection, global permission mutation or operator implementation repair. Fixed manufacturer/SDK reads retained. Missing rg and initially nonexistent own paths are preserved. Final resultJSON and normal turn.completed usage preserved; product and hardware are independently evaluated after freeze.',
    'raw_turn_usage':next((e.get('usage') for e in reversed(events) if e.get('type')=='turn.completed'),None),'frozen_adapter_reasoning_field':m['measurement']['tokens']['reasoning'],
    'operator_audited_user_interventions':0,'candidate_hardware_access':False,'in_run_feedback':False})
decision={'status':'eligible','reviewer':'Codex operator','user_interventions':0,
    'reason':'Luna followup3 has no confirmed forbidden shell composition, out-of-scope source/hardware/global changes or operator repair in the104 manually reviewed commands. Current run eligible; prior initial/followup1 invalid policy remains, so series quality/reference-cost remains ineligible. Normal completed exit and measured token usage preserved separately; previous followup2 native usage-limit failure and null tokens remain unchanged.',
    'intervention_review':'No operator candidate repair, replacement model call, in-run feedback or permission relaxation. Original measured intervention null retained; audited intervention0.',
    'evidence':[{'path':'operator-observation/'+name,'sha256':digest((OUT/name).read_bytes())} for name in ['shell-command-policy-audit.json','native-tool-review.json']]}
save(RUN/'operator-policy-decision.json',decision);create_review(RUN/'run-manifest.json',decision)
assert validate_review(m,RUN/'run-manifest.json')['decision']['status']=='eligible'
assert digest((RUN/'run-manifest.json').read_bytes())==f['original_terminal_manifest_sha256']
print(json.dumps({'policy_status':'eligible','commands_reviewed':104,'changes_reviewed':5,'confirmed_pipeline_calls':0,'raw_manifest_unchanged':True}))
