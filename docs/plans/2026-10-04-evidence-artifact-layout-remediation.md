# 제출 artifact 경로의 증거 보존 보완

목표: 최초 OpenCode 결과의 실제 `firmware/build/` artifact를 보존하고 원본 후보 경로 없이 복원한다.
상태: 완료(2026-10-05). 관련 회귀 21개 통과, 최초 실제 package 348개 파일의 독립 복원과 동결 validator 재검증 완료.

근거: 동결 `package-evidence.py`의 실제 거부와 별도 원본 보존 복원은
[정식 실행 기록](../../results/formal-comparison-20261004/report.md)에 보존했다.
원인은 `scripts/evidence_package.py`가 checkout의 `build/`만 검색하는 데 있다.

적용 범위는 종료한 후보의 운영자 보관 도구다. 동결 tag·runner·profile·57개 입력·제품/RM 기준·
실행 중 후보를 변경하지 않는다. 후속 모델에게 이 운영자 수정이나 다른 구현을 제공하지 않는다.
현재 비교의 모든 후보에 같은 artifact 수집 규칙을 사용하며 과거 거부·원본 archive는 유지한다.

1. 재현 시험: 실제 pass result가 참조하는 별도 빌드 폴더의 ignored app/ELF/map/bootloader/partition을
   보관·복원하고, 원래 checkout 없이 결과/hash가 검증되는지 시험한다.
2. 수집 보완: build evidence의 artifact 경로에서 빌드 폴더를 찾는다. artifact 경로가 없으면
   기존 `build/` 경로를 사용한다. 서로 다른 빌드 폴더의 파일을 합쳐 필수 다섯 종류를 충족시키지 않는다.
3. 검증: 누락 artifact·변조·경로 탈출·기존 정책/입력 복원 회귀를 실행하고 첫 실제 결과도 새 경로에서 복원한다.
4. 기록: 도구 commit/hash·적용 날짜·원본 거부·추가 검증 결과를 연결한다. 후보의 화면 실패나 정책 부적격 판정은 바꾸지 않는다.

완료 조건: 재현 실패를 확인한 뒤 관련 회귀가 통과하고, 첫 실제 결과의 정식 package를 독립 복원하며,
후보 코드/실행 조건/평가 기준을 변경하지 않았다는 근거가 남는다. Git 줄바꿈과 원본 bytes 보존도 기존 절차대로 검증한다.

## 완료 근거와 적용 범위

- 기존 도구에서 별도 build 경로의 정상 복원 거부와 무관한 root build를 대신 인정하는 시험 실패를 확인했다.
- 수정 후 package 회귀 7개, 정책 포함 package 회귀 5개, 정책 gate 회귀 9개가 통과했다.
- 새 package manifest SHA-256은 `c4f845c4a887a91379e293810824f16dda3e8f590d27b45048baa87ad4a854f0`이다.
  원본 package 거부 경로·원본 보존 archive는 그대로 보존하고 새 보관 경로를 사용했다.
- 새 복원 경로에서 348개 inventory 파일의 원본 bytes, 57개 입력, source commit, artifact 7개와
  `firmware/sdkconfig` bytes를 확인했다. package의 operator ZIP에서 추출한 동결 validator로 재검증했다.
- 후보 source·평가 계약·실행 profile·동결 operator checkout은 변경하지 않았다.
  `scripts/evidence_package.py`의 종료 후 수집 단계만 변경했고 이후 모든 후보에 같은 수집 규칙을 적용한다.
- 최초 정책 부적격·화면 실패·RM 미도달·원본 계측을 바꾸지 않는다.
  [복원 검증 원본](../../results/formal-comparison-20261004/operator-remediation-20261005/restore-audit.json)을 따른다.
