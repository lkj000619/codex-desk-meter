# AGY 후속 pilot 실행·검증 — 2026-09-26 KST

## 현재 판정

**PILOT_NOT_PASSED / PERMISSION_POLICY_BLOCKED**. 사용자 요청에 따라 후속 실행을
진행했다. 프롬프트 전달은 해결됐지만 r03의 첫 `dir` 명령이 scoped allow 정책에 없어
headless 환경에서 자동 거부됐다. 제품 구현·빌드·실물 평가는 모두 `not_run`이다.
권한 거부를 우회하거나 추가 구현 지시를 보내지 않았다. 원본 run은 각각 보존한다.

| 관측 | r02 | r03 |
|---|---|---|
| Run ID 접미사 | `20260926-antigravity-cli-agy-flash-medium-r02` | `20260926-antigravity-cli-agy-flash-medium-r03` |
| 전달 방식 | `--print=` + 원문 stdin | profile에 고정한 어댑터가 stdin을 읽고 `--print=원문` 인자로 1회 전달 |
| runner 시간 | 약 0.766초 | 11.125초 |
| CLI exit | 1 | 0 |
| 결과 | empty prompt, 모델 turn 없음 | 1 turn, 도구 명령 거부 후 종료 |
| runner 상태 | `environment_failed` | `completed` — 사후 검토에서 환경 실패 판정 |
| 제품 산출물 | 없음 | 없음 |

## 전달 수정과 검증

설치 CLI는 text-mode stdin을 읽지 않았다. r02는 empty prompt 오류로 끝났으며
기존 run을 덮어쓰지 않았다. r03의 어댑터 코드는 새 profile의 argv에 포함돼 semantic
profile hash로 고정된다. shell 없이 원문 UTF-8을 읽어 명시적인 `--print=VALUE` 한
인자로 전달하고 child stdin은 DEVNULL로 닫는다. 실제 subprocess를 이용한 오프라인
fake CLI 시험에서 9,775-byte 공통 프롬프트의 Unicode·개행·인용부호 보존, 중복 stdin 없음,
종료 코드 전파를 확인했다. prompt 내용과 baseline·fixture·평가 기준은 변경하지 않았다.

권한 모드는 실제 init의 `request-review`에 맞춰 descriptive 문자열을 정정했다.
scoped allow 정책은 변경하지 않았다. 새로운 profile/receipt/bundle hash를 검사하고
각 run의 R10 기록을 checkout 밖에 남긴 뒤 동결 baseline의 wrapper/runner로 실행했다.

사전 진단 중 literal `--print=-`와 1ms timeout은 본 실험 밖에서 새 conversation을
열고 zero-turn/zero-usage partial result를 반환했다. 제품 prompt를 사용하지 않았고
그 세션을 재개하지 않았다. provider activity가 전혀 없었다고 단정하지 않으며 캐시 격리는
주장하지 않는다. [진단 기록](agy-argv-review-20260926.md)과
[전달 어댑터 검토](agy-argv-adapter-review-20260926.md)를 보존한다.

## r03 실측 및 사후 판정

- 시작/종료 UTC: `2026-09-25T18:18:20.081Z` / `2026-09-25T18:18:31.218Z`.
- init model: `gemini-3.8-flash-medium`; permission mode: `request-review`.
- terminal usage: input 21,400 / output 792 / total 22,192 / thinking 702 / cache read 0.
  thinking을 total에 추가 합산하지 않는다.
- 도구 시도 1건: `run_command`, `CommandLine: dir`. step state `ERROR`,
  terminal `denied_actions`와 stderr의 headless auto-denial을 교차 확인했다.
- CLI의 `SUCCESS`와 exit 0은 제품 또는 pilot 합격이 아니다.
- 현재 runner는 `DONE` tool만 집계하고 `ERROR` step 및 `denied_actions`를 놓쳐
  tool_calls/failed_commands를 0으로 기록했다. 이 계측값은 정량 비교에 사용할 수 없다.
  원본 manifest는 유지하고 `operator-review.json`에 관측 1건과 실패 판정을 기록했다.
- 실제 운영자의 구현 피드백 0회. 모델의 도구 승인 요청은 headless 정책에 의해
  거부됐으며 사용자가 대화 중 직접 거부했다는 뜻이 아니다.

## 검증·보존

검토자: Codex maintainer, 2026-09-26 KST.

두 run의 schema/operator/evidence hash, clean checkout 및 초기 HEAD 일치를 확인했다.
제품 result가 없으므로 제품 validator나 flash를 실행하지 않았다. 전역 settings,
instructions, hooks의 원래 hash 3개가 복원됐고 각 wrapper active lock도 해제됐다.

원본 위치는 `C:\Espressif\benchmark-runs\<run-id>`다. 원본 logs, 준비 profile,
prompt, launch authorization, `run-manifest.before-review.json`, operator review,
implementation bundle을 유지한다. 초기 snapshot을 archive한 것이며 새로운 제품 코드가 아니다.

- r02 archive commit: `5af8de0fd34a0f04e525fe81dde3b4ffc9835760`.
- r03 archive commit: `4909283465e19942de9815dd1c8489c24f1968c9`.
- [최종 hash·검증 기록](agy-pilot-retry-result-20260926.json).

receipt의 `pilot_pass=false`를 유지한다. 다음 pilot에 앞서 허용할 기본 작업 범위를
검토해 scoped 정책과 증거를 갱신하고, ERROR/denied_actions를 감지하는 runner 회귀 시험을
추가해야 한다. 권한 확대나 자동 재실행으로 이번 결과를 덮어쓰지 않는다. 모든 pilot은
순위 통계에서 제외하며 정식 반복 benchmark는 보류한다.
