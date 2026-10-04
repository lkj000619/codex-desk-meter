# GPT-6 비교 모델 설정 갱신

목표: 사용자가 확인한 6개 비교 대상 중 Codex Sol/Luna만 GPT-6로 변경하고 문서상 실행 조건을 재검토한다.
상태: 설정·문서 갱신 완료. [검증 보고서](../../results/gpt6-profile-update-20261003/report.md).
본 실험 실행과 실제 GPT-6 capability 검증은 이 작업에 포함하지 않는다.

## 작업·완료 조건

- [x] 로컬 native 모델 목록에서 `gpt-6-sol` medium / `gpt-6-luna` max 지원 표기를 확인한다.
- [x] 2026-10-02 검증 profile·receipt·freeze·원본 보고서를 보존하고 새 비교용 profile을 별도 작성한다.
- [x] 현재 6개 대상과 기존 effort·예산·fixture 범위를 준비 상태에 연결한다.
- [x] 새 profile의 schema/입력 검사를 수행하고 실제 모델 capability·새 실행 ID/ledger·receipt 검증과 구분한다.
- [x] 문서상 진행 가능 여부, 남은 시작 전 조건, 검증 한계를 기록한다.

완료 조건: Sol/Luna만 GPT-6로 변경, 나머지 4개 동일, 기존 기록 불변,
새 profile의 schema 검사 통과 및 GPT-6 check 차단·실제 실행 준비 미확인 상태의 명시.
현재 문서·계약 보완 사항은 유지하며 제품 합격을 실험 시작의 전제조건으로 추가하지 않는다.
