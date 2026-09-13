# 검증 결과 인덱스

현재 게시된 본 실험 결과는 없다. 실험 원본은 agent/model 보관 브랜치에서 관리한다.
main에는 운영자가 확인한 요약과 고정 commit 링크만 추가한다.

`python scripts/summarize-benchmark.py <manifest> ... --output <new-summary.md>`로
초안을 만든 뒤 C1~C8, F1~F9 기능 상태, G1~G6 LCD GUI rubric, 자율 기능 점수,
판정자, 평가 버전, 증거 링크, 토큰 정의와 측정 한계를 검토해서 추가한다. 이
명령은 자동 commit/push/merge하지 않는다.
완료 run의 중앙값·범위와 성공/전체 시도 수를 함께 집계하고 pilot은 제외한다.

historical firmware-only cohort는 fixture 기반 firmware·LCD·입력·자율 기능만
다룬다. 정식 end-to-end 결과는 PC agent/provider collector와 PC→ESP32
transport/receiver를 포함해야 한다. 전자가 구현·검증되지 않은 결과는 F1/F3을
`not_run; out of cohort`로 기록하며, 이를 “실시간 개인 사용량 표시 완료”로
요약하지 않는다. agent 자체 시험, 공통 evaluator, 운영자 COM3 시험은 각각
분리된 상태·증거로 보존한다.

수동으로 prompt를 붙여넣었거나 실행 중 외부 피드백·코드 수정이 있었거나
manifest/receipt/raw log/token telemetry가 빠진 결과는
`manual pilot; invalid for cross-agent quantitative comparison`으로 보존하고
정식 중앙값·순위 집계에서 제외한다.
