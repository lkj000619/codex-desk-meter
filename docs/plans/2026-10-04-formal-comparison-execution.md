# 동결 조건의 정식 비교 실행

목표: ESP32-S3-LCD-3.16 제품 구현에서 에이전트의 첫 결과·자기 후속 수정 비용과 RM 도달·제품 품질을 동일 조건으로 비교한다.
시작 승인: 2026-10-04 사용자 요청 “프로젝트 목적과 목표에 엇나가지않도록 실험 시작”.
상태: 최초 평가·원본 복원 완료. 후속 1회차 timeout으로 수정 예산 소진. 남은 구현 보존·396개 파일 독립 복원·COM3 재업로드 완료. 사용자 영상 검토 후 촬영 대상 확인과 후속 RM review 대기.
원본: [운영 계약](../experiments/comparison-operating-contract.md), [현재 상태](../experiments/next-comparison-readiness.md),
[동결 기록](../../results/experiment-launch-preparation-20261004/freeze.json).

## 고정 조건

- baseline `272875140d1998d458e26fdb2f6deab5e5d8f7b5` / `comparison-baseline-20261004`.
- 활성 5개·독립 3블록, Claude 제외. seed별 순서는 freeze의 block_orders를 따른다.
- 최초 최대 7,200초, 후속 최대 3회 AND 후속 누적 최대 7,200초. 임의 재시도·추가 prompt·실행 중 구현 피드백 금지.
- 후보 입력 57개·필수 MD 3개를 수정하지 않는다. 동결된 runner/profile과 run-bound receipt를 사용한다.
- 후보는 serial/flash에 접근하지 않는다. 운영자는 결과를 동결한 뒤 COM3에서 직렬 실물 평가한다.
- 정책 적격성·RM 도달·전체 제품 합격을 구분한다. 불완전한 관측은 not_run/blocked로 남기며 비용은 모두 기록한다.
- 실제 계정 수집·credential·다른 후보 구현을 제공하지 않는다. prompt-and-log와 OS 격리 미적용이라는 한계를 유지한다.

## 실행과 완료 조건

1. 최초 호출: OpenCode Muse `20261004-opencode-cli-opencode-muse-r01`을 독립 process로 실행한다.
   작업 상태: 완료. 22:47:50~23:04:54 KST, 1,024.64초, 원본 계측·terminal ledger 보존.
   완료 조건: 실제 시작 시각·상태·원본 stdout/stderr·실제 경과 시간·provider usage가 manifest와 ledger에 연결됨.
2. 운영자 검토: 제출물·고정 입력·자체 시험·빌드 artifact를 확인하고 원본 구현을 동결한다.
   작업 상태: 완료. 고정 입력/clean 동결, 독립 Python 25개·host 6개 통과. 정책 위반은 별도 부적격 판정.
   후보의 source를 수정하거나 대신 구현하지 않는다. 정책 검토와 실제 제품 동작 관측을 각각 기록한다.
3. 관측·RM·후속: 동결된 제출물로 실물 평가하고 RM review·policy review를 연결한다.
   작업 상태: 진행 중. 최초 COM3 수락·사용자 사진·RM 판정 완료. 후속 round 1 timeout·최종 제출 누락·정책 부적격 보존. 후속 남은 코드 동결·Python 28개/host 6개 통과·COM3 수락과 관측 전 독립 보존 완료. 사용자 요청으로 같은 artifact를 재업로드하고 66.57초 영상을 검토했다. 영상 촬영 대상 확인 후 RM review를 적용한다. 누적 수정 예산을 소진해 추가 회차는 없다.
   미도달이면 자신의 직전 결과와 허용된 관측 근거만 전달하며 잔여 회차/예산 안에서 후속을 시작한다.
4. 다음 대상: 해당 series 처리 후 다음 대상을 진행한다. 날짜가 바뀐 미시작 예약은 새 ID·ledger·receipt로 준비한다.
   작업 상태: 대기. 첫 series의 허용된 후속 처리 뒤 다음 대상에 진행한다. 2026-10-05 일반 포장 도구의 `firmware/build/` 경로 지원을 [별도 운영 계획](2026-10-04-evidence-artifact-layout-remediation.md)에 따라 보완하고 첫 실제 package의 독립 복원을 확인했다. 원본 거부 기록은 유지한다.
   미시작 나머지 4개는 2026-10-05 새 ID·개별 ledger·receipt와 현재 환경 재확인까지 완료했다. 준비 중 모델 호출은 0회이며 실제 시작은 현재 series 평가 뒤다.
   원래 예약·중단·실패 비용은 보존한다. 전체 비교 완료는 15개 독립 series와 필요한 후속/관측/적격성 집계가 끝난 시점이다.

## 중단과 재개

실행 process는 대화의 토큰 한도와 분리해 최대 실행 시간을 자체 적용한다. launcher PID·명령·console 경로를 남긴다.
재개 시 manifest·ledger·process부터 확인하고 running 후보를 다시 실행하지 않는다.
강제 종료 후 running 기록이 남으면 자식 종료·원본 로그·실제 경과 시간을 확인하고 기존 reconcile 절차를 따른다.
모델/도구 오류와 관측 불가능 사유를 감추거나 자동으로 완료·적격 처리하지 않는다.
