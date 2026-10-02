# 남은 실험 도구 구현 설계

목표: 채택된 첫 결과·후속 수정 비교를 실제 실행 도구와 비용·관측·복원 기록에 연결한다.
근거는 [운영 계약](../experiments/comparison-operating-contract.md)과
[main 검토](../../results/main-purpose-review-20261002/review.md)다.

## 실행과 예산

운영자 전용 comparison ledger가 최초 run과 후속 run을 연결한다. 최초 7,200초,
후속 최대 3회·합계 7,200초다. 실패·timeout·abort도 실행 시간과 회차에 포함한다.
후속은 직전 frozen 구현 commit에서 시작하며 같은 profile·기준 입력을 유지한다.
feedback에는 관측·기대·근거·목표 ID·직전 run/commit·남은 예산을 고정한다.
동일 ledger의 동시 실행을 차단하고, 실행 중 중단된 ledger는 자동 성공/예산 회복으로 처리하지 않는다.

기존 단회 runner와 frozen baseline은 유지한다. comparison 연결 run만 인프라 준비 receipt를
사용하며 제품 pilot_pass를 요구하지 않는다. reference 판정은 운영자 evidence로 따로 기록하고
전체 product_pass와 합치지 않는다. 미평가 결과에서 다음 수정으로 자동 진행하지 않는다.

## 집계

기존 유효 completed 결과 표를 유지한다. 별도 전체 시도 표는 비교군별 terminal 상태,
제품 성공/전체 시도, 측정 비용·미측정 건수를 표시한다. prepared는 시도로 세지 않는다.
잘못된 제품 result가 있어도 유효한 실행 manifest의 소비 비용은 보존한다.
comparison 연결의 최초/후속 비용과 reference 도달 비용은 ledger 식별자별로 집계한다.

## 관측과 의미 검사

기존 frame 모델의 역사적 동작은 유지하고 별도 production 평가 oracle을 추가한다.
source timestamp 의미와 수신 monotonic age를 분리하고 fixture UTC anchor·재부팅을 기록한다.
운영자 관측 도구는 한 serial 소유 경로의 write/read 이벤트·sequence·hash·시각을 기록한다.
수락 로그와 광학 증거를 각각 검증하고 write나 host oracle만으로 실제 제품 pass를 만들지 않는다.
오프라인 replay와 주입 backend로 경계·손상·값 변화·실패를 검증한다.

## 복원과 reference

package는 source bundle·manifest·result가 참조하는 evidence·실행 로그를 상대 경로/hash로 연결한다.
새 root 복원은 경로 이탈·symlink·변조를 거부하고 기존 checkout 없이 validator를 수행한다.
reference stimulus는 원본 commit/collector/evidence에서 복구하며 58/82 숫자만으로 추정하지 않는다.
표면별 capability 증거는 receipt에 연결하고 입력 check와 실효 권한 검증을 구분한다.

범위: 도구 구현·오프라인 검증과 기존 원본의 복구. 후보 모델 실행·보드 flash·실 계정 수집은
이 구현의 검증 명령에 포함하지 않는다. 실제 화면·권한 관측이 없는 항목은 미확인으로 남긴다.
