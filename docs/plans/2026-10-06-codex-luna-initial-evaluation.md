# Codex Luna 최초 평가·업로드

목표: 사용자 지시 “업로드 진행할 수 있도록 진행”에 따라 종료한 Luna 원본 결과를 보존·검증하고 COM3 실물 평가로 연결한다. 후보 코드를 대신 수정하거나 재빌드하지 않는다.
상태: 2026-10-06 완료. 원본 동결·독립 검증·COM3 업로드와 사용자 요청 재업로드를 마쳤다. 사용자의 검은 화면 보고를 현재21:03 KST artifact에 연결해 제한된 최초 RM review를 적용했다. Application 실행·실제 수신·BOOT·30초 유지·원인은 미확인으로 남긴다. 후속/다른 모델 호출은 없다.
원본: [운영 계약](../experiments/comparison-operating-contract.md) · [최초 시작](2026-10-06-codex-luna-initial-launch.md) · [현재 상태](../experiments/next-comparison-readiness.md).

- [x] 원본 terminal manifest/ledger·로그·비용을 보존하고 자신의 source·app/ELF/설정·host artifact를 hash와 Git commit/bundle로 동결한다. 마지막 성공 build 뒤 firmware source 변경 여부를 확인한다.
- [x] 전체 native 명령·파일 접근과 공통 실행 제한을 검토해 policy review를 연결한다. 위반도 원본 비용·제품 관측과 함께 남기며 적격성은 별도로 판정한다.
- [x] 동결 source/artifact·입력57개·원본 계측·제출 형식을 새 package에서 독립 복원하고 기록된 실행 파일로 Python/C·공통 frame/collector를 확인한다. 원본 build cache·checkout을 실행 경로로 재사용하지 않는다.
- [x] COM3 VID303A/PID1001·점유 상태를 확인하고 동일 원본 firmware를 업로드한다. NVS만 공통 초기화하며 전체 flash erase·후보 source 수정·rebuild는 없다.
- [x] 같은 공통 frame0/1을 전송해 실제 수락/거부 로그와 source 의미를 연결한다. LCD/BOOT/연속 유지 관측을 요청하고 현재 artifact와 평가 단계·원본 근거를 문서에 기록한다.

완료 조건: 업로드와 실제 수신·사용자 실물 관측 요청을 원본 artifact에 연결하고, 후보 종료·검증·정책 적격성·RM/제품 합격을 구분한다. 광학 관측 전 정식 RM 완료나 제품 합격을 표시하지 않는다. 같은 최초를 재호출하거나 다른 모델로 넘어가지 않는다. 과거 Sol/Pro 종료·Flash 보류·원본 판정과 동결 ref를 보존한다.

완료 근거: [464개 파일 독립 감사](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-luna-r01/evaluation-20261006/restore-audit.json) · [현재 업로드](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-luna-r01/evaluation-20261006/operator-observation/hardware-attempt-02/hardware-slot.json) · [사용자 검은 화면 보고](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-luna-r01/evaluation-20261006/operator-observation/hardware-attempt-02/user-black-screen-report.json) · [제한된 최초 RM](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-luna-r01/evaluation-20261006/reference-review.json).
동결 source33/artifact19, Python11/C3 통과, 공통 wire 일치, collector8개 필드 차이·modern16/17을 보존했다. 정책은파이프8호출/세미콜론1호출로 부적격이다. RM1/2 partial·RM3 fail·RM4/5 not_run, reference fail·product_pass false다.
11:27 업로드 로그는 당시 대상 연결 미확인 사용자 보고와 함께 보존하고21:03 재업로드를 현재 관측에 사용한다. Host write 완료를 실제 수신 성공으로 확대하지 않는다. 최종 package SHA-256은 `57ad97f136d462b95093bd562d8a9af176e91bfee20e6ae826c36d68cebd0764`다.
