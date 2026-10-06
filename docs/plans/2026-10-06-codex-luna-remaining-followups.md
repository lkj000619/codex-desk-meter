# Codex Luna 남은 후속 실행

목표: 사용자의 추가 실행 요청에 따라 LCD의 실제 가시 출력을 확인할 때까지, 남은 후보 실행4,213초·최대2회 안에서 자기 구현을 이어서 시험한다.

상태: 2026-10-06 23:50:45.750 KST 후속2회차 `20261006-codex-cli-gpt-6-luna-r03` 실행 중. Native PID34648·thread `01a111b2-14c5-7ab3-97a7-54b3b4de34ff`, timeout4,213초다. 직전 run `20261006-codex-cli-gpt-6-luna-r02`·commit `e68356829715793dc31dd188bc2a9f528f6fcbd2`, 후속1회2,987초 사용, 현재 보드에는22:51 KST 업로드한 같은 원본 펌웨어가 있다.

사용자 지시: “추가 실험 진행 요청. lcd 화면이 나올 때까지. 하지만 남은 후속 70분13초·최대2회 안에서”. 이번 지시는 남은 두 회차의 순차 실행·원본 업로드·평가를 허용한다. 기준 도달·LCD 가시 출력·제품 합격은 각각 구분한다. LCD 출력만 확인되어 사용자의 중지 조건을 만족해도 미측정 RM을 pass로 만들지 않는다.

원본 규칙은 [운영 계약](../experiments/comparison-operating-contract.md), [고정 RM](../experiments/reference-match-matrix.md), [직전 평가](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-luna-r02/evaluation-20261006/reference-review.json)를 따른다. `gpt-6-luna/max`·CLI0.159.2·ESP-IDF5.3.2·고정 입력57개·원본 runner/profile/권한을 유지한다. 후보에게는 자기 source와 자기 관측·고정 기대만 제공하며 운영자 진단의 수정 방법·다른 후보 구현을 전달하지 않는다.

- [x] 후속2회차: 직전 reviewed source bundle에서 별도 checkout 준비. 원본 제품 source33개 Git blob과 고정 입력57개·생성 build/sdkconfig 미상속 확인, 자신의 검은 화면·정상 boot·수락 미확인·host 통과·정책 위반 관측 피드백 동결.
- [x] 현재 CLI/SDK/native 설정을 확인하고 새 run-bound receipt로 한 번 시작. 현재 누적 잔여4,213초를 이번 timeout 상한으로 사용하며 시작 시각·thread·실제 argv·원시 로그36개 파일을 보존.
- [ ] 종료 뒤 후보 source/artifact·원시 비용·정책을 동결하고 별도 복원에서 제출·빌드 결합·생산 collector/receiver와 필요한 host 시험 확인. 운영자 제품 수정·재빌드는 하지 않음.
- [ ] 같은 COM3·MAC과 원본 artifact hash를 확인해 업로드, 동일 공통 frame0/1·5초 간격 전송. 사용자 LCD/BOOT/30초 관측을 이번 run에 연결하고 가능한 RM만 평가.
- [ ] LCD 출력이 미도달이고 예산이 남으면 같은 절차로 후속3회차를 자동 진행. 새 timeout은 `floor(7,200 - 종료한 후속 실제 경과 시간 합)`이며 마지막 한 회를 넘기지 않음. 광학 관측이 없으면 다음 회차의 실패를 추정하지 않고 관측 대기로 기록.
- [ ] 가시 출력·reference 도달·시간/회차 소진·사용자 중지 중 실제 종료 사유와 모든 비용/실패를 보존. [현재 상태](../experiments/next-comparison-readiness.md)·[진행 기록](../../results/formal-comparison-20261004/report.md)·문서 지도·계측 갱신.

검증: 기존 동결 comparison manager의 직전 review·bundle·evidence guard와 예산 계산을 재사용한다. Package 원본 bytes/hash·동결 validator·source/artifact·비용/정책/RM 결합을 독립 복원에서 검증하고 문서 링크·staged evidence bytes를 확인한다. 과거 첫 판정·동결 commit/tag·package와 Sol/Pro 종료·Flash 보류는 유지한다.

완료 조건: 시작한 회차는 종료·동결·평가·예산 차감까지 기록하고, LCD가 실제로 보였는지와 관측 한계를 분명히 남긴다. 한도를 넘는 추가 실행·새 최초·모델 변경은 하지 않는다. 환경 준비·독립 평가·업로드·관측 시간은 후보 실행 예산과 구분하며 실제 소비를 별도 기록한다.

운영 기록: 시작 snapshot 생성기의 문자열 guard가 원본 보존 비교식 `==`을 대입 `=`로 잘못 판별해 생성만 중단됐다. AST 검사와 실제 최초 결과 보존 assertion을 유지하고 불필요한 문자열 guard를 제거했다. 이 동안 후보는 계속 실행됐으며 재호출·source 수정·실행 중 피드백은 없다. 오류 정정 기록을 시작 snapshot에 보존했다.
