# 다음 비교 모델 프로필 — 2026-10-03

사용자 결정: 기존 6개 비교 구성을 유지하되 Codex의 GPT-5.6 Sol/Luna를 GPT-6로 변경한다.
2026-10-04 갱신: **Claude 제외, 활성 5개 모델의 실제 infrastructure capability 검증 완료.**
원래 6개 선택은 아래에 보존한다. 현재 실행 대상은 [기계 목록](comparison-targets.json)의 `active_profiles`만 따른다.
GPT-6의 사용자 스킬 비활성·내장 스킬 유지와 hook 비활성, OpenCode 수정 권한, AGY scope를 재검증했다.
Opus 4.6은 실제 호출에서 지원 모델로 인식되지 않았으며 사용자가 Claude 제외를 선택했다.
`agy-opus.json`은 excluded/pending 기록이며 활성 profile 목록에서 제외한다.
실행 여부의 원본은 [준비 상태](../../../docs/experiments/next-comparison-readiness.md)다.

| 대상 | 모델 | effort | 설정 파일 |
|---|---|---|---|
| Codex Sol | `gpt-6-sol` | medium | [프로필](codex-sol.json) |
| Codex Luna | `gpt-6-luna` | max | [프로필](codex-luna.json) |
| OpenCode Muse | `opencode/muse-spark-1.3-contributor-free` | 기존 값 유지 | [프로필](opencode-muse.json) |
| AGY Flash | `gemini-3.8-flash-medium` | medium | [프로필](agy-flash.json) |
| AGY Pro | `gemini-3.1-pro-high` | high | [프로필](agy-pro.json) |
| AGY Opus (이번 비교 제외) | `claude-opus-4-6-thinking` | 기존 값 유지 | [제외 기록](agy-opus.json) |

Codex CLI 버전은 로컬 `--version`에서 0.159.2를 확인했다. 로컬 native cache에는 요청한 두 ID와
effort가 있으며 [선별 목록](../../../results/gpt6-profile-update-20261003/model-catalog.json)에 보존했다.
이는 모델 목록 확인이며 실제 계정 호출 성공·quota·120분 실행 가능성을 보장하지 않는다.
2026-10-04 Codex profile의 settings_inventory는 새 native inventory와 실제 GPT-6 세션을 근거로 갱신했다.

나머지 profile도 현재 검증·제외 상태를 기록하므로 10월 2일 JSON과 byte 단위로 같다고 주장하지 않는다.
실행 조건의 argv와 모델은 실제 probe와 대조하며 상태 설명 변경은 별도로 기록한다.
AGY는 root lock이 추가된 scoped wrapper에서 실행한다. 당일 ID/ledger/receipt는 현재 준비 상태를 따른다.
GPT-6 profile의 model_slug는 `gpt-6-sol`/`gpt-6-luna`로 구분하여 이전 모델 기록과 혼동을 줄였다.

제품 입력 57개 중 56개의 archive bytes는 이전 `85ba1089226a2e3198983a42eea375a3fd7e6ed0`과 동일하며,
AGY 권한 정책 1개에서 금지된 Git 이력 조회 허용을 제거했다. 모든 활성 후보에 같은 새 입력을 제공하고,
보완된 운영 기준·도구를 포함한 새 baseline commit에서 다음 실행을 준비한다. fixture 범위,
최초 120분·후속 최대 3회/누적 120분, 단일 보드 관측 조건은 유지한다.
새 baseline ZIP과 profile의 보존·평가 hash 검증 절차는 준비 상태를 따른다. 별도 평가 overlay는 사용하지 않는다.
이 폴더는 기존 [검증 기록](../verified-profiles-20261002/README.md)을 대체하거나 수정하지 않는다.

10월 3일 원본 검토는 [설정 갱신 보고서](../../../results/gpt6-profile-update-20261003/report.md)에 보존한다.
현재 실제 검증 결과는 [실행 준비 보완 보고서](../../../results/experiment-launch-preparation-20261004/report.md)를 따른다.
