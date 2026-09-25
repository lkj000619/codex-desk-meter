# AGY 권한·계측 보완 — 2026-09-26

## 변경과 검증

사용자의 보완 요청에 따라 현재 개발 checkout의 runner와 정책을 수정했다.
과거 r01/r02/r03의 profile, receipt, manifest와 원본 로그는 변경하지 않았다.

- scoped allow에 인자 없는 `dir`, `pwd`, `Get-ChildItem`, `Get-Location`을 추가했다.
  현재 작업 폴더의 목록·위치를 확인하는 목적이다. 포괄적인 shell/Python 권한이나
  flash/erase 권한을 추가하지 않았다. 실제 CLI의 규칙 매칭은 다음 pilot에서 확인한다.
- terminal `denied_actions`, tool `ERROR`의 일반 `TOOL_ERROR` 안에 들어 있는
  권한 거부 메시지, stderr에만 기록된 headless auto-denial을 실행 실패로 판정한다.
- 완료된 tool의 `DONE`과 `ERROR`를 step index별로 집계한다. 실패한 command도
  실패 횟수에 포함하며 원본 terminal usage는 그대로 보존한다.
- 새 회귀 시험 2개가 기존 구현에서 실패하는 것을 확인한 뒤 수정했다.
  전체 94개 시험 통과. 실제 r03 로그 재검사도 권한 실패 판정,
  `tool_calls=1`, `failed_commands=1`, `total=22192`를 확인했다.
- `git diff --check` 통과.

수정 policy SHA-256:
`f68a674753ef7f393bdb724317e653184e3190821eedf205f5ce10db812825fc`.

새 candidate는
`experiments/config/verified-profiles-candidate/agy-gemini-3.8-flash-remediation.candidate.json`이다.
명시적 prompt 인자 어댑터와 `request-review`를 유지하고 policy hash를 갱신했다.
schema와 resolved-profile 검증을 통과했다.

## 다음 실행 적용 조건

이 보완은 아직 동결된 `benchmark-v2-baseline-20260925`에 포함되지 않는다.
새 candidate를 과거 baseline/receipt와 섞어 실행하면 안 된다. 수정 runner와 정책을
새 baseline으로 동결하고 host preflight·policy 검토 후 새 profile-bound receipt를
발행해야 한다. 기존 receipt의 pass를 복사해 새 정책이 검증됐다고 주장하지 않는다.
이번 작업에서는 모델을 재실행하거나 전역 AGY 설정을 변경하지 않았다.
