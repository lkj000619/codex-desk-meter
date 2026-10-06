# Codex Luna 후속 1회차 실행

목표: 사용자 요청에 따라 Luna 자신의 동결 구현을 보완하고, 동일 조건에서 구현·제출·독립 평가·원본 펌웨어 관측을 진행한다.

상태: 2026-10-06 21:52:33.768 KST 후속 1회차 실행 중. run `20261006-codex-cli-gpt-6-luna-r02`, 별도 checkout HEAD `2c5b001777c395f68b879dc7649e208cc4e9f050`, native PID 14732, thread `01a11145-ddbb-7760-b6f5-16dab337b8af`. 최초 평가·동결과 별도 진단 원본은 보존했다.

- [x] 직전 commit `c0d5d61160664923e0494302fae180089d02d247`에서 별도 checkout 준비, 고정 입력 57개와 원본 보존 검증. 제품 source 29개 동일, 이전 제출물 제거, 생성 build/sdkconfig 상속 없음.
- [x] 자신의 실제 관측·로그·고정 요구사항만 피드백으로 전달. 운영자 진단의 수정 방법·추가 자료·다른 후보 구현은 제외.
- [x] 기존 runner와 `gpt-6-luna / max`, CLI 0.159.2, ESP-IDF 5.3.2로 후속 1회 호출. 후속 누적 한도 7,200초·최대 3회 중 첫 회.
- [x] 실제 프로세스·thread·argv·시작 시간을 기록하고 시작 증거 43개 파일을 보존. 비용은 종료 후 확정한다.
- [ ] 종료 후 source·artifact·원시 비용·정책을 동결하고 독립 복원·host 검증.
- [ ] 후보가 만든 동결 펌웨어를 COM3에 업로드해 공통 데이터를 전송하고 사용자 LCD·BOOT·30초 관측과 연결.
- [ ] RM과 제품 판정, 실제 소모 후속 예산, 재개 지침을 [현재 상태](../experiments/next-comparison-readiness.md)와 [진행 기록](../../results/formal-comparison-20261004/report.md)에 반영.

완료 조건: 이번 회차의 종료·제출·동결·복원·정책·비용과 가능한 실물 관측을 근거로 평가한다. 미관측 항목은 통과로 간주하지 않는다. 최초 정책 위반과 원본 판정·패키지를 유지하며 후속 결과로 덮어쓰지 않는다. 실물 답변이 필요한 경우 업로드 완료와 관측 대기를 구분해 기록한다.

절차의 원본은 [운영 계약](../experiments/comparison-operating-contract.md), [RM 목록](../experiments/reference-match-matrix.md), [도구 안내](../experiments/comparison-tooling.md)다. 새 독립 실행·모델 교체·운영자 구현 수정은 이번 범위에 포함하지 않는다.

운영자 준비 오류: 최초 launcher 경로가 없어 PowerShell이 모델 호출 전에 종료됐다. 오류·PID·로그를 별도로 보존하고 정상 경로로 다시 시작했다. 후보 호출은 1회이며 이 오류로 후속 회차·모델 예산을 소비하지 않았다.
