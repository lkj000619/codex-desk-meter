from datetime import datetime, timezone
from pathlib import Path
import json, shutil, sys

ROOT=Path.cwd();FORMAL=ROOT/'results/formal-comparison-20261004'
RUN=Path('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-luna-r03');OUT=RUN/'operator-observation'
PACK=Path('C:/meter-run-packages-20261007/codex-luna-followup02-evaluation');REST=Path('C:/meter-run-restores-20261007/codex-luna-followup02-evaluation')
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
from benchmark_support import read,save,digest
p=read(FORMAL/'progress.json');audit=read(REST/'frozen-validator-audit.json');m=read(RUN/'run-manifest.json')
assert p['state']=='codex_luna_followup_02_uploaded_awaiting_optical_observation'
assert audit['files_verified']==575 and audit['reference_review_applied'] and not audit['normal_readable_screen_observed']
assert digest((PACK/'package-manifest.json').read_bytes())==audit['package_manifest_sha256']
protected={k:p[k] for k in ['previous_series','closed_agy_pro_series','deferred_agy_flash_series','closed_codex_sol_series','codex_sol_result_at_transition','current_series_first_result','current_series_previous_result']}
now=datetime.now(timezone.utc).isoformat();public=FORMAL/'evidence'/RUN.name/'evaluation-20261007'
public.mkdir(exist_ok=False)
def extended(path):return Path('\\\\?\\'+str(path.resolve()))
def copy(source,name):
    dest=extended(public/name);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(extended(source),dest)
names=['run-manifest.json','policy-review.json','operator-policy-decision.json','operator-source-freeze.json','reference-review.json','operator-reference-review-input.json']
names += [x.relative_to(RUN).as_posix() for x in OUT.rglob('*') if x.is_file() and 'artifact-snapshot' not in x.relative_to(RUN).parts]
for name in sorted(set(names)):copy(RUN/name,name)
for source,name in [(Path(p['ledger']),'ledger-at-review.json'),(REST/'frozen-validator-audit.json','restore-audit.json'),(REST/'restore-report.json','restore-report.json'),(PACK/'package-manifest.json','package-manifest.json'),(PACK.parent/'codex-luna-followup02-evaluation-create.json','package-create.json'),(Path(__file__),'operator-helpers/'+Path(__file__).name)]:copy(source,name)
prior=FORMAL/'evidence'/RUN.name/'observation-awaiting-20261007'
copy(prior/'cost-checkpoint-inputs.json','cost-checkpoint-inputs-at-observation.json')
save(public/'snapshot-inventory.json',{'run_id':RUN.name,'round':2,'captured_at':now,
    'files':{x.relative_to(public).as_posix():{'sha256':digest(extended(x).read_bytes()),'bytes':x.stat().st_size} for x in public.rglob('*') if x.is_file()},
    'scope':'Immutable followup2 final video/RM review.575-file package independently restored. Current eligible policy separate from prior invalid series; native usage-limit environment failure and null token costs preserved. Colored LCD output present but readable values/views unmet, BOOT/RST both confirmed without exact timestamps. One authorized final followup remains.'})
p.update(checked_at=now,state='codex_luna_followup_02_reviewed_unreadable_screen',rm_review='followup02_review_complete_with_unmeasured_items',
    rm_items=audit['rm_items'],reference_status='fail',product_pass=False,
    final_package_manifest_sha256=audit['package_manifest_sha256'],final_package_files_verified=575,final_package=str(PACK),final_restore=str(REST),final_snapshot=public.relative_to(ROOT).as_posix(),
    current_optical_evidence_received=True,current_optical_evidence_kind='user_video',video_sha256=audit['video_sha256'],video_duration_seconds=38.55,
    user_initiated_reset_confirmed=True,boot_press_count=None,boot_navigation_observed=None,continuous_30s_verified=False,
    lcd_output_present=True,normal_readable_screen_observed=False,additional_candidate_round_ready_now=True,
    candidate_current_phase='Followup2 terminal, frozen/restored/host/hardware/video/RM review complete. LCD now shows duplicated rotated clipped glyphs, no readable58/82 or three information views. Native usage-limit failure and unknown token cost preserved. One already-authorized own-source followup remains within floor2965seconds.',
    board_state='Same Luna followup2 app onCOM3; current38.55s video shows rotated/duplicated/clipped glyphs. User pressed BOOT and RESET; exact times/count unavailable. Host writes0/1 complete but device acceptance unconfirmed; serial closed.',
    host_python_unit_tests_passed=22,host_c_executables_passed=3,host_provider_fixture_validity_checks_passed=17,
    collector_matches_common_reference_payload=True,common_wire_encoder_exact_match=True,frozen_operator29_pipeline_completed=False,
    restart_instruction='Followup2 evaluated and575-file package independently verified; do not repeat candidate or repair/rebuild original source. Readable LCD objective unmet. User already authorizes last round3 within remaining2965.735sec, floor2965timeout, from own frozen91f7de6 and observational feedback only. Prepare fresh10/7 non-model receipt before one call; preserve current/prior invalid series costs and all refs, Muse/Pro/Sol closed, Flash deferred. No new initial, replacement model or extra entitlement probe.')
assert all(p[k]==v for k,v in protected.items());save(FORMAL/'progress.json',p)
summary='2026-10-07 Luna 후속2 평가 완료: build·COM3 원본 실행은 RM1 pass, 공통 host 경로·USB 첫 수신과 완전한 수락 미확인을 구분해 RM2 partial이다. 38.55초 영상에서 글자 출력은 생겼지만 회전·중복·잘림으로58%/82%와 세 정보 화면을 읽을 수 없어 RM3/RM4 fail이다. 사용자는 BOOT와 RESET 모두 눌렀다고 확인했으며 정확한 조작 시점/횟수가 없어 분리된 BOOT 순환은 RM5 not_run이다. 화면 변화가 자동 재부팅이라는 추정은 하지 않는다. Reference fail·product_pass false, 이번 정책 eligible·과거 series invalid를 유지한다. 최종575파일 package 독립 검증 완료; native 사용량 한도 종료·token null·전체 coverage13/14·알려진57,517,475 token을 보존한다. 정상 가독 화면 미도달이므로 기존 승인 범위의 마지막 후속3을 준비할 수 있다. 잔여2,965.735초·최대1회이며 timeout 상한floor2,965초다. 아직 마지막 후보 호출은 없다.'
links='[후속2 최종 RM](../../'+public.relative_to(ROOT).as_posix()+'/reference-review.json) · [독립 복원](../../'+public.relative_to(ROOT).as_posix()+'/restore-audit.json)'
path=ROOT/'docs/experiments/next-comparison-readiness.md';lines=path.read_text(encoding='utf-8').splitlines(keepends=True);lines[2]='확인일: 2026-10-07. 상태: **'+summary+'**\n'
path.write_text(''.join(lines)+'\n## 2026-10-07 Luna 후속2 영상 평가 완료\n\n'+summary+'\n\n'+links+'\n',encoding='utf-8')
path=FORMAL/'report.md';lines=path.read_text(encoding='utf-8').splitlines(keepends=True);lines[2]='상태: '+summary+'\n'
path.write_text(''.join(lines)+'\n## 2026-10-07 Luna 후속2 영상 평가·마지막 후속 조건\n\n'+summary+'\n\n[최종 RM](evidence/'+RUN.name+'/evaluation-20261007/reference-review.json) · [독립 복원](evidence/'+RUN.name+'/evaluation-20261007/restore-audit.json). 전체14회 후보 종료·독립 series 종료3/15로 비교는 미완료다.\n',encoding='utf-8')
path=ROOT/'docs/plans/2026-10-06-codex-luna-remaining-followups.md';text=path.read_text(encoding='utf-8');lines=text.splitlines(keepends=True);index=next(i for i,line in enumerate(lines) if line.startswith('상태:'));lines[index]='상태: 2026-10-07 후속2 평가·최종575파일 독립 복원 완료. 정상 가독 화면 미도달, 마지막 후속3 준비 가능·잔여2,965.735초·최대1회.\n'
text=''.join(lines).replace('- [ ] 같은 COM3·MAC','- [x] 같은 COM3·MAC').replace('- [ ] 현재 LCD/BOOT/30초 사용자 관측','- [x] 현재 LCD/BOOT/30초 사용자 관측')
path.write_text(text+'\n## 2026-10-07 후속2 최종 판정\n\n'+summary+'\n\n'+links+'\n',encoding='utf-8')
path=ROOT/'docs/DOCUMENTATION_MAP.md';lines=path.read_text(encoding='utf-8').splitlines(keepends=True);index=next(i for i,line in enumerate(lines) if line.startswith('| Luna 남은 후속2/3'));lines[index]=lines[index].rstrip('\n').rstrip()[:-1]+' · [후속2 최종 RM](../'+public.relative_to(ROOT).as_posix()+'/reference-review.json) · [최종 복원](../'+public.relative_to(ROOT).as_posix()+'/restore-audit.json) |\n';path.write_text(''.join(lines),encoding='utf-8')
print(json.dumps({'state':p['state'],'snapshot_files':len(read(public/'snapshot-inventory.json')['files']),'package_verified':575,'remaining_seconds':p['remaining_current_series_followup_seconds']}))
