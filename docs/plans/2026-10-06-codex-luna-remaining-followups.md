# Codex Luna 남은 후속 실행

목표: 사용자의 추가 실행 요청에 따라 LCD의 실제 가시 출력을 확인할 때까지, 남은 후보 실행4,213초·최대2회 안에서 자기 구현을 이어서 시험한다.

상태: 2026-10-07 마지막 후속3 종료·동결·독립 검증·COM3 원본 업로드 완료, 사용자 실물 관측/RM 대기. 실제1,192.593초·정규화4,090,978 token, 잔여1,773.142초이나 남은 회차0으로 추가 실행 불가.

사용자 지시: “추가 실험 진행 요청. lcd 화면이 나올 때까지. 하지만 남은 후속 70분13초·최대2회 안에서”. 이번 지시는 남은 두 회차의 순차 실행·원본 업로드·평가를 허용한다. 기준 도달·LCD 가시 출력·제품 합격은 각각 구분한다. LCD 출력만 확인되어 사용자의 중지 조건을 만족해도 미측정 RM을 pass로 만들지 않는다.

원본 규칙은 [운영 계약](../experiments/comparison-operating-contract.md), [고정 RM](../experiments/reference-match-matrix.md), [직전 평가](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-luna-r02/evaluation-20261006/reference-review.json)를 따른다. `gpt-6-luna/max`·CLI0.159.2·ESP-IDF5.3.2·고정 입력57개·원본 runner/profile/권한을 유지한다. 후보에게는 자기 source와 자기 관측·고정 기대만 제공하며 운영자 진단의 수정 방법·다른 후보 구현을 전달하지 않는다.

- [x] 후속2회차: 직전 reviewed source bundle에서 별도 checkout 준비. 원본 제품 source33개 Git blob과 고정 입력57개·생성 build/sdkconfig 미상속 확인, 자신의 검은 화면·정상 boot·수락 미확인·host 통과·정책 위반 관측 피드백 동결.
- [x] 현재 CLI/SDK/native 설정을 확인하고 새 run-bound receipt로 한 번 시작. 현재 누적 잔여4,213초를 이번 timeout 상한으로 사용하며 시작 시각·thread·실제 argv·원시 로그36개 파일을 보존.
- [x] 종료 뒤 후보 source/artifact·원시 비용·정책을 동결하고 별도 복원에서 제출·빌드 결합·생산 collector/receiver와 필요한 host 시험 확인. 운영자 제품 수정·재빌드는 하지 않음.
- [x] 같은 COM3·MAC과 원본 artifact hash를 확인해 업로드, 동일 공통 frame0/1·5초 간격 전송. 사용자 LCD/BOOT/30초 관측을 이번 run에 연결하고 가능한 RM만 평가.
- [ ] LCD 출력이 미도달이고 예산이 남으면 같은 절차로 후속3회차를 자동 진행. 새 timeout은 `floor(7,200 - 종료한 후속 실제 경과 시간 합)`이며 마지막 한 회를 넘기지 않음. 광학 관측이 없으면 다음 회차의 실패를 추정하지 않고 관측 대기로 기록.
- [ ] 가시 출력·reference 도달·시간/회차 소진·사용자 중지 중 실제 종료 사유와 모든 비용/실패를 보존. [현재 상태](../experiments/next-comparison-readiness.md)·[진행 기록](../../results/formal-comparison-20261004/report.md)·문서 지도·계측 갱신.

검증: 기존 동결 comparison manager의 직전 review·bundle·evidence guard와 예산 계산을 재사용한다. Package 원본 bytes/hash·동결 validator·source/artifact·비용/정책/RM 결합을 독립 복원에서 검증하고 문서 링크·staged evidence bytes를 확인한다. 과거 첫 판정·동결 commit/tag·package와 Sol/Pro 종료·Flash 보류는 유지한다.

완료 조건: 시작한 회차는 종료·동결·평가·예산 차감까지 기록하고, LCD가 실제로 보였는지와 관측 한계를 분명히 남긴다. 한도를 넘는 추가 실행·새 최초·모델 변경은 하지 않는다. 환경 준비·독립 평가·업로드·관측 시간은 후보 실행 예산과 구분하며 실제 소비를 별도 기록한다.

운영 기록: 시작 snapshot 생성기의 문자열 guard가 원본 보존 비교식 `==`을 대입 `=`로 잘못 판별해 생성만 중단됐다. AST 검사와 실제 최초 결과 보존 assertion을 유지하고 불필요한 문자열 guard를 제거했다. 이 동안 후보는 계속 실행됐으며 재호출·source 수정·실행 중 피드백은 없다. 오류 정정 기록을 시작 snapshot에 보존했다.

## 2026-10-07 후속2 검증·관측 대기

- [x] 원본 source38/artifact20·비용 null·native usage-limit 실패 동결,455파일 독립 복원. CLI 배치 정정 뒤 Python22 skip0, 기존 통과 C3 재사용, 공통 collector/encoder/receiver와 provider17 확인. 원본 skip32·실패 guard 로그 보존.
- [x] 같은 COM3/MAC·원본 artifact 확인 후02:19 KST 업로드;02:20 KST 같은 app 단일 리셋·고정 frame0/1 재전송. ELF/PSRAM/USB 첫64byte 수신 확인, 완전한 수락은 미확인.
- [x] 종료14회 비용 집계: token coverage13/14·전체 합계 미상, 알려진57,517,475 token. 이번 실제 시간 차감·정책 eligible과 과거 series invalid 분리.
- [x] 현재 LCD/BOOT/30초 사용자 관측을 원본에 연결하고 한번만 RM review·최종 독립 package 확정.
- [ ] LCD 출력이 없으면 기존 승인 범위의 마지막 후속3: 현재 잔여floor2,965초·최대1회, 자기 동결 source에서 준비. 출력 관측 없이는 실패를 추정해 새 호출하지 않음.

[현재 원본](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-luna-r03/observation-awaiting-20261007/snapshot-inventory.json) · [비용14](../../results/formal-comparison-20261004/comparison-checkpoint-14.md).

## 2026-10-07 후속2 최종 판정

2026-10-07 Luna 후속2 평가 완료: build·COM3 원본 실행은 RM1 pass, 공통 host 경로·USB 첫 수신과 완전한 수락 미확인을 구분해 RM2 partial이다. 38.55초 영상에서 글자 출력은 생겼지만 회전·중복·잘림으로58%/82%와 세 정보 화면을 읽을 수 없어 RM3/RM4 fail이다. 사용자는 BOOT와 RESET 모두 눌렀다고 확인했으며 정확한 조작 시점/횟수가 없어 분리된 BOOT 순환은 RM5 not_run이다. 화면 변화가 자동 재부팅이라는 추정은 하지 않는다. Reference fail·product_pass false, 이번 정책 eligible·과거 series invalid를 유지한다. 최종575파일 package 독립 검증 완료; native 사용량 한도 종료·token null·전체 coverage13/14·알려진57,517,475 token을 보존한다. 정상 가독 화면 미도달이므로 기존 승인 범위의 마지막 후속3을 준비할 수 있다. 잔여2,965.735초·최대1회이며 timeout 상한floor2,965초다. 아직 마지막 후보 호출은 없다.

[후속2 최종 RM](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-luna-r03/evaluation-20261007/reference-review.json) · [독립 복원](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-luna-r03/evaluation-20261007/restore-audit.json)

## 2026-10-07 마지막 후속3회차 진행

- [x] 후속2 동결·독립 검증·영상/RM 완료 뒤 자기 source33개·입력57개 확인, 새 날짜 run/receipt로 마지막 회차 한 번 시작.
- [x] 마지막 후보 종료·실제 시간/원시 비용·정책·source/artifact 동결.
- [ ] 유효 build가 있으면 같은 원본 artifact 업로드·사용자 관측·RM·독립 package 검증. 없으면 원본 실패와 미실행 범위 보존.
- [ ] 정상 가독 화면 도달 여부·남은 시간과 무관한 회차 한도 종료를 기록하고 후속을 닫음.

2026-10-07 02:33:32.910 KST 마지막 Luna 후속3회차 `20261007-codex-cli-gpt-6-luna-r01` 실행 중. 날짜가 바뀌어 run suffix가r01이지만 ledger round3이며 새 최초 실행이 아니다. 자기 직전 동결 commit `91f7de60328b7db9a9d04acef60ac45eafb3685a`에서 별도 checkout을 준비하고 제품 source33개·고정 입력57개·build/sdkconfig 미상속을 확인했다. Native PID30400·thread `01a11247-1dc1-74f2-aab0-c60b8252cb72`, gpt-6-luna/max·CLI0.159.2·ESP-IDF5.3.2·원본 설정과 새 receipt를 유지하며 timeout2,965초다. 자신의 회전/중복/잘림 영상·부분 수신·host 검증과 고정 기대만 전달했다. 후보 시작15회·종료14회, 현재 비용/정책/제출/제품/RM은 미확정이다. 종료 뒤 동결·독립 검증·원본 업로드·평가하며 일찍 종료해도 추가 회차는 없다. 보드는02:19 KST 업로드한 후속2 원본이다. 과거 source/evidence/실패 비용·token null·후속2 최종575파일 package·Sol/Pro 종료·Flash 보류를 보존한다. 독립 series 종료3/15로 전체 비교는 미완료다.

## 2026-10-07 마지막 후속3 검증·관측 대기

- [x] 정상 종료·원시 비용·source37/artifact20 동결,462파일 독립 복원·Python22 skip0/C3/provider17·공통 host 경로 확인.
- [x] 같은 COM3/MAC·원본 artifact 확인 후02:57 KST 업로드,02:58 KST 같은 app 리셋·고정 frame0/1 재전송. Matching ELF boot·PSRAM·USB 첫64byte 확인, 완전한 수락 미확인.
- [x] 종료15회 비용 집계: token coverage14/15·알려진61,608,453 token, 후속2 null과 원본 판정 보존.
- [ ] 현재 사용자 LCD/BOOT/30초 관측을 연결하고 마지막 RM review·최종 독립 package 확정·series 종료.

남은 시간1,773.142초와 관계없이 후속 회차는0으로 추가 호출하지 않는다.
