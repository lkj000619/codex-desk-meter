# AGY 첫 pilot 실행 및 사후 검증 — 2026-09-26 KST

## 판정

**ENVIRONMENT_FAILED / PILOT_NOT_PASSED**. 준비된 첫 run을 runner로 한 번
실행했으나 AGY 1.2.11의 CLI 인자 해석 오류로 exit 2 종료됐다. 모델 응답·usage
이벤트와 구현 산출물이 없으므로 모델 능력이나 제품 성능의 실패로 채점하지 않는다.
정식 반복 benchmark는 진행하지 않는다. 이번 run을 재실행하거나 prompt를 추가 전달하지 않았다.

| 항목 | 관측 |
|---|---|
| Run ID | `20260926-antigravity-cli-agy-flash-medium-r01` |
| Baseline | `benchmark-v2-baseline-20260925`, `eef278013428a79c29d6b9456018049af149ca61` |
| Model / CLI | `gemini-3.8-flash-medium` / AGY 1.2.11 |
| R10 발효 UTC | `2026-09-25T18:10:19.917Z` |
| 실행 시작 UTC | `2026-09-25T18:10:35.776Z` |
| 실행 종료 UTC | `2026-09-25T18:10:35.871Z` |
| runner 측정 시간 | 약 0.093초, 모델 작업 시간으로 해석하지 않음 |
| 종료 | agent exit 2, wrapper exit 1, `environment_failed` |
| stdout | 0 bytes; init/result/usage 없음 |
| token/tool 계측 | 원본 manifest의 `null` 유지; 0으로 추정하지 않음 |
| 제품 평가 | 빌드·자동 제품 시험·실물 검증 모두 `not_run` |
| receipt | `pilot_pass=false` 유지 |

## 실행 및 비교 조건

사용자는 이번 대화에서 정량 비교 조건을 유지한 첫 AGY 실행과 종료 후 검증을
명시적으로 요청했다. 실행 전 COM3 `chip_id`가 exit 0으로 ESP32-S3 rev v0.2를
확인했다. run 날짜, clean checkout/HEAD, profile, 전달 prompt, 전체 입력 bundle과
최신 receipt evidence를 검사한 뒤 checkout 밖의 `launch-authorization.json`에 발효를 기록했다.

동결 baseline의 wrapper와 runner를 사용했고 최신 receipt는 절대 경로로 지정했다.
최초 사전 검사에서는 동결 checkout 안의 과거 receipt를 선택해 base_commit 불일치로
차단됐으며, 다음 경로 전달 시 PowerShell의 Unicode stdin 인코딩 문제로 차단됐다.
두 시도 모두 AGY 실행 이전의 검사 실패다. 작업 저장소에서 경로를 해석해 최신 receipt
검증을 통과한 뒤 실제 runner를 정확히 한 번 실행했다.

고정 prompt는 runner의 stdin 경로로 한 번 전달을 시도했다. CLI가 인자 파싱 단계에서
실패했으므로 모델이 prompt를 수신했다고 주장하지 않는다. 수동 prompt 입력,
후속 구현 피드백, agent 코드 수정, flash/erase는 수행하지 않았다.

## 원인과 후속 조건

고정 profile의 argv는 `agy --print --input-format text ...` 순서다. 원본 stderr:

```text
Error: --print took "--input-format" as its prompt, so the intended prompt was left as an argument and ignored.
Attach the prompt to the flag (--print='your prompt') and move --input-format elsewhere on the command line.
```

`agy --help`도 `--print`를 단일 prompt 실행 플래그로 표시한다. 현재 profile이
실제 CLI의 stdin/인자 처리를 검증하지 못했다는 점이 이번 pilot에서 드러났다.
정확한 수정 argv는 추가 검증 전까지 확정하지 않는다. mock-stream 시험 통과는
설치된 실제 CLI의 argument parser 호환성을 증명하지 않는다.

후속 실행은 별도 준비 작업에서 실제 CLI의 stdin 단일 전달 규칙을 확인하고,
profile/receipt hash를 다시 고정한 뒤 새 run ID로 진행해야 한다. 기존 run,
baseline, profile, 원본 logs를 덮어쓰지 않는다. 기존의 회당 승인 조건과 변경된
profile 적용 범위를 확인하고 새 실행을 기록한다. 이번 실행 요청에 실패를 숨기는
자동 재시도를 포함시키지 않았다.

## 사후 검증 및 보존

검토자: Codex maintainer, 2026-09-26 KST.

- run-manifest schema, operator 상태, 원본 evidence hash와 E2E 평가 manifest schema 통과.
- checkout clean 및 HEAD가 준비 당시와 동일함을 확인. 제품 결과 파일 없음.
- 원래 settings/instructions/hooks의 SHA-256 3개 일치, wrapper active lock 해제 확인.
- historical `validate-experiment-result.py`는 E2E experiment_id를 거부했다.
  이를 제품 실패로 취급하지 않고 E2E run에 맞는 schema/operator/evidence 검사를 수행했다.
  E2E 제품 result가 없으므로 제품 validator·build·flash를 실행할 대상은 없다.
- local archive 완료. 원본 로그는 Git 밖 run 디렉터리에 보존.
  archive commit: `45dd17b222da46292dbfd737efe27211755ab3cb`.
  archive에 기록된 implementation commit `cef90692da5c3860df2a4c4f6af14503dd7c42ae`는
  변경 없는 초기 snapshot이며 제품 구현이 생성됐다는 뜻이 아니다.

원본 위치: `C:\Espressif\benchmark-runs\20260926-antigravity-cli-agy-flash-medium-r01`.
`run-manifest.json`, `stdout.jsonl`, `stderr.txt`, `prompt.txt`, `profile.json`,
`launch-authorization.json`, `implementation.bundle`를 보존했다.
검증 hash 목록은 [사후 검증 JSON](agy-pilot-result-20260926.json)에 기록한다.
