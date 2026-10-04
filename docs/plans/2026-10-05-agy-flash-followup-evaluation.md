# AGY Flash 후속 1회차 종료 후 평가

목표: `20261005-antigravity-cli-agy-flash-r02`의 종료 결과와 비용을 보존하고, 같은 공통 입력으로 독립 검증·업로드·실물/RM 평가를 수행한다.
상태: 2026-10-05 동결·정책·독립 host 검증·05:38:52 KST 원본 업로드와 공통 전송 기록 완료. 사용자 LCD/BOOT 영상 대기. 정책은 invalid_for_comparison이며 PC 쓰기 2건 완료 뒤 장치 수락 로그 0건·LoadProhibited panic/재부팅 2회다. 최종 RM·독립 복원은 미완료다.

원본 규칙은 [운영 계약](../experiments/comparison-operating-contract.md), [RM 목록](../experiments/reference-match-matrix.md), [접근 정책](../experiments/isolation-policy.md)을 따른다.
현재 상태는 [준비 상태](../experiments/next-comparison-readiness.md)와 [진행 기록](../../results/formal-comparison-20261004/report.md)에서 관리한다.

- [x] 기존 raw 사본과 현재 bytes를 대조하고 source를 Git 동결·bundle로 보존한다. terminal manifest/ledger 원본은 유지한다.
- [x] native 도구·명령·외부 경로·거부 이후 행동을 검토하고 정책 sidecar를 기록한다. 이전 회차 실행 파일 참조를 적격 검토에 반영한다.
- [x] 동결 validator로 제출물·입력을 검증하고 Python 시험·공통 collector/encoder를 독립 실행한다.
- [x] 후보의 CTest 통과 기록과 이번 source의 별도 host 검증을 구분한다. 동일 compiler로 checkout 밖에서 host만 빌드했다. firmware를 운영자가 재빌드하거나 후보 source를 고치지 않았다.
- [x] 동결 firmware의 source/build/artifact 연결과 COM3 보드 식별을 확인한 뒤 업로드하고 원본 공통 seq 0·1을 전송·기록한다. 실패도 보존한다.
- [ ] 사용자 영상/관측을 run·artifact·업로드 슬롯에 연결하고 RM review를 한 번 적용한다. 미관측을 pass로 바꾸지 않는다.
- [ ] 최종 package를 독립 복원하고 비용·정책·RM·후속 잔여 예산을 기록한다.

완료 조건: 원본 비용·첫 결과·baseline/tag를 보존하고, 이번 회차의 source 동결·정책·독립 host 검증·실물/RM 판정·독립 복원을 근거/hash로 연결한다. 영상이 아직 없으면 평가 완료로 보고하지 않고 관측 대기 단계와 촬영 대상을 명시한다. 현재 회차를 재실행하거나 다른 모델을 먼저 시작하지 않는다.
