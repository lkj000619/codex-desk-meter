# 2026-10-02 검증한 CLI 프로필

이 6개 프로필은 별도 빈 앱 fixture에서 실제 CLI capability를 확인한 실행 설정이다.
프로필 자체는 본 실험 실행 승인이 아니다. 당시 모델 ID와 effort를 유지했다.

[준비 보고서](../../../results/experiment-preparation-20261002/report.md)의 설정·실패·한계와
[동결 목록](../../../results/experiment-preparation-20261002/freeze.json)의 profile-bound receipt를
함께 확인한다. 제품 입력 baseline은 `85ba1089226a2e3198983a42eea375a3fd7e6ed0`이다.
기존 [미확정 예제](../runner-profiles/README.md)와 과거 후보 프로필은 보존한다.

실행 직전 버전·실행본 hash와 native 설정 inventory를 다시 확인한다. AGY 프로필은
고정 1.2.14 실행본을 참조하며 기존 `agy_pilot_environment.py` scoped wrapper 안에서만
사용한다. 다른 날짜의 run ID는 새로 준비하고 receipt를 다시 연결해야 한다.
