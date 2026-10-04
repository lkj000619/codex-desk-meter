# 비교·관측·복원 도구 사용

2026-10-02 구현. 이 문서는 운영자 명령과 파일 형식을 설명한다. 예산·판정의 원본은
[운영 계약](comparison-operating-contract.md), 현재 실행 준비 상태는
[readiness](next-comparison-readiness.md)다. 후보에게 이 문서나 운영 도구를 제공하지 않는다.

## 최초 실행과 후속 회차

### 새 비교의 baseline 고정

2026-10-03 보완. 새 비교는 **제품 입력과 운영 평가 기준을 하나의 새 baseline commit**으로 고정한다.
후보 allowlist 57개와 필수 MD 3개를 유지하며 새 RM5/F9 기준·관측/보존 도구는
새 commit에 포함한다. 2026-10-04 실행 경계 보완에서 그중 AGY 권한 정책의 금지된
`git log` 허용 규칙을 제거했다. 새 동결의 해당 1개 파일 변경은 활성 5개 조합에 동일 제공한다.
나머지 56개 파일의 archive bytes는 이전 `85ba108`과 대조한다. 과거 commit/tag·receipt·package는 그대로 둔다. 기존 baseline에 새 도구만
겹쳐 적용하는 overlay 방식은 이번 비교에서 사용하지 않는다.

동결 담당자는 수정 사항을 검토·커밋하고 해당 commit의 깨끗한 operator checkout에서 다음을 확인한다.

1. 이전 `85ba108`과 새 commit을 각각 `git archive`로 추출해 allowlist 경로·각 파일 SHA-256을 대조한다.
   working checkout의 CRLF/LF 차이 대신 실제 전달될 archive bytes를 비교한다.
2. 새 commit에서 전체 회귀와 fixture 검사를 수행하고 그 commit을 모든 profile의 `check`·`prepare`
   `--baseline`에 전달한다. `prepare`는 선택 baseline과 HEAD가 같고 작업 트리가 깨끗해야 한다.
3. 새 profile·input/reference·comparison identity로 receipt를 발급·검증한다. 기존 receipt의 날짜나 hash만 고쳐 재사용하지 않는다.

`prepare`는 Git에서 추출한 전체 baseline 파일을 `operator-baseline.zip`에 보존한다. Git 이력이나
사용자 설정은 넣지 않으며, 이 ZIP은 후보 checkout 밖에 있다. ZIP과 `profile.json`의 SHA-256은
`run-manifest.json`의 `operator.evidence`에 연결된다. 후속 회차는 같은 ZIP을 전달받는다.
따라서 후보가 읽을 수 있는 3개 MD/57개 파일과 운영자가 복원할 기준 문서·도구를 구분한다.

`package-evidence.py create/restore`는 등록된 ZIP·profile hash를 검증하고 ZIP을 임시 root에 풀어
`evaluation_criteria_sha256`, `input_bundle_sha256` 등 기록된 입력 hash를 재계산한다.
틀린 평가 hash는 거부한다. 복원 보고서의 `operator_baseline_verified: true`가 이 연결의 확인값이다.
ZIP 없는 과거 package는 기존 방식으로 복원하고 이 값은 false다. 과거 검증에 새로운 요건을 소급하지 않는다.
실제 평가도 동결 commit의 도구로 수행한다. 회귀·schema·hash 검증은 도구의 실물 정확성을 대신하지 않는다.

검증한 profile과 새로 고정한 baseline을 사용한다. 기존 tag는 그대로 보존한다.
`check`·`prepare`·`init`은 모델을 실행하지 않는다. run root와 ledger는 후보 checkout 밖의 ASCII 경로다.

```powershell
python -X utf8 scripts/benchmark.py check --baseline <new-frozen-commit> --profile <verified-profile.json>
python -X utf8 scripts/benchmark.py prepare --baseline <new-frozen-commit> --profile <verified-profile.json> --root C:/meter-runs --phase benchmark --seed 1 --timeout 7200
python -X utf8 scripts/comparison.py init --ledger C:/meter-runs/<model>-<independent-repetition>-comparison.json --directory <prepared-run> --reference-inputs experiments/reference/codex-7923f96/reference-inputs.json
python -X utf8 scripts/comparison.py show --ledger C:/meter-runs/<model>-<independent-repetition>-comparison.json
python -X utf8 scripts/benchmark.py run <prepared-run> --receipt <reviewed-preflight.json>
```

comparison receipt에는 기존 access policy·base/profile hash·인프라 checks/evidence와 함께
`infrastructure_ready: true`, `comparison_id`, `input_bundle_sha256`, `reference_inputs_sha256`가 필요하다.
`capabilities`의 `read/write/list/host_build/host_test/idf_build/vendor_reference/telemetry/settings`는
각각 `{"status":"pass","evidence":"상대-증거-파일"}`로 기록한다. 파일 hash는 receipt의 `evidence`에 둔다.
운영자가 **해당 profile의 실제 CLI 세션**에서 허용·거부·계측·설정을 확인한 원본을 사용한다.
설정 선언이나 도구의 synthetic 시험만으로 실제 권한 확인을 대신하지 않는다.
runner는 실제 사용한 receipt와 그 evidence를 run 안에 사본/hash로 보존한다.
이 연결 run에는 제품 `pilot_pass`를 요구하지 않는다. comparison 없는 기존 run의 pilot gate는 유지한다.

종료된 후보 source와 첫 결과는 평가 후 동결한다. RM review JSON은 `run_id`,
`reference_inputs_sha256`, `items`의 RM1~RM5를 포함한다. 각 항목은
`status: pass/partial/fail/not_run`과 `evidence: [{"path":"run-root-상대-파일","sha256":"..."}]`다.
평가한 항목에는 근거가 필요하다. 다섯 항목 모두 pass일 때 후속 생성을 중지한다.

```powershell
python -X utf8 scripts/comparison.py review --directory <terminal-run> --report <rm-review.json>
python -X utf8 scripts/comparison.py prepare-next --ledger C:/meter-runs/<model>-<independent-repetition>-comparison.json --root C:/meter-followups --feedback <feedback.json>
python -X utf8 scripts/comparison.py stop --ledger C:/meter-runs/<model>-<independent-repetition>-comparison.json
```

feedback은 `previous_run_id`, `previous_commit`, `target_ids`(RM/C/F/I), `observed`, `expected`,
`evidence: [{"path":"직전-run-안의-절대-파일","sha256":"..."}]`를 갖는다. manager가 남은 회차·초를 추가한다.
후속은 자기 직전 Git bundle을 복제하며 같은 profile·baseline·공통 입력을 보존한다.
최초 전달 prompt를 운영자 영역의 `common-task.txt`와 ledger hash에 고정하며 매 후속에 전문을
새 run ID로 다시 전달한다. 원래 후보 파일을 수정한 내용으로 제한을 다시 구성하지 않는다.
후보용 `candidate-feedback.json`은 `.benchmark-inputs/feedback.json`으로 복사하고, 자기 직전
관측 증거만 `.benchmark-inputs/feedback-evidence/`에 복사한다. 후보에는 상대 경로·hash를 제공한다.
원본 절대 경로는 운영자 `feedback.json`에 보존한다. 실행 전후와 package 복원에서 후보용 사본을 검증한다.
최초 7,200초, 후속 최대 3회·누적 7,200초를 실제 runner timeout에 적용한다.
실패·중단·timeout의 실제 경과 시간도 차감한다. 종료 시간에는 process 정리 overhead가 포함될 수 있다.

`stop`은 새 회차를 막는다. 진행 중 process 중지는 실행 terminal에서 Ctrl+C로 처리한다.
강제 process 종료로 ledger가 running에 남으면 자동으로 예산을 복구하지 않는다.
원본 terminal manifest에 정확한 시간·종료 사유를 기록하고
`comparison.py reconcile --directory <run>`으로 종료 비용을 연결한 뒤 평가한다.
`.lock`이 남은 경우에도 현재 작업의 종료 여부를 확인하기 전에는 새 실행을 만들지 않는다.

### 정책 준수 검토

2026-10-04 보완. 새 baseline에서 prepare한 benchmark run은 `policy_review_required: true`다.
RM/제품 판정과 별도로 운영자가 전체 도구 로그·참조 범위·사람의 개입을 검토한다.
운영자 영역에 검토 메모를 저장하고 아래 decision JSON을 작성한다. evidence 경로는 run root 상대 경로다.

```json
{
  "status": "eligible",
  "reviewer": "검토자 이름",
  "reason": "전체 로그와 허용 참조를 검토한 구체적 판정 근거",
  "user_interventions": 0,
  "intervention_review": "외부 구현 피드백·사람의 코드 수정 여부를 확인한 근거",
  "evidence": [{"path": "policy-review-notes.txt", "sha256": "<메모의 SHA-256>"}]
}
```

```powershell
python -X utf8 scripts/review-policy.py --manifest <terminal-run>/run-manifest.json --decision <decision.json>
```

`eligible`·`invalid_for_comparison`·`unverified` 중 판단한다. 알려진 개입 횟수와 모순되는 값은 거부한다.
원본 계측이 null이면 운영자가 검토해 확인한 횟수를 decision에 기록할 수 있으며 원본 null은 유지한다.
개입 횟수만으로 적격을 자동 판정하지 않는다. 외부 구현 피드백·사람의 코드 수정은 부적격이며,
검토할 로그가 부족하면 unverified다. `policy-review.json`은 run/profile/input/raw 로그·검토 근거에
결합하고 기존 terminal manifest를 수정하지 않는다. 이미 작성한 review를 덮어쓰지 않는다.
검토 원본이 잘못됐으면 원본을 보존하고 후속 정정의 날짜·범위를 별도 기록한다.

품질·순위 표는 검증된 eligible만 포함한다. RM 도달 비용도 앞선 회차 전체의 적격성을 요구한다.
미검토·위반·미검증 실행의 비용과 제외 사유는 전체 시도 표에 남긴다. package는 해당 검토와
근거를 함께 보존하고 독립 복원한다. 과거 flag 없는 실행에는 새 gate를 소급하지 않는다.

### AGY 설정 scope와 중단 복구

AGY는 `agy_pilot_environment.py --backup-dir <private-backup> --workspace <candidate-checkout> run -- <runner-command>`로
runner 전체를 감싼다. wrapper가 같은 `.gemini` root에 원자적 OS lock을 잡으므로 backup 경로가 달라도
동시 진입을 거부한다. `.agy-pilot.lock`은 영구 lock 파일이며 삭제하지 않는다.
wrapper 중단 시 child process tree 종료를 확인한 다음 전역 설정을 복원한다. 종료 확인에 실패하면
원본 backup과 owner journal을 남기며 새 실행을 막는다.

강제 종료 후에는 남은 AGY 자식 process가 종료됐는지 확인하고 `.agy-pilot-owner.json`에 기록된
원래 backup을 `agy_pilot_environment.py --backup-dir <original-private-backup> restore`로 복원한다.
`--force`는 검토한 내용 차이만 무시하며 다른 소유자의 lock을 빼앗지 않는다. private 원본 설정은
공개 증거에 넣지 않는다. 이 lock은 wrapper 사이를 조정하며, 사용자가 직접 실행한 AGY나 편집기까지 잠그지는 않는다.

## 비용 집계

```powershell
python -X utf8 scripts/summarize-benchmark.py <run-manifest-1.json> <run-manifest-2.json> --output <new-summary.md>
```

모든 회차 manifest를 전달한다. 유효 completed의 조건부 표, 실패를 포함한 전체 시도 표,
최초·후속·누적·RM 도달 비용 표를 출력한다. 후속은 독립 반복 수에 넣지 않는다.
부분 입력 목록은 완전한 도달 비용을 입증하지 않는다. 시간/token coverage를 함께 읽는다.
정규화 token은 알려진 input+output이며 provider total을 섞거나 미측정을 0으로 채우지 않는다.

## 입력 복구와 production 의미 검사

[복구 입력](../../experiments/reference/codex-7923f96/reference-inputs.json)은 원본 sender의 raw fixture,
`7923f96` source와 실제 수락 frame을 대조한 목록이다. `expected-frames.jsonl`과 `schedule.json`의
전송 간격·기준 시각·원본 byte를 보존한다. 값은 synthetic stale이며 58/82는 남은 비율이다.
새 reference 복구는 `reference_inputs.py --repository <repo> --evidence <original-sender-root> --commit <frozen-commit> --output <new-root>`를 사용한다.

```powershell
python -X utf8 scripts/observe-product.py --frames experiments/reference/codex-7923f96/expected-frames.jsonl --reference-time 2026-09-30T18:40:49Z --schedule experiments/reference/codex-7923f96/schedule.json --output <new-oracle.json>
python -X utf8 scripts/evaluate-production.py trace --checkout <candidate-checkout> --adapter <adapter.json> --stimulus <trace.json> --output <new-trace-root>
```

오프라인 oracle은 제품 실행 증거가 아니다. production adapter는 실제 후보 parser/cache/view 코드에
연결해야 한다. adapter JSON은 `argv` 배열(`{stimulus}`·`{output}` 치환), `timeout_seconds`(1~60),
`production_files`·`linkage_evidence`의 checkout 상대 경로→hash, `linkage_reviewed: true`를 갖는다.
운영자가 실제 코드 연결을 검토한다. 로그·입력·출력·production hash를 함께 보존한다.

trace JSON은 `reference_time`, `monotonic_anchor`, `events`를 갖는다. event는 `seconds`와
선택적 `wire`(cdm/1 문자열), 또는 `reset: true`와 새 `reference_time`이다. wire 없는 event는 clock 진행이다.
adapter는 `{"views":[...]}`를 출력한다. 각 view는 `clock_status/reference_time/source_stale/receive_stale/sequence/payload/error_code`,
수신 event의 `accepted`, `display_values`를 포함한다. display key는 `provider_id/agent_id/account_profile_id/window_id`,
값은 `unit/percent_remaining/remaining_units/used_units/limit_units/resets_at`다.
값 변화·300초 경계·미래 시각·손상·sequence·clock 재설정을 사건으로 넣어 검사한다.
`conformance_pass`는 제공한 trace에 대한 판정이며 전체 `product_pass`는 별도 평가한다.

## 단일 포트 관측과 광학 결합

```powershell
python -X utf8 scripts/observe-product.py --send --port <explicit-port> --frames <frozen-frames.jsonl> --output <new-capture-root>
python -X utf8 scripts/evaluate-production.py optical --capture <capture-root>/capture.json --annotations <optical-annotations.json> --output <new-optical-report.json>
```

`--send --port`는 명시적으로 실물 포트를 연다. 한 연결에서 송신·raw serial·시각·sequence/hash를 수집한다.
DTR/RTS를 open 전에 내리지만 실제 reset·재열거 여부는 따로 관측한다.
`--writer-adapter` JSON의 `module_path/module_sha256/function`으로 후보 USB writer를 연결할 수 있다.
함수는 `(owned_serial, frame)`를 받아 정확한 frozen wire를 write하고 byte 수를 반환한다.
기본 경로는 operator replay다. write 완료, CDM_RX 수락 로그, CDM_DISPLAY marker는 별도 값이다.
수락 로그는 protocol ACK가 아니며 실제 LCD를 입증하지 않는다. 기존 read queue는 송신 전 로그로 분리한다.

### 후보별 수신 성공 로그 연결

2026-10-02 보완. 후보 계약은 CDM_RX라는 문자열을 요구하지 않는다. 기본 관측 경로의
`CDM_RX sequence=<n> result=0` 인식은 기존 reference 호환용이다. 다른 형식은 운영자가
실제 receiver source와 로그 발행 위치를 검토한 후 `--receiver-log <config.json>`으로 연결한다.
후보 firmware나 동결 입력에 로그 추가 patch를 요구하지 않는다.

```json
{
  "acceptance_template": "RX seq={sequence} accepted",
  "reviewer": "operator",
  "evidence_path": "receiver-source-review.txt",
  "evidence_sha256": "<검토 기록의 SHA-256>"
}
```

`acceptance_template`은 정규식이 아닌 한 줄의 literal 문자열이며 `{sequence}`가 정확히 한 개다.
LF 또는 CRLF로 끝난 전체 로그 행이 해당 순번으로 치환한 문자열과 같아야 수락으로 인식한다.
거부 로그·다른 순번·잘린 행·추가 prefix는 인정하지 않는다. 여러 read에 걸친 한 행은 누적해 판정한다.
`evidence_path`는 config 디렉터리 상대 경로 또는 절대 경로다. 검토 기록에는 후보 commit/artifact,
receiver source 경로/hash, 성공 로그가 schema/CRC/sequence 검증 후 발행되는 위치와 의미를 적는다.
도구는 검토자의 의미 판단을 자동 증명하지 않는다. raw bytes와 검토 근거가 이를 뒷받침해야 한다.
적용한 설정은 절대 경로로 해석한 `receiver-log.json`, 근거 원본은 `receiver-log-review.bin`으로
capture에 보존하고 둘 다 evidence hash에 연결한다. 수신 시각은 완전한 로그를 읽은 host 시각이며
firmware 내부 수락 시각을 정밀 측정한 값은 아니다.

```powershell
python -X utf8 scripts/observe-product.py --send --port <explicit-port> --frames <frozen-frames.jsonl> --receiver-log <reviewed-config.json> --output <new-capture-root>
```

timestamp 등 가변 prefix를 포함해 이 literal 형식으로 연결할 수 없는 로그나 수신 성공 로그가 없는
후보는 자동 광학 결합을 `not_run`과 사유로 남긴다. 도구 미지원만으로 RM/제품 fail을 선언하지 않는다.
운영자가 원본 로그·frame·영상의 연결을 독립 검토할 수 있으면 별도 RM review 근거로 기록하며,
정밀 수신→LCD 시간은 입증한 경우에만 판정한다. capture의 수신 시각을 수동으로 채워 넣지 않는다.
모든 후보에 같은 연결 절차를 적용하고 후보별 설정·검토 비용을 운영자 비용으로 남긴다.

광학 annotation은 `capture_sha256`, `clock_alignment: {status:"verified",evidence:{path,sha256}}`,
`observations`를 갖는다. observation에는 `sequence/frame_sha256/seconds/expected_values/observed_values/evidence`를 넣는다.
`expected_values`는 전송 frame에서 파생한 display key와 값의 부분집합이며,
글로벌 리셋 전체 목록은 `global_resets` key로 연결한다. 임의의 숫자를 기대값으로 넣지 않는다.
`seconds`는 capture host monotonic 시각과 정렬한 media 관측 시각이다. 운영자가 실제 가시 값과
영상/사진 hash를 확인한다. 수락과 frame 연결·값 일치·수락/송신→가시 지연을 검사하되,
표본 광학 판정으로 30초 유지·BOOT·단절 복구 등 미측정 조건을 합격 처리하지 않는다.

## 독립 복원

```powershell
python -X utf8 scripts/package-evidence.py create --directory <reviewed-terminal-run> --output <new-package-root>
python -X utf8 scripts/package-evidence.py restore --package <package-root> --output <new-independent-root> --expected-sha256 <create가-출력한-package-manifest-sha256>
```

검토·동결된 clean 구현 commit, run/operator evidence, result가 참조하는 ignored 파일과
빌드 binary를 보관한다. build pass는 app/ELF/map/bootloader/partition artifact를 요구한다.
원본 result와 복원 경로에 맞춘 사본은 별도 보존한다. 신뢰한 manifest hash로 목록·byte 수·hash·
상대 경로를 검증하고 원래 checkout을 사용하지 않는 새 root에서 E2E validator를 실행한다.
복원 시험은 보존 가능성을 검증하며 미실시 실물 평가를 추가하지 않는다.
