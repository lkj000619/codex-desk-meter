# AGY 새 pilot의 실행 입력 보완

사용자는 제한 명령 정책과 정량 비교 목적을 유지하면서 AGY 실험 진행을 요청했다.
마지막 실패는 제조사 source 밖의 운영자 build 파일 읽기였으며 원본을 그대로 보존한다.

입력 계약에는 별도의 결함도 있었다. 운영자 manifest 접근은 금지했으나 결과에는
baseline commit/ref와 입력 hash가 필요했다. `prepare`가 모든 candidate에 같은 형식의
`.benchmark-inputs/run-context.json`과 E2E 평가 manifest 사본을 제공하도록 수정했다.
이 입력에는 고정 identity와 hash만 있고 실행 telemetry, credential, 이전 구현은 없다.
외부 원본 hash를 operator evidence로 보존하고 checkout 사본을 실행 전후 비교한다.
사본 변경은 실행 실패로 판정한다. 고정 입력은 초기 snapshot에 포함되므로 실행 전
clean checkout·독립 Git history 조건도 유지된다.

허용된 제조사 source의 파일명·hash 목록 189개를 고정 입력에 추가했다. 목록은 제품
코드나 구현 안내를 포함하지 않는다. 해당 실제 source 파일을 hash로 검증했다.
과거 bring-up 문서의 build/backup 경로가 현재 읽기 권한을 뜻하지 않음을 명시했다.
SDK·제조사 source 읽기 범위, 제한 command 목록, 모델·timeout·제품 합격 기준은 유지한다.

이 변경은 새 입력 조건이다. 과거 pilot과 동일 입력의 반복으로 합산하지 않는다.
새 baseline/profile/receipt의 pilot 하나를 실행하고 원본과 결과를 검증한다.
단일 prompt, 후속 지시 0, 실행 중 코드 수정 0 조건을 유지한다.
실행 완료·구조화 결과 검증·제품 전체 합격은 각기 별도로 판정한다.

검증: 새 identity/tamper 시험 4개와 기존 회귀 시험을 포함해 전체 111개 통과.
이 사전 결과는 제품 펌웨어·실물 합격을 뜻하지 않는다. 최신 preflight와 실행 결과는
별도 파일에 기록하며 과거 receipt를 덮어쓰지 않는다.
