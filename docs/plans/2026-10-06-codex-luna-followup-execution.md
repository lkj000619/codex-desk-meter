# Codex Luna 후속 1회차 실행

목표: 사용자 요청에 따라 Luna 자신의 동결 구현을 보완하고, 동일 조건에서 구현·제출·독립 평가·원본 펌웨어 관측을 진행한다.

상태: 2026-10-06 후속 1회차 구현·제출·동결·독립 복원·COM3 업로드·가능한 실물 평가 완료. run `20261006-codex-cli-gpt-6-luna-r02`는 21:52:33.769~22:42:20.773 KST에 2,987초 실행했고 exit0으로 종료했다. 별도 checkout 시작 HEAD `2c5b001777c395f68b879dc7649e208cc4e9f050`, 동결 HEAD `e68356829715793dc31dd188bc2a9f528f6fcbd2`다. PID 14732는 종료된 이력이며 thread `01a11145-ddbb-7760-b6f5-16dab337b8af`와 최초 평가·동결·진단 원본을 보존했다. LCD는 계속 검은 화면으로 기준 미도달이다.

- [x] 직전 commit `c0d5d61160664923e0494302fae180089d02d247`에서 별도 checkout 준비, 고정 입력 57개와 원본 보존 검증. 제품 source 29개 동일, 이전 제출물 제거, 생성 build/sdkconfig 상속 없음.
- [x] 자신의 실제 관측·로그·고정 요구사항만 피드백으로 전달. 운영자 진단의 수정 방법·추가 자료·다른 후보 구현은 제외.
- [x] 기존 runner와 `gpt-6-luna / max`, CLI 0.159.2, ESP-IDF 5.3.2로 후속 1회 호출. 후속 누적 한도 7,200초·최대 3회 중 첫 회.
- [x] 실제 프로세스·thread·argv·시작 시간을 기록하고 시작 증거 43개 파일을 보존. 비용은 종료 후 확정한다.
- [x] source38개·artifact20개와 원시 비용·정책을 동결하고 535개 파일의 최종 package를 독립 복원·검증. Python22개·원본 C 실행 파일3개, common collector/encoder·production host receiver, provider validity17/17 확인.
- [x] 원본 `build/codex_desk_meter.bin`을 22:51 KST COM3에 업로드하고 공통 frame0/1 전송. 22:54 KST 같은 펌웨어 리셋 후 정상 boot/USB ready 확인. 사용자 “검은 화면이 계속됨”을 연결하고 BOOT·30초 미관측은 명시.
- [x] RM과 제품 판정, 실제 소모 후속 예산, 재개 지침을 [현재 상태](../experiments/next-comparison-readiness.md)와 [진행 기록](../../results/formal-comparison-20261004/report.md)에 반영.

완료 조건: 이번 회차의 종료·제출·동결·복원·정책·비용과 가능한 실물 관측을 근거로 평가한다. 미관측 항목은 통과로 간주하지 않는다. 최초 정책 위반과 원본 판정·패키지를 유지하며 후속 결과로 덮어쓰지 않는다. 실물 답변이 필요한 경우 업로드 완료와 관측 대기를 구분해 기록한다.

절차의 원본은 [운영 계약](../experiments/comparison-operating-contract.md), [RM 목록](../experiments/reference-match-matrix.md), [도구 안내](../experiments/comparison-tooling.md)다. 새 독립 실행·모델 교체·운영자 구현 수정은 이번 범위에 포함하지 않는다.

운영자 준비 오류: 최초 launcher 경로가 없어 PowerShell이 모델 호출 전에 종료됐다. 오류·PID·로그를 별도로 보존하고 정상 경로로 다시 시작했다. 후보 호출은 1회이며 이 오류로 후속 회차·모델 예산을 소비하지 않았다.

최종 근거: [RM](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-luna-r02/evaluation-20261006/reference-review.json), [독립 감사](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-luna-r02/evaluation-20261006/restore-audit.json), [사용자 관측](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-luna-r02/evaluation-20261006/operator-observation/user-black-screen-report.json), [비용 checkpoint13](../../results/formal-comparison-20261004/comparison-checkpoint-13.md).

RM1 pass·RM2 partial·RM3 fail·RM4/5 not_run, reference fail·product_pass false다. 실제 파이프2호출로 정책은 invalid_for_comparison이다. Raw 비용 13,414,031 token은 모두 보존하며 cached input을 중복 합산하지 않는다. 잔여 후속은 4,213초(70분13초)·최대2회다. 추가 호출은 준비·시작하지 않았으며 다음 회차는 자신의 관측 피드백·source·새 preflight를 사용하는 정상 gate를 거친다.

2026-10-06 운영 기록 정정: 독립 host 시험은 후보 최종 응답의21개와 달리 실제22개였다. 처음 감사의 개수 guard 오류·통과 원본 로그를 보존하고 시험을 반복하지 않은 다음 감사에서 확인했다. Runtime PSRAM marker의 잘못된 false 값은 원본을 보존한 별도 날짜 있는 정정으로 수정했다. 제품 source·빌드·후보 비용·최초 판정은 변경하지 않았다. 후보 자체29개 wire 시험과 고정 operator29 pipeline 시험은 서로 다르며 후자는 미실행이다.
