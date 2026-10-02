# 비교·관측·복원 도구 사용

2026-10-02 구현. 이 문서는 운영자 명령과 파일 형식을 설명한다. 예산·판정의 원본은
[운영 계약](comparison-operating-contract.md), 현재 실행 준비 상태는
[readiness](next-comparison-readiness.md)다. 후보에게 이 문서나 운영 도구를 제공하지 않는다.

## 최초 실행과 후속 회차

검증한 profile과 새로 고정한 baseline을 사용한다. 기존 tag는 그대로 보존한다.
`check`·`prepare`·`init`은 모델을 실행하지 않는다. run root와 ledger는 후보 checkout 밖의 ASCII 경로다.

```powershell
python -X utf8 scripts/benchmark.py check --baseline <new-frozen-commit> --profile <verified-profile.json>
python -X utf8 scripts/benchmark.py prepare --baseline <new-frozen-commit> --profile <verified-profile.json> --root C:/meter-runs --phase benchmark --seed 1 --timeout 7200
python -X utf8 scripts/comparison.py init --ledger C:/meter-runs/comparison.json --directory <prepared-run> --reference-inputs experiments/reference/codex-7923f96/reference-inputs.json
python -X utf8 scripts/comparison.py show --ledger C:/meter-runs/comparison.json
python -X utf8 scripts/benchmark.py run --directory <prepared-run> --receipt <reviewed-preflight.json>
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
python -X utf8 scripts/comparison.py prepare-next --ledger C:/meter-runs/comparison.json --root C:/meter-followups --feedback <feedback.json>
python -X utf8 scripts/comparison.py stop --ledger C:/meter-runs/comparison.json
```

feedback은 `previous_run_id`, `previous_commit`, `target_ids`(RM/C/F/I), `observed`, `expected`,
`evidence: [{"path":"직전-run-안의-절대-파일","sha256":"..."}]`를 갖는다. manager가 남은 회차·초를 추가한다.
후속은 자기 직전 Git bundle을 복제하며 같은 profile·baseline·공통 입력을 보존한다.
최초 7,200초, 후속 최대 3회·누적 7,200초를 실제 runner timeout에 적용한다.
실패·중단·timeout의 실제 경과 시간도 차감한다. 종료 시간에는 process 정리 overhead가 포함될 수 있다.

`stop`은 새 회차를 막는다. 진행 중 process 중지는 실행 terminal에서 Ctrl+C로 처리한다.
강제 process 종료로 ledger가 running에 남으면 자동으로 예산을 복구하지 않는다.
원본 terminal manifest에 정확한 시간·종료 사유를 기록하고
`comparison.py reconcile --directory <run>`으로 종료 비용을 연결한 뒤 평가한다.
`.lock`이 남은 경우에도 현재 작업의 종료 여부를 확인하기 전에는 새 실행을 만들지 않는다.

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
