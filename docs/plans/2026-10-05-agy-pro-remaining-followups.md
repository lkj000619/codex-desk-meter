# AGY Pro 남은 후속 회차

목표: 정식 비교의 같은 profile·권한·공통 과제에서 Pro 후속 최대 3회 AND 누적 7,200초를 적용하고 모든 실패·비용·자기 직전 source를 보존한다.
상태: 2026-10-05 r02·r03·r04의 최종 평가·독립 복원을 완료했다. 마지막 r04는 22:58:07.087 KST에 Get-FileHash 거부로 종료했다. 모두 정책 eligible·RM1 fail/RM2~RM5 not_run이며 firmware·최종 제출물이 없다. Pro 최초+후속 3회 누적 677.5초·정규화 660,989 token이다. 잔여 회차 0으로 종료하며 시간 6,590.703초는 원본 ledger에 남겨 예산을 초기화하지 않는다.
원본: [운영 계약](../experiments/comparison-operating-contract.md), [현재 상태](../experiments/next-comparison-readiness.md), [Pro 첫 후속](2026-10-05-agy-pro-followup-execution.md).

- [x] r02의 원본 terminal/비용·446-byte CMakeLists 사본·동결 source·정책/RM·독립 복원을 보존한다. LF raw와 CRLF Git 복원 차이는 내용·Git blob 동일성으로 검증하고 최초 audit 오류도 보존한다.
- [x] 자기 직전 결과만 전달한 r03을 별도 checkout·새 receipt로 한 번 실행하고 원본·정책/RM·독립 복원을 보존한다. SDK manufacturer read와 own writes, 권한 거부 후 중단을 로그로 확인한다.
- [x] 남은 7,066.5초·1회에서 최대 7,066초로 r04를 한 번 시작하고 actual native model/cwd/request-review를 확인한다.
- [x] 종료 후 실제 시간·token·source·제출·정책·RM를 보존하고 package를 독립 복원한다. 최대 회차에 도달하면 추가 Pro 회차를 생성하지 않는다.

완료 조건: 모든 Pro 최초/후속 비용과 원본 판정·실행 hash를 보존하며 각 종료에 RM review를 한 번만 적용한다. Native 거부 후 중단과 일반 인자 오류를 구분하고, 권한 완화나 운영자 구현 수정을 하지 않는다. 펌웨어가 없으면 Pro 업로드/광학 관측은 not_run으로 기록하며 기존 Flash 화면을 Pro 근거로 쓰지 않는다. Flash 잔여 예산과 동결 baseline은 유지한다. 다음 Codex 모델은 이번 사용자 지시에서 함께 시작하지 않는다.

완료 근거: [마지막 독립 복원](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-pro-r04/evaluation-final-20261005/restore-audit.json)·[보완 host 검증](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-pro-r04/evaluation-final-20261005/post-package-host-runtime-check.json)·[series 종료](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-pro-r04/evaluation-final-20261005/operator-series-completion.json). 마지막 package는 361개 파일을 검사했다. 초기 host DLL loader 오류는 보존하고 독립 복원본에 기록된 compiler runtime 경로로 같은 바이너리를 실행해 partial host 12/29 통과를 확인했다. 제품 기준 미도달·원본 비용과 제출 누락은 유지한다.
