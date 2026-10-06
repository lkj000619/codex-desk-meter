"""Evidence-bound terminal policy review; never execute captured commands."""
from datetime import datetime, timezone
from pathlib import Path
import json, shutil, sys
ROOT=Path('C:/meter-followups-20261006');RUN=ROOT/'20261006-codex-cli-gpt-6-luna-r02';OUT=RUN/'operator-observation'
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
from benchmark_support import read, save, digest
from policy_review import create_review, validate_review
m=read(RUN/'run-manifest.json');f=read(RUN/'operator-source-freeze.json')
assert digest((RUN/'run-manifest.json').read_bytes())==f['original_terminal_manifest_sha256']
events=[json.loads(s) for s in (RUN/'stdout.jsonl').read_bytes().splitlines()]
commands=[dict(raw_line=n,**e['item']) for n,e in enumerate(events,1) if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='command_execution']
changes=[dict(raw_line=n,**e['item']) for n,e in enumerate(events,1) if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='file_change']
findings=read(ROOT/'luna-followup01-shell-command-findings.json')
confirmed=[v for v in findings if not v['parse_errors'] and (v['pipeline_extents'] or v['separator_extents'])]
assert len(commands)==229 and len(changes)==35 and len(events)==545
assert [v['raw_line'] for v in confirmed]==[39,288] and not any(v['separator_extents'] for v in confirmed)
assert all(v['run_id']==RUN.name for v in findings)
for item in changes:
    for change in item['changes']:assert Path(change['path']).resolve().is_relative_to((RUN/'checkout').resolve())
denials=[i['raw_line'] for i in commands if 'permission denied' in i.get('aggregated_output','').lower() or 'access is denied' in i.get('aggregated_output','').lower()]
assert not denials
now=datetime.now(timezone.utc).isoformat()
save(OUT/'shell-command-policy-audit.json',{'date':'2026-10-06','run_id':RUN.name,'reviewed_at':now,
    'raw_stdout_sha256':digest((RUN/'stdout.jsonl').read_bytes()),'confirmed_findings':confirmed,
    'ambiguous_parse_findings_excluded':[v for v in findings if v['parse_errors']],
    'frozen_task_instruction':'셸 명령은 한 호출에 하나만 실행한다. `;`, `&&`, 파이프·명령 치환·shell wrapper로 결합하지 않는다.',
    'method':'Inert PowerShell AST/token inspection and manual review of all 229 captured command bodies. Quoted regex alternation and native launcher wrapper excluded.',
    'confirmed_pipeline_calls':2,'confirmed_semicolon_composition_calls':0,
    'scope':'Unchanged supplied task restriction. Line288 attempted pipeline failed because rg was unavailable; the composed call still violates the rule. No retrospective permission change.'})
procedure=OUT/'policy-audit-procedure';procedure.mkdir(exist_ok=False)
shutil.copy2(Path('C:/meter-runs-20261006/audit-luna-captured-shell.ps1'),procedure/'audit-luna-captured-shell.ps1')
for name in ['luna-followup01-shell-command-input.json','luna-followup01-shell-command-findings.json']:shutil.copy2(ROOT/name,procedure/name)
save(OUT/'native-tool-review.json',{'run_id':RUN.name,'reviewed_at':now,'raw_events':len(events),'commands':commands,'file_changes':changes,
    'failed_commands':sum(i.get('exit_code') not in (None,0) for i in commands),'denial_raw_lines':denials,'confirmed_forbidden_composition_calls':2,
    'review':'All captured commands and own-checkout changes reviewed. No observed candidate serial/flash, other implementation/diagnostic source access, credential collection, global permission mutation or operator implementation repair. Fixed manufacturer/SDK reads retained. Missing rg and wrong local paths, intermediate test failures and default-example validator EVIDENCE_NOT_FOUND are preserved; final own result validated.',
    'raw_turn_usage':events[-1]['usage'],'frozen_adapter_reasoning_field':m['measurement']['tokens']['reasoning'],
    'operator_audited_user_interventions':0,'candidate_hardware_access':False,'in_run_feedback':False})
decision={'status':'invalid_for_comparison','reviewer':'Codex operator','user_interventions':0,
    'reason':'Luna followup1 contains two confirmed forbidden pipeline calls at raw lines39 and288. Preserve own source, firmware, all cost and product/RM observations; exclude this run from policy-eligible quality/reference-cost comparison. Initial invalid policy remains separately preserved.',
    'intervention_review':'No operator candidate repair, replacement model call, in-run feedback or permission relaxation. Original measured intervention null retained; audited intervention0.',
    'evidence':[{'path':'operator-observation/'+name,'sha256':digest((OUT/name).read_bytes())} for name in ['shell-command-policy-audit.json','native-tool-review.json']]}
save(RUN/'operator-policy-decision.json',decision);create_review(RUN/'run-manifest.json',decision)
assert validate_review(m,RUN/'run-manifest.json')['decision']['status']=='invalid_for_comparison'
assert digest((RUN/'run-manifest.json').read_bytes())==f['original_terminal_manifest_sha256']
print(json.dumps({'policy_status':'invalid_for_comparison','commands_reviewed':229,'changes_reviewed':35,'confirmed_pipeline_calls':2,'raw_manifest_unchanged':True}))
