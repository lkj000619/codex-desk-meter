# timeout 결과의 관측 전 증거 보존과 재개

목표: OpenCode 후속 1회차의 최종 제출 누락 상태와 원본 비용을 유지하고, 실물 관측 답변을 기다리는 동안 남은 구현과 운영자 증거를 원본 경로 없이 검증할 수 있게 보존한다.
상태: 완료. 관측 전 보존·재업로드·영상 대상 확인·최종 RM review·최종 package 독립 복원·예산 소진 종료 기록을 마쳤다. 다음 AGY Flash 최초 실험이 03:09:41 KST 시작됐다.
원본 규칙: [정식 실행 계획](2026-10-04-formal-comparison-execution.md), [운영 계약](../experiments/comparison-operating-contract.md), [현재 상태](../experiments/next-comparison-readiness.md).

## 작업과 완료 조건

1. 재개 확인 — 완료. `r02`는 timeout이며 프로세스가 없고 후속 예산은 0초다. 원본 terminal manifest와 ledger hash, 동결 source·artifact, 정책 review를 다시 검증한다.
2. 관측 전 보존본 — 완료. 별도 staging에 원본 운영자 파일을 복사하고 포장용 파생 manifest를 만들었다.
   파생 manifest에는 검증한 동결 implementation commit과 보존할 운영자 증거 hash만 연결한다.
   원본 manifest/ledger/정책/후보 checkout은 변경하지 않는다. 원본과 파생본의 변경 필드·hash를 기록한다.
   raw product source와 artifact 사본도 보관해 Git 줄바꿈 변환과 별도로 원본 bytes를 확인한다.
3. 독립 복원 — 완료. 새 경로에서 396개 inventory 파일·원본 terminal bytes·동결 source commit·57개 입력·정책·9개 artifact 사본·46개 source 사본을 검증했다.
   package의 operator ZIP에 들어 있는 동결 validator로 재검증한다. 후보 result JSON·선택 문서가 없는 상태를 유지하고 `result_valid: false`를 확인한다.
4. 보존 기록 — 완료. package와 복원의 hash·범위·한계를 [실행 기록](../../results/formal-comparison-20261004/report.md)에 연결했다.
   이 보존본은 RM 판정 전 자료이며 최종 관측 완료나 제품 합격을 뜻하지 않는다.
5. 사용자 요청 재업로드 — 완료. 02:50 KST 같은 동결 artifact와 공통 frame을 다시 전송했다. 최초 슬롯은 보존하고 별도 `recapture-r2-20261005/`에 새 로그를 기록했다. 후보 호출·예산 변경·source 수정·재빌드는 없다.
6. 실물 평가 — 완료. 사용자가 최초 후속 업로드 이후 촬영했음을 확인했다. 한 번만 가능한 RM review를 적용해 RM1 pass/RM2 partial/RM3 partial/RM4 partial/RM5 pass, reference fail로 판정했다.
   최종 package 430개 파일을 새 경로에서 동결 validator로 재검증했고 예산 소진 종료 근거를 보존했다. 영상·관측 미측정 한계·정책 부적격·제출 누락·원본 비용은 유지한다.

관측 전 보존의 완료 조건: 원본 terminal/ledger hash가 바뀌지 않고, 원래 후보 경로 없이 새 보존본의 실제 bytes와 동결 validator 검증이 통과하며, 제출 누락·정책 부적격·당시 RM 관측 대기·예산 소진이 그대로 기록된다.
후보 재호출·source 수정·firmware 재빌드·다른 모델로 대체는 이 작업에 포함하지 않는다.

보존 완료 근거: [복원 감사](../../results/formal-comparison-20261004/timeout-preservation-20261005/restore-audit.json),
[원본 대조와 재전송 확인](../../results/formal-comparison-20261004/timeout-preservation-20261005/validation.json).
package manifest SHA-256은 `9a7c506fe8cd3e861184232134dd2127b847d523997b44a51941ad7a9c045fc3`이다.
후속 실물 판정의 완료 조건은 촬영 대상 확인·RM 항목별 실제 증거·최종 package 독립 복원·series 예산 소진 종료 기록이다.
최종 완료 근거는 [RM 판정](../../results/formal-comparison-20261004/review-finalization-20261005/reference-review.json),
[독립 복원](../../results/formal-comparison-20261004/review-finalization-20261005/restore-audit.json),
[series 종료](../../results/formal-comparison-20261004/review-finalization-20261005/series-completion.json)다.
최종 manifest SHA-256은 `948261ab0ea75f3742b11664086976816dd353cf5f6cd39394a7270422117fd4`이다.
최종 RM 연결에 따른 manifest/ledger 변경은 관측 전 원본 사본과 구분해 보존했고 계측·실행 정보·후보 source는 바뀌지 않았다.
