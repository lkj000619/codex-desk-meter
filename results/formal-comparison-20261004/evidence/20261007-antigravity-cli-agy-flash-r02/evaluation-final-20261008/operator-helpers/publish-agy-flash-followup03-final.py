"""Publish dated final review; keep prior cost snapshots and closed series intact."""
from datetime import datetime, timezone
from pathlib import Path
import json, shutil, sys
ROOT=Path.cwd();FORMAL=ROOT/'results/formal-comparison-20261004'
RUN=Path('C:/meter-followups-20261007/20261007-antigravity-cli-agy-flash-r02');OUT=RUN/'operator-observation'
PACK=Path('C:/meter-run-packages-20261007/agy-flash-followup03-final');REST=Path('C:/meter-run-restores-20261007/agy-flash-followup03-final')
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
from benchmark_support import read,save,digest
def extended(p):return Path('\\\\?\\'+str(p.resolve()))
p=read(FORMAL/'progress.json');assert p['state']=='agy_flash_followup_3_uploaded_awaiting_optical_observation'
protected={k:p[k] for k in ('previous_series','closed_agy_pro_series','closed_codex_sol_series','codex_sol_result_at_transition','closed_codex_luna_series','codex_luna_result_at_transition','agy_flash_deferred_state_at_resumption','current_series_first_result','current_series_previous_result')}
audit=read(REST/'frozen-validator-audit.json');closure=read(OUT/'operator-series-completion.json');m=read(RUN/'run-manifest.json')
assert audit['files_verified']==588 and audit['reference_review_applied'] and audit['series_closed'] and audit['normal_readable_screen_observed']
assert all(x=='pass' for x in audit['rm_items'].values()) and not audit['product_pass'] and closure['remaining_followup_rounds']==0
assert digest((PACK/'package-manifest.json').read_bytes())==audit['package_manifest_sha256']
now=datetime.now(timezone.utc).isoformat()
PUBLIC=FORMAL/'evidence'/RUN.name/'evaluation-final-20261008';PUBLIC.mkdir(parents=True,exist_ok=False)
def copy(source,name):
    dest=extended(PUBLIC/name);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(extended(source),dest)
names=['run-manifest.json','policy-review.json','operator-policy-decision.json','operator-source-freeze.json','reference-review.json','operator-reference-review-input.json']
names += [x.relative_to(extended(RUN)).as_posix() for x in extended(OUT).rglob('*') if x.is_file() and 'artifact-snapshot' not in x.parts]
for name in sorted(set(names)):copy(RUN/name,name)
for source,name in [(Path(p['ledger']),'ledger-at-review.json'),(REST/'frozen-validator-audit.json','restore-audit.json'),
    (REST/'restore-report.json','restore-report.json'),(PACK/'package-manifest.json','package-manifest.json'),
    (PACK.parent/'agy-flash-followup03-final-create.json','package-create.json'),
    (PACK.parent/'verify-agy-flash-followup03-final.py','operator-helpers/verify-agy-flash-followup03-final.py'),
    (Path(__file__),'operator-helpers/'+Path(__file__).name)]:copy(source,name)
cost=FORMAL/'evidence'/RUN.name/'cost-checkpoint-17-20261007';inputs=read(cost/'cost-checkpoint-inputs.json')
assert inputs['unique_attempts']==17 and inputs['known_normalized_tokens']==62535521 and inputs['token_measurement_coverage']=='16/17' and inputs['total_normalized_tokens'] is None
for item in inputs['input_manifests']:assert digest(extended(cost/item['snapshot_path']).read_bytes())==item['sha256']
current=next(x for x in inputs['input_manifests'] if x['run_id']==RUN.name)
assert read(cost/current['snapshot_path'])['measurement']==m['measurement'] and read(cost/current['snapshot_path'])['execution']==m['execution']
checkpoint=ROOT/p['cost_checkpoint'];raw=(cost/'checkpoint-original.md').read_bytes()
assert checkpoint.read_bytes().replace(b'\r\n',b'\n')==raw.replace(b'\r\n',b'\n')
save(PUBLIC/'cost-checkpoint-origin.json',{'recorded_at':now,'checkpoint':p['cost_checkpoint'],
    'scope':'Checkpoint17 is the17 terminal attempts before final optical review. No additional call or cost change. Final RM is dated separately; historical cost inputs are not rewritten.',
    'input_snapshot_directory':cost.relative_to(ROOT).as_posix(),'input_inventory_sha256':digest((cost/'cost-checkpoint-inputs.json').read_bytes()),
    'checkpoint_original_path':(cost/'checkpoint-original.md').relative_to(ROOT).as_posix(),'checkpoint_original_sha256':digest(raw),
    'checkpoint_repository_lf_sha256':digest(raw.replace(b'\r\n',b'\n')),
    'token_measurement_coverage':'16/17','known_normalized_tokens':62535521,'total_normalized_tokens':None})
save(PUBLIC/'snapshot-inventory.json',{'run_id':RUN.name,'round':3,'captured_at':now,
    'files':{x.relative_to(extended(PUBLIC)).as_posix():{'bytes':x.stat().st_size,'sha256':digest(x.read_bytes())} for x in extended(PUBLIC).rglob('*') if x.is_file()},
    'scope':'2026-10-08 publication and588-file independent audit of2026-10-07 frozen final followup3/video/RM review. Prior499/485 packages, original terminal cost/source and prior policy/verdicts preserved. RM reached; full product unverified and series quality/reference cost remains ineligible.'})
p.update(checked_at=now,state='agy_flash_series_closed_reference_reached',independent_series_completed=5,
    rm_review='followup03_final_reference_review_complete_with_unmeasured_items',rm_items=audit['rm_items'],reference_status='pass',product_pass=False,
    final_package_manifest_sha256=audit['package_manifest_sha256'],final_package_files_verified=588,final_package=str(PACK),final_restore=str(REST),final_snapshot=PUBLIC.relative_to(ROOT).as_posix(),
    current_optical_evidence_received=True,current_optical_evidence_kind='user_video',video_sha256=audit['video_sha256'],video_duration_seconds=62.87,
    user_initiated_reset_confirmed=True,user_power_cycle_confirmed=True,boot_press_count=3,boot_navigation_observed=True,
    continuous_30s_verified=False,continuous_30s_status='not_certified',lcd_output_present=True,normal_readable_screen_observed=True,
    orientation_feature_status='unverified',automatic_restart_observed=None,
    additional_candidate_round_start_authorized_now=False,additional_candidate_round_ready_now=False,next_model_start_authorized_now=False,next_model_execution_started=False,
    current_series_normalized_tokens=3892990,current_series_known_normalized_tokens=3892990,current_series_token_measurement_coverage='4/4',
    current_series_measured_seconds=closure['series_measured_seconds'],current_series_followup_measured_seconds=closure['followup_measured_seconds'],
    remaining_current_series_followup_seconds=closure['remaining_unused_followup_seconds'],remaining_current_series_followup_rounds=0,
    quality_reference_cost_eligible=False,policy_status='eligible',series_policy_status='invalid_for_comparison',
    candidate_current_phase='Final Flash followup3 implementation,submission,video/RM and588-file independent restoration complete. RM1-5 reached; previous series invalidity preserved. First block five series closed; remaining two independent blocks not started.',
    board_state='Last observed final frozen Flash followup3 app:58/82 and BOOT cycle before confirmed manual RESET/power cycle; then WAITING/default without retransmission. Current live board connection/state not re-probed. Serial closed; no additional upload/reset/rebuild in final review.',
    closed_agy_flash_series=dict(closure,final_package_manifest_sha256=audit['package_manifest_sha256'],final_package_files_verified=588,final_snapshot=PUBLIC.relative_to(ROOT).as_posix()),
    first_block_closed=True,formal_comparison_complete=False,
    restart_instruction='AGY Flash initial+three followups ended and reviewed. RM1-5 reached at final round3; current policy eligible, earlier series invalid_for_comparison retained. Final588-file package independently audited; product_pass false, timing/30s/IMU/full recovery unverified. Remaining4303.593sec but0 rounds: no additional candidate round. First block all5 series closed, overall5/15; no next model/block started. Preserve17 terminal costs coverage16/17 known62535521/null total and all earlier verdicts/source/evidence.')
assert all(p[k]==v for k,v in protected.items());save(FORMAL/'progress.json',p)
summary='2026-10-08 최종 보관·문서 갱신 완료. 10월7일 AGY Flash 마지막 후속3은1,141.688초·713,570 token에 구현·제출을 마쳤고, 같은 동결 펌웨어가 COM3에서 공통 frame0·1을 수락했다. 62.87초 영상과 BOOT 연속3회 확인으로58%·82% 및 사용량→글로벌 리셋→진단→사용량 복귀를 관측해 RM1~RM5 모두 pass, reference 도달로 series를 종료했다. RESET·전원 재연결은 사용자 수동 조작이며 자동 재부팅으로 단정하지 않는다. 자동 회전/흔들기·연속30초 안정성·정밀 응답 시간·전체 오류/복구·GUI 검증은 미완료라 product_pass false다. 최종588파일 독립 복원과 원본 source40개/artifact25개·영상·정책·비용·RM 연결을 검증했다. 이번 정책 eligible, 과거 후속1의 series invalid와 품질/reference 비용 제외는 유지한다. 잔여4,303.593초(71분43.593초)·남은 회차0으로 추가 호출은 없다. 최초5회+후속12회=전체17회 종료, 비용 coverage16/17·알려진62,535,521 token·전체 합계 미상이다. 첫 블록5개 모델 series 종료5/15로 전체3블록 비교는 미완료이며 다음 블록은 시작하지 않았다.'
link=PUBLIC.relative_to(ROOT).as_posix()
links='[최종 RM](../../'+link+'/reference-review.json) · [최종 독립 복원](../../'+link+'/restore-audit.json) · [series 종료](../../'+link+'/operator-observation/operator-series-completion.json) · [영상 판독](../../'+link+'/operator-observation/user-video-01/video-review.json)'
path=ROOT/'docs/experiments/next-comparison-readiness.md';lines=path.read_text(encoding='utf-8').splitlines(keepends=True);assert lines[2].startswith('확인일:');lines[2]='확인일: 2026-10-08. 상태: **'+summary+'**\n'
path.write_text(''.join(lines)+'\n## 2026-10-08 Flash 최종 평가 보관·첫 블록 종료\n\n'+summary+'\n\n'+links+'\n',encoding='utf-8')
path=FORMAL/'report.md';lines=path.read_text(encoding='utf-8').splitlines(keepends=True);assert lines[2].startswith('상태:') and lines[3].startswith('독립 series 종료');lines[2]='상태: '+summary+'\n';lines[3]='독립 series 종료5/15(첫 블록5개 완료)이며 전체 비교는 미완료다. 아래 기록은 각 당시 관측이며 최신 상태는 위 상태와 마지막 갱신을 따른다.\n'
path.write_text(''.join(lines)+'\n## 2026-10-08 Flash 마지막 후속3 최종 평가·종료\n\n'+summary+'\n\n[최종 RM](evidence/'+RUN.name+'/evaluation-final-20261008/reference-review.json) · [독립 복원](evidence/'+RUN.name+'/evaluation-final-20261008/restore-audit.json) · [series 종료](evidence/'+RUN.name+'/evaluation-final-20261008/operator-observation/operator-series-completion.json) · [비용17 원본 연결](evidence/'+RUN.name+'/evaluation-final-20261008/cost-checkpoint-origin.json). 비용17은 최종 광학 판정 전17개 terminal 원본으로 보존하며 시간/token 변화는 없다. 글로벌 화면의 FRESH 표시와 오래된 captured 시각은 [전체 제품 관측 제한](evidence/'+RUN.name+'/evaluation-final-20261008/operator-observation/product-observation-scope.json)에 별도로 남긴다. RM 화면 존재 판정을 전체 source-age 정확성으로 확대하지 않는다.\n',encoding='utf-8')
path=ROOT/'docs/plans/2026-10-07-agy-flash-remaining-followups.md';lines=path.read_text(encoding='utf-8').splitlines(keepends=True);i=next(i for i,x in enumerate(lines) if x.startswith('상태:'));lines[i]='상태: 2026-10-08 허용된후속2/3·최종 영상/RM·588파일 독립 복원 완료. 마지막 RM1~RM5 pass로 series 종료, 잔여4,303.593초·남은 회차0·추가 실행 없음. 전체 제품 합격은 미확정.\n'
path.write_text(''.join(lines)+'\n## 2026-10-08 완료 조건 검증\n\n'+summary+'\n\n'+links+'\n\n- [x] 허용된 후속2/3 각각 한 번 실행·terminal 원본과 비용 보존.\n- [x] 과거 부적격과 후속2 권한 거부 실패를 보존하고 자기 원본/입력57개 유지.\n- [x] 마지막 원본 artifact 업로드·실제 frame0/1 수락·현재 영상/BOOT 확인.\n- [x] RM 한 번 적용·series 종료·588파일 독립 복원·현재 상태 연결.\n- [x] 미측정30초/응답 시간/IMU/전체 제품 범위를 합격으로 확대하지 않음.\n',encoding='utf-8')
path=ROOT/'docs/plans/2026-10-04-formal-comparison-execution.md';lines=path.read_text(encoding='utf-8').splitlines(keepends=True);i=next(i for i,x in enumerate(lines) if x.startswith('상태:'));lines[i]='상태: '+summary+'\n';path.write_text(''.join(lines),encoding='utf-8')
path=ROOT/'docs/DOCUMENTATION_MAP.md';lines=path.read_text(encoding='utf-8').splitlines(keepends=True);i=next(i for i,x in enumerate(lines) if x.startswith('| AGY Flash 잔여 후속'));lines[i]=lines[i].replace('AGY Flash 잔여 후속 재개·현재 실행','AGY Flash 후속2/3 평가 완료·첫 블록 종료').rstrip().removesuffix('|')+' · [최종 RM](../'+link+'/reference-review.json) · [최종 독립 복원](../'+link+'/restore-audit.json) · [series 종료](../'+link+'/operator-observation/operator-series-completion.json) |\n';path.write_text(''.join(lines),encoding='utf-8')
print(json.dumps({'state':p['state'],'files':len(read(PUBLIC/'snapshot-inventory.json')['files']),'package_files':588,'series_completed':5,'rm_items':audit['rm_items']}))
