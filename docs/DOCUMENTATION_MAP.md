# 문서 지도

| 용도 | 원본 |
|---|---|
| 새 협업 범위·역할·기존 과제와 다른 조건 | [협업 설계](design/2026-10-08-orca-harness.md) |
| 목표·작업 상태·완료 조건 | [계획](plans/2026-10-08-orca-harness.md) |
| 현재 실행·미해결 조건 | [준비 상태](experiments/next-comparison-readiness.md) |
| 토큰 세션 만료·초기화 후 재개 | [재개 절차](experiments/orca-harness-resume.md) 및 계획의 체크리스트 |
| 기존 제품 동작 C/I/F·wire·stale·화면·시험 | [동결 제품 계약](PRODUCT_CONTRACT.md) 및 연결 schema |
| 보드 핀·극성·SDK·허용 제조사 source | [동결 보드 자료](hardware/version-2-capabilities.md) |
| 보존 입력·SHA-256 | [입력 목록](../experiments/orca-harness-20261008/frozen-inputs.json) |
| Orca Run·worktree·사용자 확정 사항 | [실험 식별자](../experiments/orca-harness-20261008/context.json) |
| Gemini GUI 후보 A/B/C·LCD 구현 인계 | [Gemini handoff](design/lcd/gemini/handoff.md) |
| Codex Sol 6.1 GUI 후보 D/E/F·LCD 구현 인계 | [Sol 6.1 handoff](design/lcd/sol61/handoff.md) |
| 독립 요구·인터페이스 검토와 합격 기준 | [Luna 검토](agent-runs/orca-luna/requirements-review.md) |
| GUI 6개 최초 브라우저 검증·보완 결함 | [GUI 검토](agent-runs/orca-luna/gui-review.md) |
| 선택 B 독립 검증·첫 FAIL 및 날짜별 수정 후 PASS | [B 재검토](agent-runs/orca-luna/gui-b-review.md) |
| 실제 시안 A–F·정상 화면 증거·공통 데이터 | [비교 화면](../opendesign/comparison.html) |
| PC 최초 구현 제출 (제품 합격과 구분) | [AGY 보고](agent-runs/orca-flash/report.md) |
| PC 최초 구현 검토·재현 결함·보완 연결 | [PC 보완 검토](design/2026-10-08-pc-review-findings.md) |
| ESP32 firmware 구현·실제 build·hash·물리 시험 절차 | [Sol 보고](agent-runs/orca-sol/report.md) |
| 현재 PC→실제 C 통합·독립 검증·미측정 범위 | [Luna 제품 검토](agent-runs/orca-luna/product-review.md) |
| 검증 이후 PC 실행·업로드·실물 관측 순서 | [운영 절차](experiments/orca-harness-operator.md) |
| 협업 결과·역할별 근거·실제 수집/업로드·미측정 범위 | [협업 결과](experiments/orca-harness-results.md) |
| 실물 반복 점멸의 원인 재현·firmware 보완·재검증 | [점멸 보완 계획](plans/2026-10-10-lcd-flicker.md) |
| 점멸 수정의 독립 host 판정·SDK 경계·실물 한계 | [독립 표시 검증](agent-runs/orca-luna/lcd-flicker-review.md) |
| 현재 점멸 수정 binary/hash·업로드 gate | [수정 후보](../experiments/orca-harness-20261008/operator/firmware-flicker-candidate.json) |
| 점멸 수정본 실물 영상·BOOT/수동 RESET·숫자 잘림 | [후속 관측](../experiments/orca-harness-20261008/operator/post-flicker-observation-20261010.json) |
| 토큰·사용한도 숫자 잘림 보완과 후속 검증 | [숫자 표시 계획](plans/2026-10-10-lcd-numeric-readability.md) |

`docs/PRODUCT_CONTRACT.md`와 57개 원본 입력은 수정하지 않는다. 이번 실험의 live 수집과
협업 실행 변경은 협업 설계가 소유한다. 구현 보고서와 검증 보고서는 각각 실제 역할 작업에
연결하며, 브라우저 시안·host 시험·실물 동작을 별도 근거로 남긴다.
