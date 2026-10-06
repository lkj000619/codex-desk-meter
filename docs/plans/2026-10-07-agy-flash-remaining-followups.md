# AGY Flash 잔여 후속 실행

목표: 자기 직전 동결 구현에서 공통 데이터 수신·가독 화면·BOOT 탐색을 보완하고 실제 보드로 RM1~RM5를 평가한다.

상태: 후속 2회차 `20261007-antigravity-cli-agy-flash-r01`가03:38:00.978 KST에 native 시작. 준비·현재 환경 검증 완료, 구현 실행 중. 다른 모델과 새 독립 반복은 시작하지 않는다.

- 기존 series: `20261005-antigravity-cli-agy-flash-r01`, 최초 1회·후속 1회 평가 완료.
- 시작 원본: `94018f1785a590e1514ef1b5145c40f0c03ffca3`.
- 잔여: 5,710.780999999959초(95분10.781초), 최대 2회. 실제 후보 경과 시간으로 차감한다.
- 모델·입력·권한: 동결된 `gemini-3.8-flash-medium`, 공통 입력 57개, 기존 profile과 native scoped 설정을 유지한다.
- 기존 후속1의 `invalid_for_comparison` 판정과 비용은 보존한다. 이후 개선으로 과거 series 적격성을 되살리지 않는다.

작업 순서:

1. 직전 독립 복원·평가·ledger와 원본 hash 확인. 자기 관측과 공통 기대만 feedback으로 제공한다.
2. 새 checkout의 상속된 생성 build/cache/sdkconfig만 제거하고 제품 source Git blob 동일성을 검증한다. 이전 원본·package는 보존한다.
3. 현재 CLI/SDK/모델 목록/전역 설정을 확인하고 새 run-bound receipt로 native 후속2를 한 번 실행한다.
4. 종료·비용·정책·제출물·source/artifact를 보존하고 독립 복원 검증 후 같은 artifact를 COM3에 업로드한다.
5. 공통 frame 0·1과 사용자 실물 영상으로 화면·BOOT·30초 유지를 평가한다. 실제 RESET 조작과 자동 재부팅을 구분한다.
6. 미도달이고 잔여 시간·회차가 모두 허용하면 자기 평가에서 마지막 후속3을 진행한다. 도달·시간·회차 한도에서 종료한다.

완료 조건: 허용된 후속 실행의 terminal 원본·전체 비용·정책·RM·보드 관측을 보존하고 독립 복원 검증, 현재 상태 및 series 종료/대기 이유를 연결한다. 미관측은 합격으로 처리하지 않는다.

방법: 기존 frozen benchmark와 scoped AGY launcher/평가 도우미를 재사용한다. 운영자가 제품 구현을 수정하거나 후보 실행 중 실물 피드백을 추가하지 않는다.
