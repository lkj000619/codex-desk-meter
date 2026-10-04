# AGY Flash 최초 실행 종료 후 평가

목표: 종료된 `20261005-antigravity-cli-agy-flash-r01`의 원본 비용·실패·제출 상태를 보존하고, 후보가 남긴 구현을 공통 기준으로 평가한다.
상태: 완료. 종료 보존·동결·정책·호스트·업로드·사용자 영상·최종 RM·430개 파일 package 독립 복원을 마쳤다. environment_failed·제출 누락·Write timeout·기준 미도달을 유지한다. 후속 실행은 정식 실행 계획과 현재 상태를 따른다.
원본 규칙: [정식 실행 계획](2026-10-04-formal-comparison-execution.md), [운영 계약](../experiments/comparison-operating-contract.md), [현재 상태](../experiments/next-comparison-readiness.md).

## 작업과 완료 조건

1. 종료 보존 — 완료. 프로세스 종료·전역 AGY 설정 복원·원본 terminal manifest/ledger hash·57개 입력을 검증했다. 최종 JSON 누락과 762.813초·정규화 토큰 1,352,958을 유지한다.
2. 구현 동결 — 완료. Git 변환 전 source 38개/artifact·설정 10개 원본 bytes를 보존하고 `29e1d7af54a8c9c879e36192ec4ed689e5bbf82d` 및 bundle로 동결했다. 운영자 제품 source 수정·firmware 재빌드는 없다.
3. 정책 검토 — 완료. native 383개 이벤트·123개 도구·접근 범위·마지막 거부·이후 도구 0개를 검토했다. eligible이며 environment_failed와 구분한다. 원본 unknown/null은 유지하고 감사한 개입 0회를 sidecar에만 기록했다.
4. 호스트 검증 — 완료. Python 5개·C 실행 파일 4개가 통과했다. 마지막 성공 build 뒤 firmware 수정이 없다. 공통 frame encoder는 일치하지만 실제 collector는 usage 5개/reset 2개를 모아 공통 payload와 다르다. 제출 누락은 유지한다.
5. 실물 관측 — 완료. COM3 업로드 hash 검증은 성공했고, 공통 seq 0 전송은 Write timeout·bytes_written unknown·수신 로그 0 bytes다. seq 1은 시도하지 않았다. 사용자가 해당 펌웨어의 48.12초 영상을 제공했다. 데이터 대기·reset 기록 부재·Sequence NONE/cache 0·화면 순환을 확인했다. BOOT/IMU별 trigger·연속 30초·정밀 지연은 미측정이다. 전송 시도 파일을 장치 전달 성공으로 해석하지 않는다.
6. 최종 기록 — 완료. 시작 snapshot과 원본 terminal/ledger를 유지한 별도 terminal snapshot 102개 파일과 최종 평가 snapshot 35개 파일을 기록했다. 한 번만 가능한 RM review를 적용해 RM1 pass/RM2 partial/RM3 fail/RM4 partial/RM5 partial로 판정했다. package 430개 파일을 독립 경로에서 동결 validator로 검증했고 result_valid는 false다.

완료 조건: 원본 비용과 실패 상태가 보존되고 동결 source/artifact·정책·호스트·실물 증거가 연결되며, RM 판정과 독립 복원이 완료된다. 이후 필요한 후속은 같은 profile에서 자기 직전 결과만 사용해 최대 3회 AND 누적 7,200초 제한을 따른다. 평가 대기는 후보 실행 시간에 합산하지 않는다.

완료 근거: [최종 RM](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-flash-r01/evaluation-final-20261005/reference-review.json) · [독립 복원](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-flash-r01/evaluation-final-20261005/restore-audit.json).
package manifest SHA-256: `c800ac8aabdebc10961d7ae7ac9dd4a5fceb47f13fba984afc45552054b1b426`.
