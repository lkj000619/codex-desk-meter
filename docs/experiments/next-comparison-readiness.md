# 다음 동일 조건 비교 준비 상태

확인일: 2026-10-04. 상태: **실행 경계 보완과 활성 5개 모델의 실제 준비 검증 완료. 새 baseline 동결·당일 예약·독립 복원 연결 중. 제품 실험 0회.**

이 문서는 다음 비교의 현재 상태를 관리한다. 과거 판정·evidence·동결 commit/tag는 보존한다.
2026-10-02의 6개 모델 준비 완료 판정은 [당시 보고서](../../results/experiment-preparation-20261002/report.md)의 조건에만 적용된다.
2026-10-03의 보류 권고와 E1~E5 원본은 [실행 경계 검토](../../results/experiment-execution-review-20261003/report.md)에 남긴다.
이번 보완의 실제 근거는 [선행 작업 결과](../../results/experiment-launch-preparation-20261004/report.md)와
[작업 계획](../plans/2026-10-03-formal-comparison-launch-prerequisites.md)을 따른다.

## 현재 비교 대상과 공통 조건

사용자 결정에 따라 Claude는 이번 비교에서 제외한다. Claude Code 구독이 없고 AGY의 기존
Opus 4.6 호출도 거부됐다. 실패 원본과 비용은 보존하며 Opus 5.5로 대체하지 않는다.
활성 목록의 원본은 [comparison-targets.json](../../experiments/config/next-profiles-20261003/comparison-targets.json)이다.

| 표면 | 모델·effort | 실제 준비 검증 |
|---|---|---|
| Codex | `gpt-6-sol` medium | 9개 capability 통과 |
| Codex | `gpt-6-luna` max | 9개 capability 통과 |
| OpenCode | `opencode/muse-spark-1.3-contributor-free` | 9개 capability 통과, 최종 권한 수정 후 재확인 |
| AGY | `gemini-3.8-flash-medium` | 9개 capability 통과 |
| AGY | `gemini-3.1-pro-high` | 9개 capability 통과 |

- 목표: synthetic fixture 기반 Version 2 E2E. 실제 계정 수집은 별도 owner-only 통합이다.
- 기준 도달: [reference-match RM1~RM5](reference-match-matrix.md). 전체 `product_pass`는 별도다.
- 예산: 최초 7,200초, 후속 최대 3회 AND 후속 누적 7,200초. 자기 직전 결과에서만 이어간다.
- 독립 반복: 5개 조합×3개 블록=15개 최초 series. 후속 최대 45회, 후보 시간 상한 60시간.
- 접근: `prompt-and-log`, `read_isolation: not_enforced`, `builtin-only-v1`. 후보에게 serial/flash와 다른 후보 구현 접근을 허용하지 않는다.
- 보드 사실·고정 제조사 source를 동일 제공한다. BSP 작성도 후보 비용에 포함한다.

[운영 계약](comparison-operating-contract.md), [격리 정책](isolation-policy.md),
[프로필 목록](../../experiments/config/next-profiles-20261003/README.md)이 상세 조건의 원본이다.
전체 제품 합격을 후보 시작의 전제조건으로 삼지 않는다.

## 보류 사유의 보완 상태

| 항목 | 반영한 동작 | 검증 |
|---|---|---|
| E1 정책 준수와 비교 적격성 | 신규 benchmark의 필수 `policy-review.json`; eligible만 품질·순위·RM 도달에 인정 | run/profile/input/raw 로그·검토 근거 결합, 변조·누락 제외, 전체 실패 비용 보존 |
| E2 fresh 후속 과제 연결 | 최초 공통 task 전문·새 ID·잔여 예산 재전달, 자기 증거 상대 경로·hash 고정 | task·증거 변조 차단, 독립 복원, Windows 줄바꿈 변환 시 원본 bytes 보존 |
| E3 native 권한 | 정상 상대 py_compile 허용, 탭 명령 차단, ref 이력 조회 제거, SDK/vendor edit 거부 | 선언 회귀·native 실효 config·실제 정상 도구 실행 |
| E4 실행 문법 | `benchmark.py run <directory> --receipt ...`; AGY 옵션을 action 앞에 배치 | 실제 parser와 대조 |
| E5 AGY 전역 설정 | root 단위 OS lock·owner journal, child 종료 확인 후 원본 복원 | 경합·중단·실패 복구 회귀, 실제 probe 전후 bytes 동일 |
| 평가 baseline 보존 | operator ZIP/profile을 후보 checkout 밖에 보존, 복원 시 입력·평가 hash 재계산 | package 독립 복원 시험 |
| Codex hook | 전역 hook inventory 확인 후 비교 profile에서 `--disable hooks` | native `hooks=false`, 최종 조건의 모델 재검증 |

정책 검토는 운영자의 판단 기록이며 로그가 자동으로 준수를 입증하지 않는다. review digest는 변조 검사다.
기록 부족은 `unverified`, 위반은 `invalid_for_comparison`으로 품질 비교에서 제외하고 비용·사유를 남긴다.
과거 flag 없는 실행에는 새 gate를 소급 적용하지 않는다.
native command map과 지침도 OS 격리를 보장하지 않는다. AGY 공개 SDK view가 요청한 줄 범위보다
넓었던 사실과 native 비동기 도구 사용은 실제 로그에 남겼으며, 본 비교에서 별도 정책 검토한다.

## 동결과 후보 입력

새 baseline tag는 `comparison-baseline-20261004`로 정했다. 실제 commit과 준비 기록은 동결 완료 후
선행 작업 보고서에 연결한다. 이전 `85ba108`과 tag·receipt·package는 변경하지 않는다.

후보 allowlist는 57개/필수 MD 3개다. E3 변경으로 이번 비교의
`experiments/config/agy-pilot-permissions.json` 1개에서 git log 허용 규칙을 제거했다.
나머지 56개 archive bytes는 이전 baseline과 동일해야 하며 활성 5개 모두 같은 새 입력을 받는다.
이 정정은 2026-10-03 계획의 “57개 모두 동일” 조건에만 적용한다. 제품 계약·fixture·공통 과제는 유지한다.

runner는 allowlist만 후보에 복사하고 운영·평가·과거 구현·결과를 제외한다.
`candidate-inputs.json`과 `.benchmark-inputs/` 사본을 실행 전후 검사한다.
후속 clone과 package 복원에서는 Git 줄바꿈 변환과 별개로 고정 입력의 원본 bytes를 보존한다.
새 제품 파일의 작성은 허용한다.

## 실제 시작과 평가 순서

첫 블록은 seed 1로 순서를 고정하고 5개의 개별 ID·ledger·새 receipt를 준비한다.
블록 2·3은 seed 2·3을 사용하며 실제 시작일에 새 ID를 생성한다. 각 모델/독립 반복의 ledger를 분리한다.
기본 순서는 series 실행→결과 동결→운영자 실물 관측→RM·정책 review→필요한 후속→다음 대상이다.
한 보드의 flash·serial·광학 관측은 하나씩 수행한다. provider 사용량과 보드 시간은 시작 직전에 확인한다.

현재 포트 열거에는 COM1만 있고 ESP32의 기존 COM3/VID_303A는 확인되지 않았다.
후보 구현 세션은 보드 없이 시작할 수 있다. 실물 평가 전에 보드를 연결하고 포트·VID/PID를 확인해야 한다.
연결·수신·화면·BOOT·단절 복구를 실제 확인하기 전에는 `not_run`을 유지한다.
후보가 기능을 구현하지 못한 결과는 실패·미도달로 보존한다.

실행과 평가 명령은 [도구 안내](comparison-tooling.md)를 따른다. prepared 상태의 예약은 모델 실행이 아니다.
예약 ID는 해당 KST 날짜에만 유효하다. 다음 날에는 같은 동결 baseline에서 새 ID·ledger를 만들고
CLI/model/settings/environment를 재확인해 새 run-bound receipt를 연결한다.
2026-10-02 ID와 GPT-5.6 receipt는 이번 비교에 재사용하지 않는다.

```powershell
python -X utf8 -m unittest discover -s scripts/tests -v
python -X utf8 scripts/validate-end-to-end-result.py --matrix experiments/fixtures/provider-fixture-matrix.json
python -X utf8 scripts/benchmark.py check --baseline comparison-baseline-20261004 --profile experiments/config/next-profiles-20261003/codex-sol.json
```

`check`는 동결 입력을 검사하며 모델 호출이나 ID 예약을 수행하지 않는다.
실제 제품 terminal artifact와 정책·RM 관측 package는 후보 제출 이후 별도로 생성한다.
